# -*- coding: utf-8 -*-
"""
Skybridge — Ponte entre intenção humana e execução assistida por IA.

Core package contendo:
- Kernel: SDK estável para apps e plugins
- Core: Bounded Contexts (FileOps, Tasks)
- Platform: Runtime e infraestrutura
- Infra: Implementações concretas

Versionamento: Single source of truth via arquivo VERSION (ADR012)
"""

import os
from pathlib import Path

# Try to read from VERSION file, fall back to defaults
_VERSION_FILE = Path(__file__).parent.parent.parent / "VERSION"

def _read_version(key: str, default: str) -> str:
    """Read version from VERSION file."""
    if _VERSION_FILE.exists():
        with open(_VERSION_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == key:
                        return v.strip()
    return default

__version__ = _read_version("SKYBRIDGE_VERSION", "0.1.0")
__kernel_api__ = _read_version("KERNEL_API_VERSION", "0.1.0")

# Fronteiras explícitas:
# - Apps dependem de Kernel + Application layer
# - Plugins dependem apenas do Kernel
# - Contexts não se importam entre si
# - Domain nunca importa Infra

__all__ = ["__version__", "__kernel_api__"]
