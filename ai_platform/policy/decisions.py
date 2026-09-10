from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_HUMAN = "REQUIRE_HUMAN"


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reason: str
    policy_id: str = "simple-permission-v1"
