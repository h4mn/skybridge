# -*- coding: utf-8 -*-
"""
Skybridge Kernel — SDK estável para apps e plugins.

Este módulo fornece:
- Result type para retornos tipados
- Envelope para respostas de API
- Registry para handlers CQRS

Versionamento: Single source of truth via arquivo VERSION (ADR012)
"""

from pathlib import Path

# Try to read from VERSION file, fall back to default
_VERSION_FILE = Path(__file__).parent.parent.parent.parent / "VERSION"

def _read_version(default: str) -> str:
    """Read KERNEL_API_VERSION from VERSION file."""
    if _VERSION_FILE.exists():
        with open(_VERSION_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "KERNEL_API_VERSION":
                        return v.strip()
    return default

__kernel_api_version__ = _read_version("0.1.0")

from .contracts.result import Result, Status
from .envelope.envelope import Envelope
from .registry.query_registry import QueryRegistry, QueryHandler, get_query_registry

__all__ = [
    '__kernel_api_version__',
    'Result',
    'Status',
    'Envelope',
    'QueryRegistry',
    'QueryHandler',
    'get_query_registry',
]
