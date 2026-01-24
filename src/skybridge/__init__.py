# -*- coding: utf-8 -*-
"""
Skybridge Application Module.

Versionamento: Single source of truth via arquivo VERSION (ADR012)
"""

from pathlib import Path

# Try to read from VERSION file, fall back to default
_VERSION_FILE = Path(__file__).parent.parent.parent / "VERSION"

def _read_version(default: str) -> str:
    """Read SKYBRIDGE_VERSION from VERSION file."""
    if _VERSION_FILE.exists():
        with open(_VERSION_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "SKYBRIDGE_VERSION":
                        return v.strip()
    return default

__version__ = _read_version("0.1.0")

__all__ = [
    '__version__',
]
