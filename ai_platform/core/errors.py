"""Standardized Provider Exception Hierarchy for AI Platform Kernel."""

from typing import Any, Dict, Optional


class KernelError(Exception):
    """Base exception for all AI Platform Kernel errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        if not message or not isinstance(message, str):
            message = "An unclassified kernel error occurred."
        super().__init__(message)
        self.message = message
        self.details = details if isinstance(details, dict) else {}


class ProviderError(KernelError):
    """Base exception for model provider errors."""

    def __init__(
        self,
        message: str,
        provider_name: str = "unknown",
        model_name: Optional[str] = None,
        status_code: Optional[int] = None,
        raw_error: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details=details)
        if not provider_name or not isinstance(provider_name, str):
            raise ValueError("provider_name must be a non-empty string")
        self.provider_name = provider_name
        self.model_name = model_name
        self.status_code = status_code
        self.raw_error = raw_error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "status_code": self.status_code,
            "details": self.details,
        }


class AuthenticationError(ProviderError):
    """Raised when provider API key or authentication fails."""
    pass


class RateLimitError(ProviderError):
    """Raised when provider rate limits or concurrency bounds are exceeded."""

    def __init__(
        self,
        message: str,
        retry_after_seconds: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        if retry_after_seconds is not None and (not isinstance(retry_after_seconds, (int, float)) or retry_after_seconds < 0):
            raise ValueError("retry_after_seconds must be a non-negative number")
        super().__init__(message, **kwargs)
        self.retry_after_seconds = retry_after_seconds
        if retry_after_seconds is not None:
            self.details["retry_after_seconds"] = retry_after_seconds


class InvalidRequestError(ProviderError):
    """Raised when input parameters, messages, or formats are invalid."""
    pass


class ProviderTimeoutError(ProviderError):
    """Raised when a request times out or is cancelled."""
    pass


class ProviderQuotaError(ProviderError):
    """Raised when provider account quota or budget is exhausted."""
    pass


class ProviderUnavailableError(ProviderError):
    """Raised when provider service is down or returning 5xx server errors."""
    pass


class ContextWindowExceededError(ProviderError):
    """Raised when input prompt exceeds model maximum token context window."""

    def __init__(
        self,
        message: str,
        max_context_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        if max_context_tokens is not None and (not isinstance(max_context_tokens, int) or max_context_tokens <= 0):
            raise ValueError("max_context_tokens must be a positive integer")
        super().__init__(message, **kwargs)
        self.max_context_tokens = max_context_tokens
        if max_context_tokens is not None:
            self.details["max_context_tokens"] = max_context_tokens


def normalize_provider_error(
    error: Exception,
    provider_name: str = "unknown",
    model_name: Optional[str] = None,
) -> ProviderError:
    """Normalizes raw Python or SDK exceptions into Kernel ProviderError types."""
    if isinstance(error, ProviderError):
        return error

    err_str = str(error).lower()

    if "rate limit" in err_str or "429" in err_str or "too many requests" in err_str:
        return RateLimitError(str(error), provider_name=provider_name, model_name=model_name, raw_error=error)
    elif "auth" in err_str or "api key" in err_str or "unauthorized" in err_str or "401" in err_str:
        return AuthenticationError(str(error), provider_name=provider_name, model_name=model_name, raw_error=error)
    elif "timeout" in err_str or "timed out" in err_str or "deadline" in err_str:
        return ProviderTimeoutError(str(error), provider_name=provider_name, model_name=model_name, raw_error=error)
    elif "context length" in err_str or "maximum context" in err_str or "too long" in err_str:
        return ContextWindowExceededError(str(error), provider_name=provider_name, model_name=model_name, raw_error=error)
    elif "quota" in err_str or "insufficient_quota" in err_str or "credit" in err_str:
        return ProviderQuotaError(str(error), provider_name=provider_name, model_name=model_name, raw_error=error)
    elif "500" in err_str or "502" in err_str or "503" in err_str or "unavailable" in err_str:
        return ProviderUnavailableError(str(error), provider_name=provider_name, model_name=model_name, raw_error=error)
    else:
        return InvalidRequestError(str(error), provider_name=provider_name, model_name=model_name, raw_error=error)
