# -*- coding: utf-8 -*-
"""Utilitários para capturar diffs do git."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def get_git_diff(worktree_path: str | Path) -> dict[str, Any]:
    """
    Captura informações de diff do git worktree.

    Retorna dicionário com:
    - files: lista de arquivos alterados com status (A/M/D)
    - diffs: dict mapeando caminho do arquivo -> diff unificado
    - summary: contagem de arquivos por status
    """
    worktree = Path(worktree_path)
    if not worktree.exists():
        logger.warning(f"Worktree não existe: {worktree_path}")
        return {"files": [], "diffs": {}, "summary": {}}

    logger.info(f"Capturando git diff | worktree={worktree_path}")

    try:
        # Obtém lista de arquivos alterados (com status)
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=worktree,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        files_with_status: list[dict[str, str]] = []
        added: list[str] = []
        modified: list[str] = []
        deleted: list[str] = []

        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            # Formato: XY path
            # X = staging area status, Y = working tree status
            status = line[:2].strip()
            path = line[3:]
            files_with_status.append({"path": path, "status": status})

            if status == "A":
                added.append(path)
            elif status in ("M", "MM"):
                modified.append(path)
            elif status == "D":
                deleted.append(path)

        logger.debug(
            f"Arquivos alterados | added={len(added)} | modified={len(modified)} | deleted={len(deleted)}",
            extra={
                "worktree_path": str(worktree_path),
                "added_count": len(added),
                "modified_count": len(modified),
                "deleted_count": len(deleted),
                "files": [f["path"] for f in files_with_status]
            }
        )

        # Captura diff unificado dos arquivos modificados
        diffs: dict[str, str] = {}
        for path in modified:
            try:
                diff_result = subprocess.run(
                    ["git", "diff", "--unified=3", "--", path],
                    cwd=worktree,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if diff_result.stdout.strip():
                    diffs[path] = diff_result.stdout.strip()
                    logger.debug(f"Diff capturado | path={path} | lines={diff_result.stdout.count(chr(10))}")
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
                diffs[path] = "[Erro ao capturar diff]"
                logger.warning(f"Erro ao capturar diff | path={path} | error={str(e)}")

        # Para arquivos novos, tenta capturar o conteúdo
        for path in added:
            try:
                full_path = worktree / path
                if full_path.is_file():
                    # Lê primeiras 100 linhas do arquivo novo
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        lines = []
                        for i, line in enumerate(f, 1):
                            if i > 100:
                                lines.append(f"... (restante do arquivo truncado)")
                                break
                            lines.append(line.rstrip("\n\r"))
                        content = "\n".join(lines)
                        diffs[path] = f"--- ARQUIVO NOVO ---\n{content}"
                        logger.debug(f"Arquivo novo capturado | path={path} | lines={len(lines)}")
            except Exception as e:
                diffs[path] = "[Arquivo novo - erro ao ler conteúdo]"
                logger.warning(f"Erro ao ler arquivo novo | path={path} | error={str(e)}")

        summary = {
            "added": len(added),
            "modified": len(modified),
            "deleted": len(deleted),
            "total": len(files_with_status),
        }

        logger.info(
            f"Git diff capturado com sucesso | worktree={worktree_path} | total={summary['total']}",
            extra={
                "worktree_path": str(worktree_path),
                **summary
            }
        )

        return {
            "files": files_with_status,
            "diffs": diffs,
            "summary": summary,
        }

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.error(
            f"Erro ao capturar git diff | worktree={worktree_path} | error={str(e)}",
            extra={
                "worktree_path": str(worktree_path),
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )
        return {
            "files": [],
            "diffs": {},
            "summary": {"error": str(e)},
        }


def get_git_changes_summary(worktree_path: str | Path) -> dict[str, Any]:
    """
    Obtém resumo de alterações do git (sem diff de conteúdo).

    Retorna dict com:
    - staged: arquivos em staging
    - unstaged: arquivos modificados mas não staged
    - untracked: arquivos não rastreados
    """
    worktree = Path(worktree_path)
    if not worktree.exists():
        logger.warning(f"Worktree não existe: {worktree_path}")
        return {"staged": 0, "unstaged": 0, "untracked": 0}

    logger.debug(f"Capturando resumo de alterações git | worktree={worktree_path}")

    try:
        # Usa git diff para contar mudanças
        staged_result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=worktree,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        staged = len([line for line in staged_result.stdout.strip().splitlines() if line])

        unstaged_result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=worktree,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        unstaged = len([line for line in unstaged_result.stdout.strip().splitlines() if line])

        untracked_result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=worktree,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        untracked = len([line for line in untracked_result.stdout.strip().splitlines() if line])

        logger.debug(
            f"Resumo de alterações | staged={staged} | unstaged={unstaged} | untracked={untracked}",
            extra={
                "worktree_path": str(worktree_path),
                "staged": staged,
                "unstaged": unstaged,
                "untracked": untracked
            }
        )

        return {"staged": staged, "unstaged": unstaged, "untracked": untracked}

    except Exception as e:
        logger.error(
            f"Erro ao capturar resumo git | worktree={worktree_path} | error={str(e)}",
            extra={
                "worktree_path": str(worktree_path),
                "error": str(e)
            }
        )
        return {"staged": 0, "unstaged": 0, "untracked": 0}
