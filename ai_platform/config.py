"""Validated, secret-safe provider configuration."""
import ipaddress
import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class ProviderConfig:
    provider_name: str
    model_name: str
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: float = 60.0
    max_retries: int = 1
    api_key_env: str = "OPENAI_API_KEY"

    def __post_init__(self) -> None:
        if not self.provider_name or not self.model_name: raise ValueError("provider_name and model_name are required")
        if self.timeout_seconds <= 0: raise ValueError("timeout_seconds must be positive")
        if self.max_retries < 1: raise ValueError("max_retries must be >= 1")
        parsed = urlparse(self.base_url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            raise ValueError("base_url must be an absolute HTTP(S) URL")
        host = parsed.hostname.lower()
        if parsed.scheme == "http" and host not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("HTTP base_url is only permitted for local gateways")
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_link_local or ip.is_multicast or str(ip) == "169.254.169.254":
                raise ValueError("base_url targets a blocked network address")
        except ValueError as exc:
            if str(exc).startswith("base_url targets"):
                raise

    @classmethod
    def from_env(cls, provider_name: str = "openai-compatible", model_name: str = "gpt-4o-mini") -> "ProviderConfig":
        return cls(provider_name, model_name, os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                   float(os.getenv("AI_PLATFORM_TIMEOUT_SECONDS", "60")),
                   int(os.getenv("AI_PLATFORM_MAX_RETRIES", "1")))

    def to_public_dict(self) -> dict:
        return {"provider_name": self.provider_name, "model_name": self.model_name,
                "base_url": self.base_url, "timeout_seconds": self.timeout_seconds,
                "max_retries": self.max_retries, "api_key_env": self.api_key_env}
