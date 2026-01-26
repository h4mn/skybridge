# -*- coding: utf-8 -*-
"""
Schemas de validação para snapshots do Skybridge.

Garante que os snapshots tenham a estrutura mínima necessária
para exibição correta no WebUI (Worktrees.tsx).
"""
from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class SnapshotStats(BaseModel):
    """Estatísticas do snapshot."""
    files: int | None = None
    lines: int | None = None
    total_files: int | None = None
    total_dirs: int | None = None
    total_size: int | None = None
    file_types: dict[str, int] | None = None


class GitDiffSummary(BaseModel):
    """Resumo de diffs do git."""
    added: int = 0
    modified: int = 0
    deleted: int = 0
    total: int = 0


class GitDiffFile(BaseModel):
    """Arquivo alterado no git."""
    path: str
    status: str  # A, M, MM, D, R


class GitDiffData(BaseModel):
    """Dados de diff do git."""
    files: list[dict[str, Any]] = []
    diffs: dict[str, str] = {}
    summary: dict[str, Any] | None = None

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: dict[str, Any] | None) -> dict[str, Any]:
        """Garante que summary tenha os campos mínimos."""
        if v is None or not isinstance(v, dict):
            return {"added": 0, "modified": 0, "deleted": 0, "total": 0}
        return {
            "added": v.get("added", 0),
            "modified": v.get("modified", 0),
            "deleted": v.get("deleted", 0),
            "total": v.get("total", 0),
        }


class ValidationStatus(BaseModel):
    """Status de validação do worktree."""
    staged: int = 0
    unstaged: int = 0
    untracked: int = 0


class ValidationData(BaseModel):
    """Dados de validação do worktree."""
    status: dict[str, int] | None = None
    validated: bool | None = None
    can_remove: bool | None = None
    message: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: dict[str, int] | None) -> dict[str, int] | None:
        """Garante que status tenha os campos mínimos."""
        if v is None:
            return {"staged": 0, "unstaged": 0, "untracked": 0}
        if not isinstance(v, dict):
            return {"staged": 0, "unstaged": 0, "untracked": 0}
        return {
            "staged": v.get("staged", 0),
            "unstaged": v.get("unstaged", 0),
            "untracked": v.get("untracked", 0),
        }


class SnapshotMetadata(BaseModel):
    """Metadados do snapshot."""
    snapshot_id: str | None = None
    timestamp: str | None = None
    subject: str | None = None
    target: str | None = None
    depth: int | None = None
    git_hash: str | None = None
    git_branch: str | None = None
    tags: dict[str, str] | None = None


class Snapshot(BaseModel):
    """Snapshot completo."""
    metadata: dict[str, Any] | None = None
    stats: dict[str, Any] | None = None
    structure: dict[str, Any] | None = None


