from dataclasses import dataclass
from .capabilities import Capability
from .authorization import Identity


@dataclass(frozen=True)
class HumanApproval:
    """External proof scoped to one subject and capability; never model-generated."""
    subject: str
    capability: Capability
    approval_id: str
    approver_id: str

    def matches(self, identity: Identity, capability: Capability) -> bool:
        return self.subject == identity.subject and self.capability == capability and bool(self.approval_id) and bool(self.approver_id)
