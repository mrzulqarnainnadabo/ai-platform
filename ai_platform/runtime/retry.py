from dataclasses import dataclass
from typing import Tuple, Type
from ai_platform.core.errors import ProviderUnavailableError, RateLimitError, ProviderError


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    backoff_seconds: float = 0.25

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.backoff_seconds < 0:
            raise ValueError("backoff_seconds must be >= 0")

    @property
    def retryable_errors(self) -> Tuple[Type[ProviderError], ...]:
        return (RateLimitError, ProviderUnavailableError)
