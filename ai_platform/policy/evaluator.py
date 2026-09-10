from .authorization import AuthorizationContext
from .capabilities import Capability
from .decisions import Decision, PolicyDecision
from .errors import PolicyEvaluationError


class SimplePermissionEvaluator:
    """Deterministic, fail-closed evaluator. No LLM or provider knowledge."""
    policy_id = "simple-permission-v1"

    def evaluate(self, context: AuthorizationContext, capability: Capability) -> PolicyDecision:
        try:
            if not isinstance(context, AuthorizationContext):
                raise TypeError("invalid authorization context")
            if not isinstance(capability, Capability):
                raise TypeError("invalid capability")
            if context.permissions.allows(capability):
                return PolicyDecision(Decision.ALLOW, "Capability permitted", self.policy_id)
            return PolicyDecision(Decision.DENY, "Capability not granted", self.policy_id)
        except Exception as exc:
            if isinstance(exc, PolicyEvaluationError):
                raise
            raise PolicyEvaluationError("Policy evaluation failed closed") from exc
