"""Tests for ProviderCapabilities and ModelCapabilities."""

import unittest

from ai_platform.core.capabilities import (
    MediaCapability,
    ModelCapabilities,
    ProviderCapabilities,
)


class TestCapabilities(unittest.TestCase):
    """Tests model and provider capability discovery contracts and validation."""

    def test_model_capabilities_validation(self) -> None:
        with self.assertRaises(ValueError):
            ModelCapabilities(max_context_tokens=-100)

        with self.assertRaises(ValueError):
            ModelCapabilities(max_output_tokens=0)

    def test_provider_capabilities_validation(self) -> None:
        with self.assertRaises(ValueError):
            ProviderCapabilities(provider_name="")

        with self.assertRaises(ValueError):
            p = ProviderCapabilities(provider_name="test")
            p.get_model_capabilities("")

    def test_capabilities_serialization(self) -> None:
        p_caps = ProviderCapabilities(
            provider_name="openai",
            supported_models=["gpt-4o"],
            model_capabilities={
                "gpt-4o": ModelCapabilities(supports_vision=True),
            },
        )
        data = p_caps.to_dict()
        restored = ProviderCapabilities.from_dict(data)
        self.assertTrue(restored.get_model_capabilities("gpt-4o").supports_vision)


if __name__ == "__main__":
    unittest.main()
