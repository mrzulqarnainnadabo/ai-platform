"""Pure-stdlib OpenAI-compatible chat-completions adapter with native SSE streaming."""
import asyncio
import json
import os
import queue
import threading
import urllib.error
import urllib.request
from typing import AsyncGenerator, List, Optional

from ai_platform.core.capabilities import ModelCapabilities, ProviderCapabilities
from ai_platform.core.config import ModelConfig
from ai_platform.core.context import ExecutionContext
from ai_platform.core.errors import (AuthenticationError, ContextWindowExceededError,
    InvalidRequestError, ProviderError, ProviderQuotaError, ProviderUnavailableError,
    RateLimitError, normalize_provider_error)
from ai_platform.core.messages import ContentPart, Message, Role
from ai_platform.core.provider import IModelProvider
from ai_platform.core.response import FinishReason, ModelResponse, TokenUsage


class OpenAICompatibleProvider(IModelProvider):
    provider_name = "openai-compatible"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout_seconds: float = 60.0) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.timeout_seconds = timeout_seconds
        if not self.base_url.startswith(("https://", "http://localhost", "http://127.0.0.1", "http://[::1]")):
            raise ValueError("base_url must use HTTPS unless targeting localhost")

    async def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(provider_name=self.provider_name, supported_models=[], model_capabilities={})

    def _payload(self, messages: List[Message], config: ModelConfig, stream: bool = False) -> bytes:
        body = {"model": config.model_name, "messages": [self._message(m) for m in messages], "stream": stream}
        if config.temperature is not None: body["temperature"] = config.temperature
        if config.top_p is not None: body["top_p"] = config.top_p
        if config.max_tokens is not None: body["max_tokens"] = config.max_tokens
        if config.stop_sequences: body["stop"] = config.stop_sequences
        if config.response_format: body["response_format"] = config.response_format.to_dict()
        if config.tools: body["tools"] = [t.to_dict() for t in config.tools]
        if config.tool_choice != "auto": body["tool_choice"] = config.tool_choice
        body.update(config.extra_params)
        return json.dumps(body).encode("utf-8")

    @staticmethod
    def _message(message: Message) -> dict:
        content = message.content
        if isinstance(content, list):
            parts = []
            for part in content:
                if part.text is not None: parts.append({"type": "text", "text": part.text})
                elif part.image_url is not None: parts.append({"type": "image_url", "image_url": {"url": part.image_url}})
                elif part.data is not None: parts.append({"type": "text", "text": "[binary content omitted]"})
            content = parts
        out = {"role": message.role.value, "content": content}
        if message.name: out["name"] = message.name
        if message.tool_calls: out["tool_calls"] = [t.to_dict() for t in message.tool_calls]
        if message.tool_call_id: out["tool_call_id"] = message.tool_call_id
        return out

    def _request(self, body: bytes, timeout: float) -> dict:
        req = urllib.request.Request(self.base_url + "/chat/completions", data=body,
            headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise self._http_error(exc.code, raw) from exc
        except urllib.error.URLError as exc:
            raise ProviderUnavailableError("Provider connection failed", provider_name=self.provider_name, raw_error=exc) from exc

    def _http_error(self, code: int, raw: str) -> ProviderError:
        safe = raw[:500]
        if code in (401, 403): return AuthenticationError("Provider authentication failed", provider_name=self.provider_name, status_code=code)
        if code == 429: return RateLimitError("Provider rate limit exceeded", provider_name=self.provider_name, status_code=code)
        if code in (402,): return ProviderQuotaError("Provider quota unavailable", provider_name=self.provider_name, status_code=code)
        if code in (408, 504): return ProviderError("Provider request timed out", provider_name=self.provider_name, status_code=code)
        if code in (500, 502, 503): return ProviderUnavailableError("Provider unavailable", provider_name=self.provider_name, status_code=code)
        if code in (400, 422):
            lowered = safe.lower()
            if "context" in lowered or "token" in lowered and "limit" in lowered:
                return ContextWindowExceededError("Provider context window exceeded", provider_name=self.provider_name, status_code=code)
            return InvalidRequestError("Provider rejected the request", provider_name=self.provider_name, status_code=code)
        return InvalidRequestError("Provider request failed", provider_name=self.provider_name, status_code=code)

    @staticmethod
    def _response(data: dict, provider_name: str) -> ModelResponse:
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        role = msg.get("role", "assistant")
        content = msg.get("content") or ""
        usage = data.get("usage") or {}
        reason = choice.get("finish_reason") or "stop"
        if reason not in {r.value for r in FinishReason}: reason = "stop"
        return ModelResponse(Message(Role(role), content), FinishReason(reason),
            TokenUsage(int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0)), int(usage.get("total_tokens", 0))),
            str(data.get("model") or "unknown"), provider_name, response_id=str(data.get("id") or ""))

    async def generate(self, messages: List[Message], config: ModelConfig, context: Optional[ExecutionContext] = None) -> ModelResponse:
        if context: context.cancellation_token.raise_if_cancelled()
        try:
            data = await asyncio.to_thread(self._request, self._payload(messages, config), min(config.timeout_seconds, self.timeout_seconds))
            if context: context.cancellation_token.raise_if_cancelled()
            return self._response(data, self.provider_name)
        except ProviderError:
            raise
        except Exception as exc:
            raise normalize_provider_error(exc, self.provider_name, config.model_name) from exc

    async def stream(self, messages: List[Message], config: ModelConfig, context: Optional[ExecutionContext] = None) -> AsyncGenerator[ModelResponse, None]:
        """Native SSE chat-completions stream. Runtime owns overall timeout/cancellation."""
        q: "queue.Queue[object]" = queue.Queue()
        stop = threading.Event()
        sentinel = object()
        holder = {}

        def worker() -> None:
            req = urllib.request.Request(self.base_url + "/chat/completions", data=self._payload(messages, config, True),
                headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})}, method="POST")
            try:
                response = urllib.request.urlopen(req, timeout=min(config.timeout_seconds, self.timeout_seconds))
                holder["response"] = response
                with response:
                    for raw in response:
                        if stop.is_set(): break
                        line = raw.decode("utf-8", errors="replace").strip()
                        if not line or not line.startswith("data:"): continue
                        data = line[5:].strip()
                        if data == "[DONE]": break
                        try: q.put(self._response(json.loads(data), self.provider_name))
                        except (ValueError, KeyError, TypeError) as exc: q.put(exc); break
            except urllib.error.HTTPError as exc:
                q.put(self._http_error(exc.code, exc.read().decode("utf-8", errors="replace")[:500]))
            except Exception as exc:
                q.put(normalize_provider_error(exc, self.provider_name, config.model_name))
            finally:
                q.put(sentinel)

        thread = threading.Thread(target=worker, name="ai-platform-provider-stream", daemon=True)
        thread.start()
        try:
            while True:
                if context: context.cancellation_token.raise_if_cancelled()
                item = await asyncio.to_thread(q.get)
                if item is sentinel: break
                if isinstance(item, Exception): raise item
                yield item  # type: ignore[misc]
        finally:
            stop.set()
            response = holder.get("response")
            if response is not None:
                try: response.close()
                except Exception: pass
