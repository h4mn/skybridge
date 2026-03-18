# -*- coding: utf-8 -*-
"""
Version module for Skybridge.

Single Source of Truth: Git Tags via setuptools_scm (PL001)
Priority cascade for version detection:
  1. Auto-generated _version.py (from git tags via setuptools_scm)
  2. Git describe (development fallback)
  3. Unknown (last resort)

DO NOT EDIT __version__ directly - it is auto-generated from git tags.
"""

import subprocess
from pathlib import Path

# Tenta 1: setuptools_scm auto-generated (preferred)
# Tenta import relativo primeiro (pacote), depois absoluto (direto)
try:
    from ._version import version as __version__
except ImportError:
    try:
        from _version import version as __version__
    except ImportError:
        # Tenta 2: Git describe (fallback para desenvolvimento)
        try:
            # Tenta pegar a tag mais recente
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            if result.returncode == 0:
                tag = result.stdout.strip().lstrip("v")
                # Adicionar sufixo .dev para indicar desenvolvimento
                __version__ = f"{tag}.dev"
            else:
                raise subprocess.CalledProcessError(result.returncode, "git")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # Tenta 3: Fallback final
            __version__ = "0.0.0-unknown"

__all__ = ["__version__"]
