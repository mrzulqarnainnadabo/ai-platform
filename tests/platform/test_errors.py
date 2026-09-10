"""Tests for ProviderError Hierarchy and Error Normalization."""

import unittest

from platform.core.errors import (
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
    """Tests standardized provider error creation and normalization."""

    def test_provider_error_attributes(self) -> None:
        err = RateLimitError(
            message="Rate limit exceeded",
            provider_name="openai",
            model_name="gpt-4o",
            status_code=429,
            retry_after_seconds=5.0,
        )
        self.assertIsInstance(err, KernelError)
        self.assertIsInstance(err, ProviderError)
        self.assertEqual(err.provider_name, "openai")
        self.assertEqual(err.model_name, "gpt-4o")
        self.assertEqual(err.status_code, 429)
        self.assertEqual(err.retry_after_seconds, 5.0)

        data = err.to_dict()
        self.assertEqual(data["error_type"], "RateLimitError")
        self.assertEqual(data["details"]["retry_after_seconds"], 5.0)

    def test_context_window_exceeded_error(self) -> None:
        err = ContextWindowExceededError(
            message="Prompt tokens 150000 exceeds max context 128000",
            provider_name="anthropic",
            max_context_tokens=128000,
        )
        self.assertEqual(err.max_context_tokens, 128000)
        self.assertEqual(err.details["max_context_tokens"], 128000)

    def test_normalize_provider_error(self) -> None:
        raw_429 = Exception("Error 429: Too Many Requests from server")
        norm_429 = normalize_provider_error(raw_429, provider_name="openai")
        self.assertIsInstance(norm_429, RateLimitError)

        raw_auth = Exception("401 Unauthorized: Invalid API key provided")
        norm_auth = normalize_provider_error(raw_auth, provider_name="gemini")
        self.assertIsInstance(norm_auth, AuthenticationError)

        raw_timeout = Exception("Connection timed out after 30 seconds")
        norm_timeout = normalize_provider_error(raw_timeout, provider_name="ollama")
        self.assertIsInstance(norm_timeout, ProviderTimeoutError)

        raw_ctx = Exception("Maximum context length exceeded in request")
        norm_ctx = normalize_provider_error(raw_ctx, provider_name="openai")
        self.assertIsInstance(norm_ctx, ContextWindowExceededError)


if __name__ == "__main__":
    unittest.main()
