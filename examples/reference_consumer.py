"""Minimal application integration pattern; domain rules belong in the consumer."""
import asyncio
from ai_platform.core import Message, ModelConfig, Role
from ai_platform.policy import AuthorizationContext, Identity, Permissions, Capability
from ai_platform.runtime import AuthorizedModelRuntime, ModelRuntime, MockModelProvider, ProviderRegistry


def build_runtime() -> AuthorizedModelRuntime:
    registry = ProviderRegistry()
    registry.register(MockModelProvider())
    return AuthorizedModelRuntime(ModelRuntime(registry))


async def main() -> None:
    auth = AuthorizationContext(Identity("reference-user", "reference-tenant"), Permissions(frozenset({Capability.MODEL_GENERATE})))
    result = await build_runtime().generate(auth, [Message(Role.USER, "Say hello")], ModelConfig("mock"), "mock")
    print(result.response.message.content)


if __name__ == "__main__":
    asyncio.run(main())
