"""Tests for ModelResponse and TokenUsage Contracts."""

import unittest

from platform.core.messages import Message, Role
from platform.core.response import FinishReason, ModelResponse, TokenUsage


class TestResponseContracts(unittest.TestCase):
    """Tests model response and token usage contracts."""

    def test_token_usage_calculation(self) -> None:
        usage = TokenUsage(prompt_tokens=150, completion_tokens=50, cost_usd=0.002)
        self.assertEqual(usage.total_tokens, 200)
        self.assertEqual(usage.cost_usd, 0.002)

        data = usage.to_dict()
        self.assertEqual(data["total_tokens"], 200)

        restored = TokenUsage.from_dict(data)
        self.assertEqual(restored.total_tokens, 200)

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
        self.assertIn("claude-3-5-sonnet", json_str)
        self.assertIn("anthropic", json_str)

        restored = ModelResponse.from_json(json_str)
        self.assertEqual(restored.model_name, "claude-3-5-sonnet")
        self.assertEqual(restored.provider_name, "anthropic")
        self.assertEqual(restored.finish_reason, FinishReason.STOP)
        self.assertEqual(restored.structured_output["status"], "success")


if __name__ == "__main__":
    unittest.main()