class CompletedSnapshot(BaseModel):
    """
    Schema para snapshot COMPLETED com estrutura completa.

    Esta é a estrutura mínima exigida pelo WebUI para exibir
    corretamente os detalhes do worktree.
    """
    status: str = Field(..., pattern="^(COMPLETED|FAILED|PROCESSING)$")
    updated_at: str
    initial: dict[str, Any] | None = None
    final: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
    git_diff: dict[str, Any] | None = None

    @field_validator("initial")
    @classmethod
    def validate_initial(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Garante que initial tenha stats mínimo."""
        if v is None:
            return {"stats": {"files": 0, "lines": 0}}
        if "stats" not in v:
            v["stats"] = {"files": 0, "lines": 0}
        elif v["stats"] is None:
            v["stats"] = {"files": 0, "lines": 0}
        return v

    @field_validator("final")
    @classmethod
    def validate_final(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Garante que final tenha stats mínimo."""
        if v is None:
            return {"stats": {"files": 0, "lines": 0}}
        if "stats" not in v:
            v["stats"] = {"files": 0, "lines": 0}
        elif v["stats"] is None:
            v["stats"] = {"files": 0, "lines": 0}
        return v

    @field_validator("validation")
    @classmethod
    def validate_validation_field(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Garante que validation tenha status mínimo."""
        if v is None:
            return {"status": {"staged": 0, "unstaged": 0, "untracked": 0}}
        if "status" not in v:
            v["status"] = {"staged": 0, "unstaged": 0, "untracked": 0}
        elif v["status"] is None:
            v["status"] = {"staged": 0, "unstaged": 0, "untracked": 0}
        return v

    @field_validator("git_diff")
    @classmethod
    def validate_git_diff(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Garante que git_diff tenha estrutura mínima."""
        if v is None:
            return {"files": [], "diffs": {}, "summary": {"added": 0, "modified": 0, "deleted": 0, "total": 0}}
        if "files" not in v:
            v["files"] = []
        if "diffs" not in v:
            v["diffs"] = {}
        if "summary" not in v:
            v["summary"] = {"added": 0, "modified": 0, "deleted": 0, "total": 0}
        return v


class FailedSnapshot(BaseModel):
    """
    Schema para snapshot FAILED com erro.

    Usado quando há falha em alguma etapa do processamento.
    """
    status: str = Field(..., pattern="^(COMPLETED|FAILED|PROCESSING)$")
    updated_at: str
    error: str | None = None
    error_type: str | None = None
    initial: dict[str, Any] | None = None

    @field_validator("initial")
    @classmethod
    def validate_initial(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Garante que initial tenha stats mínimo."""
        if v is None:
            return {"stats": {"files": 0, "lines": 0}}
        if "stats" not in v:
            v["stats"] = {"files": 0, "lines": 0}
        return v


def validate_snapshot_for_webui(snapshot: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    """
    Valida se o snapshot tem a estrutura mínima para o WebUI.

    Args:
        snapshot: Dicionário com dados do snapshot

    Returns:
        Tupla (válido, lista de erros críticos, lista de avisos)
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Campos obrigatórios
    if "status" not in snapshot:
        errors.append("Campo 'status' é obrigatório")
    elif snapshot["status"] not in ("COMPLETED", "FAILED", "PROCESSING"):
        errors.append(f"Status inválido: {snapshot.get('status')}")

    if "updated_at" not in snapshot:
        errors.append("Campo 'updated_at' é obrigatório")

    # Se for COMPLETED ou FAILED, valida estrutura completa
    status = snapshot.get("status")
    if status in ("COMPLETED", "FAILED"):
        # Valida initial (OBRIGATÓRIO para ambos)
        if "initial" not in snapshot:
            errors.append("Campo 'initial' é obrigatório para status COMPLETED/FAILED")
        else:
            initial = snapshot["initial"]
            if initial is None:
                errors.append("Campo 'initial' não pode ser nulo")
            elif not isinstance(initial, dict):
                errors.append("Campo 'initial' deve ser um dicionário")
            elif "stats" not in initial:
                errors.append("Campo 'initial.stats' é obrigatório")
            elif initial["stats"] is None:
                errors.append("Campo 'initial.stats' não pode ser nulo")

        # Para FAILED com erro, validation e git_diff são opcionais
        has_error = "error" in snapshot

        # Valida final (OBRIGATÓRIO para COMPLETED, opcional para FAILED)
        if status == "COMPLETED" and "final" not in snapshot:
            errors.append("Campo 'final' é obrigatório para status COMPLETED")

        # Valida validation (OBRIGATÓRIO para COMPLETED, opcional para FAILED)
        if status == "COMPLETED":
            if "validation" not in snapshot:
                errors.append("Campo 'validation' é obrigatório para status COMPLETED")
            else:
                validation = snapshot["validation"]
                if validation is None:
                    errors.append("Campo 'validation' não pode ser nulo")
                elif not isinstance(validation, dict):
                    errors.append("Campo 'validation' deve ser um dicionário")
        elif not has_error:
            # FAILED sem erro - avisa sobre ausência de validation
            if "validation" not in snapshot:
                warnings.append("Campo 'validation' ausente em snapshot FAILED sem erro")

        # Valida git_diff (OBRIGATÓRIO para COMPLETED, opcional para FAILED)
        if status == "COMPLETED":
            if "git_diff" not in snapshot:
                errors.append("Campo 'git_diff' é obrigatório para status COMPLETED")
            else:
                git_diff = snapshot["git_diff"]
                if git_diff is None:
                    errors.append("Campo 'git_diff' não pode ser nulo")
                elif not isinstance(git_diff, dict):
                    errors.append("Campo 'git_diff' deve ser um dicionário")
                elif "files" not in git_diff:
                    errors.append("Campo 'git_diff.files' é obrigatório")
                elif "summary" not in git_diff:
                    errors.append("Campo 'git_diff.summary' é obrigatório")
        elif not has_error:
            # FAILED sem erro - avisa sobre ausência de git_diff
            if "git_diff" not in snapshot:
                warnings.append("Campo 'git_diff' ausente em snapshot FAILED sem erro")

    # Se for FAILED com erro, valida estrutura de erro
    if "error" in snapshot and "error_type" not in snapshot:
        errors.append("Campo 'error_type' é obrigatório quando 'error' está presente")

    # Log de validação - registra erros e avisos
    if errors:
        logger.error(
            f"Validação de snapshot falhou | status={status} | errors={len(errors)}",
            extra={
                "status": status,
                "error_count": len(errors),
                "warning_count": len(warnings),
                "errors": errors,
                "warnings": warnings
            }
        )
    elif warnings:
        logger.warning(
            f"Validação de snapshot com avisos | status={status} | warnings={len(warnings)}",
            extra={
                "status": status,
                "warning_count": len(warnings),
                "warnings": warnings
            }
        )

    return len(errors) == 0, errors, warnings


def ensure_minimal_structure(snapshot: dict[str, Any]) -> dict[str, Any]:
    """
    Garante que o snapshot tenha a estrutura mínima para o WebUI.

    Preenche campos ausentes com valores padrão.

    Args:
        snapshot: Dicionário com dados do snapshot

    Returns:
        Snapshot com estrutura mínima garantida
    """
    result = snapshot.copy()
    added_fields: list[str] = []

    # Campos obrigatórios
    if "status" not in result:
        result["status"] = "UNKNOWN"
        added_fields.append("status")
    if "updated_at" not in result:
        from datetime import datetime
        result["updated_at"] = datetime.utcnow().isoformat()
        added_fields.append("updated_at")

    # Se for COMPLETED ou FAILED, garante estrutura mínima
    status = result.get("status")
    if status in ("COMPLETED", "FAILED"):
        # Garante initial
        if "initial" not in result or result["initial"] is None:
            result["initial"] = {"stats": {"files": 0, "lines": 0}}
            added_fields.append("initial")
        elif "stats" not in result["initial"] or result["initial"]["stats"] is None:
            result["initial"]["stats"] = {"files": 0, "lines": 0}
            added_fields.append("initial.stats")

        # Garante final (para COMPLETED)
        if status == "COMPLETED":
            if "final" not in result or result["final"] is None:
                result["final"] = {"stats": {"files": 0, "lines": 0}}
                added_fields.append("final")
            elif "stats" not in result["final"] or result["final"]["stats"] is None:
                result["final"]["stats"] = {"files": 0, "lines": 0}
                added_fields.append("final.stats")

        # Garante validation
        if "validation" not in result or result["validation"] is None:
            result["validation"] = {"status": {"staged": 0, "unstaged": 0, "untracked": 0}}
            added_fields.append("validation")
        elif "status" not in result["validation"] or result["validation"]["status"] is None:
            result["validation"]["status"] = {"staged": 0, "unstaged": 0, "untracked": 0}
            added_fields.append("validation.status")

        # Garante git_diff
        if "git_diff" not in result or result["git_diff"] is None:
            result["git_diff"] = {
                "files": [],
                "diffs": {},
                "summary": {"added": 0, "modified": 0, "deleted": 0, "total": 0}
            }
            added_fields.append("git_diff")
        else:
            if "files" not in result["git_diff"]:
                result["git_diff"]["files"] = []
                added_fields.append("git_diff.files")
            if "diffs" not in result["git_diff"]:
                result["git_diff"]["diffs"] = {}
                added_fields.append("git_diff.diffs")
            if "summary" not in result["git_diff"]:
                result["git_diff"]["summary"] = {"added": 0, "modified": 0, "deleted": 0, "total": 0}
                added_fields.append("git_diff.summary")

    # Log se campos foram adicionados
    if added_fields:
        logger.info(
            f"Estrutura mínima garantida | status={status} | campos_adicionados={len(added_fields)}",
            extra={
                "status": status,
                "added_fields": added_fields,
                "field_count": len(added_fields)
            }
        )

    return result
