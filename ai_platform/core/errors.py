"""Provider-neutral error taxonomy for the AI Platform kernel."""
from typing import Any, Dict, Optional


class KernelError(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        message = message if isinstance(message, str) and message else "An unclassified kernel error occurred."
        super().__init__(message)
        self.message = message
        self.details = details if isinstance(details, dict) else {}


class ProviderError(KernelError):
    def __init__(self, message: str, provider_name: str = "unknown", model_name: Optional[str] = None,
                 status_code: Optional[int] = None, raw_error: Optional[Any] = None,
                 details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, details)
        if not isinstance(provider_name, str) or not provider_name:
            raise ValueError("provider_name must be a non-empty string")
        self.provider_name = provider_name
        self.model_name = model_name
        self.status_code = status_code
        self.raw_error = raw_error

    def to_dict(self) -> Dict[str, Any]:
        return {"error_type": type(self).__name__, "message": self.message,
                "provider_name": self.provider_name, "model_name": self.model_name,
                "status_code": self.status_code, "details": self.details}


class AuthenticationError(ProviderError):
    pass


class RateLimitError(ProviderError):
    def __init__(self, message: str, retry_after_seconds: Optional[float] = None, **kwargs: Any) -> None:
        if retry_after_seconds is not None and (not isinstance(retry_after_seconds, (int, float)) or retry_after_seconds < 0):
            raise ValueError("retry_after_seconds must be a non-negative number")
        super().__init__(message, **kwargs)
        self.retry_after_seconds = retry_after_seconds
        if retry_after_seconds is not None:
            self.details["retry_after_seconds"] = retry_after_seconds


class InvalidRequestError(ProviderError):
    pass


class ProviderTimeoutError(ProviderError):
    """The provider operation exceeded its deadline."""
    pass


class CancellationError(ProviderError):
    """The caller explicitly cancelled execution."""
    pass


class ProviderQuotaError(ProviderError):
    pass


class ProviderUnavailableError(ProviderError):
    pass


class ContextWindowExceededError(ProviderError):
    def __init__(self, message: str, max_context_tokens: Optional[int] = None, **kwargs: Any) -> None:
        if max_context_tokens is not None and (not isinstance(max_context_tokens, int) or max_context_tokens <= 0):
            raise ValueError("max_context_tokens must be a positive integer")
        super().__init__(message, **kwargs)
        self.max_context_tokens = max_context_tokens
        if max_context_tokens is not None:
            self.details["max_context_tokens"] = max_context_tokens


def normalize_provider_error(error: Exception, provider_name: str = "unknown",
                             model_name: Optional[str] = None) -> ProviderError:
    if isinstance(error, ProviderError):
        return error
    text = str(error)
    lowered = text.lower()
    if "rate limit" in lowered or "429" in lowered or "too many requests" in lowered:
        return RateLimitError(text, provider_name=provider_name, model_name=model_name, raw_error=error)
    if "auth" in lowered or "api key" in lowered or "unauthorized" in lowered or "401" in lowered:
        return AuthenticationError(text, provider_name=provider_name, model_name=model_name, raw_error=error)
    if "timeout" in lowered or "timed out" in lowered or "deadline" in lowered:
        return ProviderTimeoutError(text, provider_name=provider_name, model_name=model_name, raw_error=error)
    if "cancel" in lowered:
        return CancellationError(text, provider_name=provider_name, model_name=model_name, raw_error=error)
    if "context length" in lowered or "maximum context" in lowered or "too long" in lowered:
        return ContextWindowExceededError(text, provider_name=provider_name, model_name=model_name, raw_error=error)
    if "quota" in lowered or "insufficient_quota" in lowered or "credit" in lowered:
        return ProviderQuotaError(text, provider_name=provider_name, model_name=model_name, raw_error=error)
    if any(code in lowered for code in ("500", "502", "503", "unavailable")):
        return ProviderUnavailableError(text, provider_name=provider_name, model_name=model_name, raw_error=error)
    return InvalidRequestError(text, provider_name=provider_name, model_name=model_name, raw_error=error)
