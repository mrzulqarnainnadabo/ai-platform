from typing import Dict
from ai_platform.core.provider import IModelProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, IModelProvider] = {}

    def register(self, provider: IModelProvider) -> None:
        name = provider.provider_name
        if not name or not isinstance(name, str):
            raise ValueError("provider_name must be a non-empty string")
        self._providers[name] = provider

    def resolve(self, provider_name: str) -> IModelProvider:
        try:
            return self._providers[provider_name]
        except KeyError as exc:
            raise ValueError(f"Unknown provider: {provider_name}") from exc

    def names(self):
        return tuple(sorted(self._providers))
