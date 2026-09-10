from ai_platform.core.errors import KernelError


class PolicyEvaluationError(KernelError):
    pass


class InvalidCapabilityError(KernelError):
    pass


class PolicyDeniedError(KernelError):
    pass


class HumanApprovalRequiredError(KernelError):
    pass
