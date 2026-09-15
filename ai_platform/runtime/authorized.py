from typing import AsyncGenerator, List, Optional
from ai_platform.core.config import ModelConfig
from ai_platform.core.context import ExecutionContext
from ai_platform.core.messages import Message
from ai_platform.models.registry import ModelPolicy, ModelRegistry
from .model_runtime import ModelRuntime, RuntimeResult
from .run_engine import RunEngine
from ai_platform.policy.approval import ApprovalService, HumanApproval
from ai_platform.policy.authorization import AuthorizationContext
from ai_platform.policy.capabilities import Capability, parse_capability
from ai_platform.policy.decisions import Decision
from ai_platform.policy.errors import HumanApprovalRequiredError, InvalidCapabilityError, PolicyDeniedError
from ai_platform.policy.evaluator import SimplePermissionEvaluator


class AuthorizedModelRuntime:
    """Application-facing model boundary: AuthZ -> approval -> budget -> durable run -> provider."""
    def __init__(self, runtime: ModelRuntime, evaluator: Optional[SimplePermissionEvaluator] = None,
                 run_engine: Optional[RunEngine] = None, model_registry: Optional[ModelRegistry] = None,
                 approval_service: Optional[ApprovalService] = None) -> None:
        self.runtime = runtime
        self.evaluator = evaluator or SimplePermissionEvaluator()
        self.run_engine = run_engine
        self.model_registry = model_registry or ModelRegistry()
        self.approval_service = approval_service

    def _authorize(self, auth: AuthorizationContext, capability: str, approval: Optional[HumanApproval],
                   approval_id: Optional[str] = None) -> Capability:
        try: cap = parse_capability(capability)
        except ValueError as exc: raise InvalidCapabilityError(str(exc)) from exc
        decision = self.evaluator.evaluate(auth, cap)
        if decision.decision == Decision.DENY: raise PolicyDeniedError(decision.reason)
        if decision.decision == Decision.REQUIRE_HUMAN and approval is None and approval_id and self.approval_service:
            approval = self.approval_service.get(approval_id=approval_id, tenant_id=auth.identity.tenant_id,
                                                 subject_id=auth.identity.subject, capability=cap.value)
        if decision.decision == Decision.REQUIRE_HUMAN and (approval is None or not approval.matches(auth.identity, cap)):
            raise HumanApprovalRequiredError(decision.reason)
        return cap

    @staticmethod
    def _validate_tenant(auth: AuthorizationContext, context: Optional[ExecutionContext]) -> None:
        if context is not None and context.tenant_id != auth.identity.tenant_id:
            raise PolicyDeniedError("Authorization tenant does not match execution tenant")

    def _policy_for(self, config: ModelConfig, explicit: Optional[ModelPolicy]) -> Optional[ModelPolicy]:
        if explicit: return explicit
        attached = getattr(config, "_model_policy", None)
        if attached: return attached
        for policy in self.model_registry.all():
            if policy.model == config.model_name: return policy
        return None

    async def generate(self, auth: AuthorizationContext, messages: List[Message], config: ModelConfig,
                       provider_name: str, context: Optional[ExecutionContext] = None,
                       approval: Optional[HumanApproval] = None, approval_id: Optional[str] = None,
                       model_policy: Optional[ModelPolicy] = None):
        self._validate_tenant(auth, context)
        self._authorize(auth, Capability.MODEL_GENERATE.value, approval, approval_id)
        resolved_policy = self._policy_for(config, model_policy)
        if self.run_engine and resolved_policy:
            return await self.run_engine.generate(tenant_id=auth.identity.tenant_id, subject_id=auth.identity.subject,
                                                  model_policy=resolved_policy, messages=messages, config=config, context=context)
        return await self.runtime.generate(messages, config, provider_name, context)

    async def stream(self, auth: AuthorizationContext, messages: List[Message], config: ModelConfig,
                     provider_name: str, context: Optional[ExecutionContext] = None,
                     approval: Optional[HumanApproval] = None, approval_id: Optional[str] = None,
                     model_policy: Optional[ModelPolicy] = None) -> AsyncGenerator[RuntimeResult, None]:
        self._validate_tenant(auth, context)
        self._authorize(auth, Capability.MODEL_STREAM.value, approval, approval_id)
        async for result in self.runtime.stream(messages, config, provider_name, context):
            yield result
