"""Tests for ProviderError Hierarchy and Error Normalization."""

import unittest

from ai_platform.core.errors import (
    AuthenticationError,
    ContextWindowExceededError,
    InvalidRequestError,
    KernelError,
    ProviderError,
    ProviderQuotaError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
    normalize_provider_error,
)


class TestErrorHierarchy(unittest.TestCase):
    """Tests standardized provider error creation, validation, and normalization."""

    def test_provider_error_attributes(self) -> None:
        err = RateLimitError(
            message="Rate limit exceeded",
            provider_name="openai",
            model_name="gpt-4o",
            status_code=429,
            retry_after_seconds=5.0,
        )
        self.assertEqual(err.provider_name, "openai")
        self.assertEqual(err.retry_after_seconds, 5.0)

    def test_invalid_provider_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            ProviderError(message="test", provider_name="")

    def test_invalid_retry_after_raises(self) -> None:
        with self.assertRaises(ValueError):
            RateLimitError(message="test", retry_after_seconds=-1.0)

    def test_normalize_provider_error(self) -> None:
        raw_429 = Exception("Error 429: Too Many Requests from server")
        norm_429 = normalize_provider_error(raw_429, provider_name="openai")
        self.assertIsInstance(norm_429, RateLimitError)


if __name__ == "__main__":
    unittest.main()
