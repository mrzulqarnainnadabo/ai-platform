"""Architectural Guard Test for AI Platform Kernel.

Proves that platform/core does NOT import provider-specific SDKs or application modules.
"""

import importlib
import inspect
import sys
import unittest

import platform.core


class TestArchitecturalGuard(unittest.TestCase):
    """Ensures platform.core remains clean, dependency-light, and provider-neutral."""

    FORBIDDEN_IMPORTS = [
        "openai",
        "anthropic",
        "google.generativeai",
        "google.genai",
        "groq",
        "ollama",
        "phidata",
        "agno",
        "langchain",
        "crewai",
        "autogen",
        "pydantic_ai",
        "applications",
        "starter_ai_agents",
        "advanced_ai_agents",
    ]

    def test_kernel_has_no_forbidden_imports(self) -> None:
        """Verifies that no forbidden vendor SDKs or application packages are loaded by platform.core."""
        # Force import of all platform.core modules
        modules = [
            "platform.core",
            "platform.core.errors",
            "platform.core.context",
            "platform.core.capabilities",
            "platform.core.messages",
            "platform.core.config",
            "platform.core.response",
            "platform.core.provider",
        ]
        for mod_name in modules:
            mod = importlib.import_module(mod_name)
            source = inspect.getsource(mod)

            for forbidden in self.FORBIDDEN_IMPORTS:
                self.assertNotIn(
                    f"import {forbidden}",
                    source,
                    f"Forbidden import '{forbidden}' found in {mod_name}",
                )
                self.assertNotIn(
                    f"from {forbidden}",
                    source,
                    f"Forbidden import '{forbidden}' found in {mod_name}",
                )

    def test_loaded_sys_modules_purity(self) -> None:
        """Verifies that importing platform.core did not load vendor SDKs into sys.modules."""
        for forbidden in ["openai", "anthropic", "groq", "ollama", "phidata", "agno"]:
            self.assertNotIn(
                forbidden,
                sys.modules,
                f"Forbidden vendor module '{forbidden}' was dynamically loaded into sys.modules",
            )


if __name__ == "__main__":
    unittest.main()
