import asyncio
import json

import pytest

from ai_platform.core import ModelConfig, Message, Role
from ai_platform.providers import OpenAICompatibleProvider


class FakeProvider(OpenAICompatibleProvider):
    def _request(self, body, timeout):
        return {"id": "resp-1", "model": "test", "choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}


def test_openai_compatible_generate_is_normalized():
    async def run():
        return await FakeProvider(api_key="test").generate([Message(Role.USER, "hello")], ModelConfig("test"))
    response = asyncio.run(run())
    assert response.message.content == "ok"
    assert response.provider_name == "openai-compatible"
    assert response.usage.total_tokens == 2


def test_provider_default_repr_does_not_expose_api_key():
    p = OpenAICompatibleProvider(api_key="super-secret")
    assert "super-secret" not in repr(p)


def test_native_sse_path_is_not_generate_fallback():
    source = open("ai_platform/providers/openai_compatible.py", encoding="utf-8").read()
    assert '"stream": stream' in source
    assert "for raw in response" in source
    assert "generate_fallback" not in source


def test_extra_params_cannot_override_request_envelope():
    provider = FakeProvider(api_key="test")
    for key, value in {
        "model": "attacker-selected-model",
        "messages": [],
        "stream": True,
        "temperature": 0,
        "top_p": 0,
        "max_tokens": 1,
        "stop": ["stop"],
        "response_format": {"type": "text"},
        "tools": [],
        "tool_choice": "none",
    }.items():
        config = ModelConfig("test", extra_params={key: value})
        with pytest.raises(ValueError, match="extra_params cannot override request fields"):
            provider._payload([Message(Role.USER, "hello")], config)


def test_non_reserved_extra_params_remain_provider_specific():
    provider = FakeProvider(api_key="test")
    payload = provider._payload(
        [Message(Role.USER, "hello")],
        ModelConfig("test", extra_params={"reasoning_effort": "low"}),
    )
    body = json.loads(payload)
    assert body["model"] == "test"
    assert body["stream"] is False
    assert body["reasoning_effort"] == "low"
