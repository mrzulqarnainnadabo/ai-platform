"""Deterministic capability and authorization boundary."""
from .authorization import AuthorizationContext, AuthContextProvider, Identity, Permissions
from .capabilities import Capability, parse_capability
from .decisions import Decision, PolicyDecision
from .evaluator import SimplePermissionEvaluator
from .approval import HumanApproval
from .errors import HumanApprovalRequiredError, InvalidCapabilityError, PolicyDeniedError, PolicyEvaluationError

__all__ = ["AuthorizationContext", "AuthContextProvider", "Identity", "Permissions", "Capability", "parse_capability", "Decision", "PolicyDecision", "SimplePermissionEvaluator", "HumanApproval", "HumanApprovalRequiredError", "InvalidCapabilityError", "PolicyDeniedError", "PolicyEvaluationError"]
