"""AI Platform Infrastructure Package with Standard Library Passthrough."""

import sys
import importlib.util

# Load standard library platform module to prevent namespace shadowing for uuid, urllib, etc.
_stdlib_platform = None
for _path in sys.path:
    if _path and 'site-packages' not in _path and 'app' not in _path and _path != '':
        try:
            _spec = importlib.util.spec_from_file_location("_stdlib_platform", f"{_path}/platform.py")
            if _spec and _spec.loader:
                _mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                _stdlib_platform = _mod
                break
        except Exception:
            pass

__version__ = "0.1.0"


def __getattr__(name: str):
    if _stdlib_platform and hasattr(_stdlib_platform, name):
        return getattr(_stdlib_platform, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
