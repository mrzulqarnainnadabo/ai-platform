import asyncio
import json

import pytest

from ai_platform.core import ModelConfig, Message, Role
from ai_platform.core.messages import ProviderOptions
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


def test_provider_options_are_validated_and_serialized():
    provider = FakeProvider(api_key="test")
    config = ModelConfig("test", provider_options=ProviderOptions(reasoning_effort="low", seed=7))
    payload = provider._payload([Message(Role.USER, "hello")], config)
    body = json.loads(payload)
    assert body["model"] == "test"
    assert body["stream"] is False
    assert body["reasoning_effort"] == "low"
    assert body["seed"] == 7


def test_provider_options_reject_unknown_fields():
    with pytest.raises(ValueError):
        ProviderOptions.model_validate({"attacker_selected_model": "evil"})
