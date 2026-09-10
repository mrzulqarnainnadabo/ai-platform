"""AI Platform Kernel Core Public Contracts."""

from ai_platform.core.capabilities import (
    MediaCapability,
    ModelCapabilities,
    ProviderCapabilities,
)
from ai_platform.core.config import (
    ModelConfig,
    ResponseFormat,
    ResponseFormatType,
    ToolDefinition,
    ToolFunction,
)
from ai_platform.core.context import CancellationToken, ExecutionContext
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
from ai_platform.core.messages import (
    ContentPart,
    Message,
    Role,
    ToolCall,
    ToolResult,
)
from ai_platform.core.provider import IModelProvider
from ai_platform.core.response import FinishReason, ModelResponse, TokenUsage

__all__ = [
    # Errors
    "KernelError",
    "ProviderError",
    "AuthenticationError",
    "RateLimitError",
    "InvalidRequestError",
    "ProviderTimeoutError",
    "ProviderQuotaError",
    "ProviderUnavailableError",
    "ContextWindowExceededError",
    "normalize_provider_error",
    # Context
    "CancellationToken",
    "ExecutionContext",
    # Capabilities
    "MediaCapability",
    "ModelCapabilities",
    "ProviderCapabilities",
    # Messages
    "Role",
    "ContentPart",
    "ToolCall",
    "ToolResult",
    "Message",
    # Config
    "ResponseFormatType",
    "ResponseFormat",
    "ToolFunction",
    "ToolDefinition",
    "ModelConfig",
    # Response
    "FinishReason",
    "TokenUsage",
    "ModelResponse",
    # Provider
    "IModelProvider",
]
