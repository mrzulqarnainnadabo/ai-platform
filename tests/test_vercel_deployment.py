"""Regression guards for the Vercel production dependency boundary."""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
_FORBIDDEN_PACKAGES = ("sentence-transformers", "sentence_transformers", "torch", "transformers")


def test_vercel_has_one_modern_function_configuration_without_legacy_builds():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert "builds" not in config
    assert set(config["functions"]) == {"api/index.py", "api/frontdoor.py"}
    assert config["functions"]["api/index.py"]["includeFiles"] == "config/models.yaml"
    for function in config["functions"].values():
        excluded = function["excludeFiles"]
        for pattern in ("tests/**", "docs/**", ".git/**", "third_party/**", "**/*.pyc"):
            assert pattern in excluded


def test_vercel_declares_runtime_dependencies_in_the_effective_project_manifest():
    root_requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert not (ROOT / "api" / "requirements.txt").exists()
    for dependency in (
        "fastapi>=0.115,<1",
        "starlette>=0.40",
        "pydantic>=2",
        "supabase>=2.28,<3",
        "httpx>=0.27",
        "mangum>=0.17,<1",
        "pyyaml>=6.0,<7",
    ):
        assert dependency.lower() in pyproject.lower()
    assert all(package not in root_requirements for package in _FORBIDDEN_PACKAGES)
    assert "pyyaml" in root_requirements


def test_production_entrypoints_import_without_heavy_ml_packages():
    script = """
import builtins
import sys

forbidden = {"sentence_transformers", "torch", "transformers"}
real_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name.split(".", 1)[0] in forbidden:
        raise AssertionError(f"forbidden ML import: {name}")
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
import api.index  # noqa: F401
import api.frontdoor  # noqa: F401
assert not any(name.split(".", 1)[0] in forbidden for name in sys.modules)
"""
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout
