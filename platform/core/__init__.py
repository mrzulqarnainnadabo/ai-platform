"""AI Platform Kernel Core Contracts."""

from platform.core.capabilities import (
    MediaCapability,
    ModelCapabilities,
    ProviderCapabilities,
)
from platform.core.config import (
    ModelConfig,
    ResponseFormat,
    ResponseFormatType,
    ToolDefinition,
    ToolFunction,
)
from platform.core.context import CancellationToken, ExecutionContext
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
from platform.core.messages import (
    ContentPart,
    Message,
    Role,
    ToolCall,
    ToolResult,
)
from platform.core.provider import IModelProvider
from platform.core.response import FinishReason, ModelResponse, TokenUsage

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
