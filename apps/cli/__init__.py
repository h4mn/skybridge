# -*- coding: utf-8 -*-
"""
Skybridge CLI — Interface de linha de comando sb.

Conforme PRD009-RF15: CLI sb com subcomandos rpc.

Versionamento: Herdado do Core Skybridge (ADR012)
"""

# Import version from Core package
try:
    from skybridge import __version__ as skybridge_version
    __version__ = skybridge_version
except ImportError:
    __version__ = "0.1.0"
