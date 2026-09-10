"""Tests for ModelResponse and TokenUsage Contracts."""

import unittest

from ai_platform.core.messages import Message, Role
from ai_platform.core.response import FinishReason, ModelResponse, TokenUsage


class TestResponseContracts(unittest.TestCase):
    """Tests model response and token usage contracts and validation."""

    def test_token_usage_valid(self) -> None:
        usage = TokenUsage(prompt_tokens=150, completion_tokens=50, cost_usd=0.002)
        self.assertEqual(usage.total_tokens, 200)

    def test_token_usage_invalid_value_raises(self) -> None:
        with self.assertRaises(ValueError):
            TokenUsage(prompt_tokens=-5)

        with self.assertRaises(ValueError):
            TokenUsage(cost_usd=-0.01)

    def test_model_response_invalid_name_raises(self) -> None:
        msg = Message(role=Role.ASSISTANT, content="Hello")
        usage = TokenUsage()

        with self.assertRaises(ValueError):
            ModelResponse(
                message=msg,
                finish_reason=FinishReason.STOP,
                usage=usage,
                model_name="",
                provider_name="openai",
            )

        with self.assertRaises(ValueError):
            ModelResponse(
                message=msg,
                finish_reason=FinishReason.STOP,
                usage=usage,
                model_name="gpt-4o",
                provider_name="",
            )

    def test_model_response_serialization(self) -> None:
        msg = Message(role=Role.ASSISTANT, content="Execution completed.")
        usage = TokenUsage(prompt_tokens=100, completion_tokens=20)
        resp = ModelResponse(
            message=msg,
            finish_reason=FinishReason.STOP,
            usage=usage,
            model_name="claude-3-5-sonnet",
            provider_name="anthropic",
            structured_output={"status": "success"},
        )

        json_str = resp.to_json()
        restored = ModelResponse.from_json(json_str)
        self.assertEqual(restored.model_name, "claude-3-5-sonnet")
        self.assertEqual(restored.provider_name, "anthropic")


if __name__ == "__main__":
    unittest.main()
