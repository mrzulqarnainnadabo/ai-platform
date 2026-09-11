from dataclasses import dataclass, field
from typing import FrozenSet, Mapping, Protocol
from .capabilities import Capability


@dataclass(frozen=True)
class Identity:
    subject: str
    tenant_id: str = "default"

    def __post_init__(self) -> None:
        if not self.subject or not self.tenant_id:
            raise ValueError("subject and tenant_id are required")


@dataclass(frozen=True)
class Permissions:
    capabilities: FrozenSet[Capability] = field(default_factory=frozenset)

    def allows(self, capability: Capability) -> bool:
        return capability in self.capabilities


@dataclass(frozen=True)
class AuthorizationContext:
    identity: Identity
    permissions: Permissions


class AuthContextProvider(Protocol):
    """Application-boundary protocol; implementations may map trusted sessions/JWTs."""
    def get_context(self) -> AuthorizationContext: ...
