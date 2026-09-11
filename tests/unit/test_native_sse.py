import asyncio
import json
from ai_platform.core import ModelConfig, Message, Role
from ai_platform.providers import openai_compatible


class FakeResponse:
    def __init__(self, lines): self.lines = lines
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def __iter__(self): return iter(self.lines)
    def close(self): pass


def test_native_sse_stream_normalizes_chunks(monkeypatch):
    lines = [
        b'data: ' + json.dumps({"id":"1","model":"m","choices":[{"message":{"role":"assistant","content":"A"},"finish_reason":None}]}).encode() + b'\n',
        b'data: ' + json.dumps({"id":"1","model":"m","choices":[{"message":{"role":"assistant","content":"B"},"finish_reason":"stop"}]}).encode() + b'\n',
        b'data: [DONE]\n',
    ]
    monkeypatch.setattr(openai_compatible.urllib.request, "urlopen", lambda *a, **k: FakeResponse(lines))

    async def run():
        provider = openai_compatible.OpenAICompatibleProvider(api_key="test")
        return [r async for r in provider.stream([Message(Role.USER, "hi")], ModelConfig("m"))]

    chunks = asyncio.run(run())
    assert [c.message.content for c in chunks] == ["A", "B"]
