"""Tests for ExecutionContext and CancellationToken."""

import unittest

from platform.core.context import CancellationToken, ExecutionContext
from platform.core.errors import ProviderTimeoutError


class TestContextAndCancellation(unittest.TestCase):
    """Tests cancellation tokens and execution context behavior."""

    def test_cancellation_token_initial_state(self) -> None:
        token = CancellationToken()
        self.assertFalse(token.is_cancelled)
        token.raise_if_cancelled()  # Should not raise

    def test_cancellation_token_cancel(self) -> None:
        token = CancellationToken()
        token.cancel(reason="Timeout exceeded")
        self.assertTrue(token.is_cancelled)
        self.assertEqual(token.reason, "Timeout exceeded")

        with self.assertRaises(ProviderTimeoutError) as cm:
            token.raise_if_cancelled()
        self.assertIn("Timeout exceeded", str(cm.exception))

    def test_execution_context_serialization(self) -> None:
        ctx = ExecutionContext(
            tenant_id="tenant-123",
            user_id="user-456",
            agent_id="agent-789",
            timeout_seconds=30.0,
            metadata={"environment": "production"},
        )
        data = ctx.to_dict()
        self.assertEqual(data["tenant_id"], "tenant-123")
        self.assertEqual(data["user_id"], "user-456")
        self.assertEqual(data["agent_id"], "agent-789")
        self.assertEqual(data["timeout_seconds"], 30.0)
        self.assertFalse(data["is_cancelled"])

        restored = ExecutionContext.from_dict(data)
        self.assertEqual(restored.tenant_id, "tenant-123")
        self.assertEqual(restored.user_id, "user-456")
        self.assertEqual(restored.metadata["environment"], "production")


if __name__ == "__main__":
    unittest.main()
