"""Validated, secret-safe provider configuration helpers.

URL validation lives here so host wiring and provider adapters share one rule set
and cannot drift. Secrets are never stored on ProviderConfig itself—only the
environment variable *name* is recorded.
"""
from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from urllib.parse import urlparse


def validate_provider_base_url(url: str) -> str:
    """Normalize and validate a provider base URL.

    Allows HTTPS public hosts and loopback HTTP(S). Rejects non-HTTP schemes,
    non-loopback HTTP, and literal private/link-local/reserved IPs (including
    cloud metadata addresses). Returns the stripped URL without a trailing slash.
    """
    cleaned = (url or "").strip().rstrip("/")
    if not cleaned:
        raise ValueError("base_url is required")

    parsed = urlparse(cleaned)
    if parsed.scheme not in ("https", "http"):
        raise ValueError("base_url scheme must be https (or http for loopback only)")
    if not parsed.hostname:
        raise ValueError("base_url must include a hostname")

    host = parsed.hostname.lower()
    is_loopback_name = host in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme == "http" and not is_loopback_name:
        raise ValueError("base_url must use HTTPS unless targeting localhost")

    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            if not ip.is_loopback:
                raise ValueError("base_url must not target private, link-local, or reserved addresses")
    except ValueError as exc:
        if "base_url must not" in str(exc):
            raise
        # Hostname is not a literal IP — public DNS names are allowed.
        pass

    return cleaned


@dataclass(frozen=True)
class ProviderConfig:
    """Library-level provider settings (no secret values)."""

    provider_name: str
    model_name: str
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: float = 60.0
    max_retries: int = 1
    api_key_env: str = "OPENAI_API_KEY"

    def __post_init__(self) -> None:
        if not self.provider_name or not self.model_name:
            raise ValueError("provider_name and model_name are required")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        object.__setattr__(self, "base_url", validate_provider_base_url(self.base_url))

    @classmethod
    def from_env(
        cls,
        provider_name: str = "openai-compatible",
        model_name: str = "gpt-4o-mini",
    ) -> "ProviderConfig":
        return cls(
            provider_name,
            model_name,
            os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            float(os.getenv("AI_PLATFORM_TIMEOUT_SECONDS", "60")),
            int(os.getenv("AI_PLATFORM_MAX_RETRIES", "1")),
        )

    def to_public_dict(self) -> dict:
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "base_url": self.base_url,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "api_key_env": self.api_key_env,
        }
