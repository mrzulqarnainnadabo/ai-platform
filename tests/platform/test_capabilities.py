"""Tests for ProviderCapabilities and ModelCapabilities."""

import unittest

from platform.core.capabilities import (
    MediaCapability,
    ModelCapabilities,
    ProviderCapabilities,
)


class TestCapabilities(unittest.TestCase):
    """Tests model and provider capability discovery contracts."""

    def test_model_capabilities_defaults(self) -> None:
        caps = ModelCapabilities()
        self.assertTrue(caps.supports_streaming)
        self.assertTrue(caps.supports_structured_output)
        self.assertTrue(caps.supports_tools)
        self.assertFalse(caps.supports_vision)
        self.assertEqual(caps.max_context_tokens, 128000)

    def test_model_capabilities_serialization(self) -> None:
        caps = ModelCapabilities(
            supports_vision=True,
            supports_audio=True,
            max_context_tokens=200000,
            supported_media=[MediaCapability.TEXT, MediaCapability.VISION, MediaCapability.AUDIO],
        )
        data = caps.to_dict()
        self.assertTrue(data["supports_vision"])
        self.assertIn("vision", data["supported_media"])

        restored = ModelCapabilities.from_dict(data)
        self.assertTrue(restored.supports_vision)
        self.assertTrue(restored.supports_audio)
        self.assertEqual(restored.max_context_tokens, 200000)

    def test_provider_capabilities_get_model(self) -> None:
        p_caps = ProviderCapabilities(
            provider_name="openai",
            supported_models=["gpt-4o", "gpt-4o-mini"],
            model_capabilities={
                "gpt-4o": ModelCapabilities(supports_vision=True, max_context_tokens=128000),
            },
        )
        data = p_caps.to_dict()
        self.assertEqual(data["provider_name"], "openai")

        restored = ProviderCapabilities.from_dict(data)
        g4_caps = restored.get_model_capabilities("gpt-4o")
        self.assertTrue(g4_caps.supports_vision)

        unknown_caps = restored.get_model_capabilities("unknown-model")
        self.assertFalse(unknown_caps.supports_vision)


if __name__ == "__main__":
    unittest.main()
