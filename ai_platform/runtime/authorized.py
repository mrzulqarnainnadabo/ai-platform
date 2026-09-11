from typing import AsyncGenerator, List, Optional
from ai_platform.core.config import ModelConfig
from ai_platform.core.context import ExecutionContext
from ai_platform.core.messages import Message
from .model_runtime import ModelRuntime, RuntimeResult
from ai_platform.policy.approval import HumanApproval
from ai_platform.policy.authorization import AuthorizationContext
from ai_platform.policy.capabilities import Capability, parse_capability
from ai_platform.policy.decisions import Decision
from ai_platform.policy.errors import HumanApprovalRequiredError, InvalidCapabilityError, PolicyDeniedError
from ai_platform.policy.evaluator import SimplePermissionEvaluator


class AuthorizedModelRuntime:
    """Recommended application entry point enforcing deterministic policy before runtime."""
    def __init__(self, runtime: ModelRuntime, evaluator: Optional[SimplePermissionEvaluator] = None) -> None:
        self.runtime = runtime
        self.evaluator = evaluator or SimplePermissionEvaluator()

    def _authorize(self, auth: AuthorizationContext, capability: str, approval: Optional[HumanApproval]) -> Capability:
        try:
            cap = parse_capability(capability)
        except ValueError as exc:
            raise InvalidCapabilityError(str(exc)) from exc
        decision = self.evaluator.evaluate(auth, cap)
        if decision.decision == Decision.DENY:
            raise PolicyDeniedError(decision.reason)
        if decision.decision == Decision.REQUIRE_HUMAN:
            if approval is None or not approval.matches(auth.identity, cap):
                raise HumanApprovalRequiredError(decision.reason)
        return cap

    @staticmethod
    def _validate_tenant(auth: AuthorizationContext, context: Optional[ExecutionContext]) -> None:
        if context is not None and context.tenant_id != auth.identity.tenant_id:
            raise PolicyDeniedError("Authorization tenant does not match execution tenant")

    async def generate(self, auth: AuthorizationContext, messages: List[Message], config: ModelConfig,
                       provider_name: str, context: Optional[ExecutionContext] = None,
                       approval: Optional[HumanApproval] = None) -> RuntimeResult:
        self._validate_tenant(auth, context)
        self._authorize(auth, Capability.MODEL_GENERATE.value, approval)
        return await self.runtime.generate(messages, config, provider_name, context)

    async def stream(self, auth: AuthorizationContext, messages: List[Message], config: ModelConfig,
                     provider_name: str, context: Optional[ExecutionContext] = None,
                     approval: Optional[HumanApproval] = None) -> AsyncGenerator[RuntimeResult, None]:
        self._validate_tenant(auth, context)
        self._authorize(auth, Capability.MODEL_STREAM.value, approval)
        async for result in self.runtime.stream(messages, config, provider_name, context):
            yield result
