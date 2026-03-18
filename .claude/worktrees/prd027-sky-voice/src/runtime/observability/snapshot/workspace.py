# -*- coding: utf-8 -*-
"""
Configura workspace do Snapshot Service.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

WORKSPACE_ENV = "SKYBRIDGE_WORKSPACE"


def resolve_workspace_root() -> Path:
    """Resolve o diretorio base do workspace."""
    override = os.getenv(WORKSPACE_ENV)
    base = Path(override) if override else Path("workspace")
    return base.expanduser().resolve()


def ensure_workspace() -> dict[str, Path]:
    """Garante que a estrutura de workspace existe e e gravavel."""
    root = resolve_workspace_root()
    skybridge_root = root / "skybridge"
    snapshots_dir = skybridge_root / "snapshots"
    diffs_dir = skybridge_root / "diffs"

    for path in (skybridge_root, snapshots_dir, diffs_dir):
        path.mkdir(parents=True, exist_ok=True)

    try:
        with tempfile.NamedTemporaryFile(dir=skybridge_root, delete=True) as tmp:
            tmp.write(b"ok")
            tmp.flush()
    except OSError as exc:
        raise RuntimeError(
            f"Workspace sem permissao de escrita: {skybridge_root}"
        ) from exc

    return {
        "root": root,
        "skybridge": skybridge_root,
        "snapshots": snapshots_dir,
        "diffs": diffs_dir,
    }
