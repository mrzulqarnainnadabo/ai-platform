"""Lightweight liveness/readiness contracts for deployable hosts."""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class PlatformHealth:
    status: HealthStatus
    version: str
    checks: dict


def liveness(version: str = "unknown") -> PlatformHealth:
    return PlatformHealth(HealthStatus.HEALTHY, version, {"process": "up"})


def readiness(version: str = "unknown", provider_check: Optional[Callable[[], bool]] = None) -> PlatformHealth:
    checks = {"configuration": "valid"}
    if provider_check is not None:
        try:
            checks["provider"] = "reachable" if provider_check() else "unreachable"
        except Exception:
            checks["provider"] = "unreachable"
    ready = all(v not in ("unreachable", "invalid") for v in checks.values())
    return PlatformHealth(HealthStatus.HEALTHY if ready else HealthStatus.NOT_READY, version, checks)
