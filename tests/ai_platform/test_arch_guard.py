"""Architectural Guard Test and Standard Library Namespace Regression Test."""

import ast
import importlib
import inspect
import os
import sys
import unittest


class TestArchitecturalGuard(unittest.TestCase):
    """Ensures ai_platform.core remains dependency-light, vendor-neutral, and namespace-pure."""

    FORBIDDEN_MODULES = [
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

    def test_stdlib_platform_namespace_coexistence(self) -> None:
        """Explicit regression test proving Python's standard-library platform module and ai_platform co-exist without collision."""
        import platform as std_platform
        import ai_platform.core

        self.assertTrue(hasattr(std_platform, "system"), "Standard library platform module missing system()")
        self.assertTrue(hasattr(std_platform, "python_version"), "Standard library platform module missing python_version()")
        self.assertTrue(hasattr(ai_platform.core, "Message"), "ai_platform.core missing Message contract")

    def test_ast_for_forbidden_imports(self) -> None:
        """Parses AST of all ai_platform/core/*.py files to verify zero vendor SDK or application imports."""
        core_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ai_platform", "core")
        py_files = [
            os.path.join(core_dir, f)
            for f in os.listdir(core_dir)
            if f.endswith(".py")
        ]

        for filepath in py_files:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filepath)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in self.FORBIDDEN_MODULES:
                            self.assertFalse(
                                alias.name.startswith(forbidden),
                                f"Forbidden AST import '{alias.name}' in {filepath}",
                            )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for forbidden in self.FORBIDDEN_MODULES:
                            self.assertFalse(
                                node.module.startswith(forbidden),
                                f"Forbidden AST importFrom '{node.module}' in {filepath}",
                            )

    def test_loaded_sys_modules_purity(self) -> None:
        """Verifies that importing ai_platform.core did not load vendor SDKs into sys.modules."""
        for forbidden in ["openai", "anthropic", "groq", "ollama", "phidata", "agno"]:
            self.assertNotIn(
                forbidden,
                sys.modules,
                f"Forbidden vendor module '{forbidden}' was dynamically loaded into sys.modules",
            )


if __name__ == "__main__":
    unittest.main()
