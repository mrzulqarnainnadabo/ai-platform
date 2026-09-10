import ast
from pathlib import Path


def imports_for(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_kernel_runtime_policy_are_provider_and_app_free():
    root = Path("ai_platform")
    for package in (root / "core", root / "runtime", root / "policy"):
        for path in package.rglob("*.py"):
            imports = list(imports_for(path))
            assert not any(i.startswith(("openai", "anthropic", "google", "boto3")) for i in imports), path
            assert not any(i.startswith(("starter_ai_agents", "advanced_ai_agents", "applications")) for i in imports), path


def test_stdlib_platform_namespace_is_not_shadowed():
    assert not Path("platform").exists()
    import platform
    assert hasattr(platform, "system")
