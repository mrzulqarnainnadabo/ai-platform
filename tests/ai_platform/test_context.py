"""Tests for ExecutionContext and CancellationToken."""
import unittest
from ai_platform.core.context import CancellationToken, ExecutionContext
from ai_platform.core.errors import CancellationError


class TestContextAndCancellation(unittest.TestCase):
    def test_cancellation_token(self) -> None:
        token = CancellationToken()
        self.assertFalse(token.is_cancelled)
        token.cancel(reason="User stopped")
        self.assertTrue(token.is_cancelled)
        with self.assertRaises(CancellationError):
            token.raise_if_cancelled()

    def test_execution_context_validation(self) -> None:
        with self.assertRaises(ValueError): ExecutionContext(timeout_seconds=-1.0)
        with self.assertRaises(ValueError): ExecutionContext(tenant_id="")

    def test_execution_context_serialization(self) -> None:
        ctx = ExecutionContext(tenant_id="tenant-123", user_id="user-456", agent_id="agent-789", timeout_seconds=30.0, metadata={"environment": "production"})
        restored = ExecutionContext.from_dict(ctx.to_dict())
        self.assertEqual(restored.tenant_id, "tenant-123")
        self.assertEqual(restored.metadata["environment"], "production")
