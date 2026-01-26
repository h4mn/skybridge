# -*- coding: utf-8 -*-
"""
Testes para validação de schemas de snapshot.

Garante que os snapshots tenham a estrutura mínima necessária
para exibição correta no WebUI (Worktrees.tsx).
"""
from __future__ import annotations

import pytest

from runtime.observability.snapshot.schemas import (
    CompletedSnapshot,
    FailedSnapshot,
    validate_snapshot_for_webui,
    ensure_minimal_structure,
    SnapshotStats,
    GitDiffData,
    ValidationData,
)


def _is_valid(valid: tuple[bool, list[str], list[str]]) -> bool:
    """Helper para extrair apenas o status válido da tupla."""
    return valid[0]


class TestValidateSnapshotForWebui:
    """Testa validação de snapshots para o WebUI."""

    def test_completed_snapshot_valid(self):
        """Snapshot COMPLETED completo deve ser válido."""
        snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {
                "stats": {"files": 100, "lines": 5000},
                "metadata": {"snapshot_id": "test123"},
                "structure": {}
            },
            "final": {
                "stats": {"files": 102, "lines": 5150},
                "metadata": {"snapshot_id": "test456"},
                "structure": {}
            },
            "validation": {
                "status": {"staged": 2, "unstaged": 0, "untracked": 0}
            },
            "git_diff": {
                "files": [{"path": "test.py", "status": "M"}],
                "diffs": {"test.py": "--- a/test.py\n+++ b/test.py"},
                "summary": {"added": 1, "modified": 2, "deleted": 0, "total": 3}
            }
        }

        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        assert valid, f"Snapshot deveria ser válido, erros: {errors}"
        assert len(errors) == 0
        assert len(warnings) == 0

    def test_completed_snapshot_missing_status(self):
        """Snapshot sem campo 'status' deve ser inválido."""
        snapshot = {
            "updated_at": "2026-01-25T20:00:00",
            "initial": {"stats": {"files": 100, "lines": 5000}},
        }

        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        assert not valid
        assert any("status" in e.lower() for e in errors)

    def test_completed_snapshot_missing_initial(self):
        """Snapshot COMPLETED sem campo 'initial' deve ser inválido."""
        snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
        }

        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        assert not valid
        assert any("initial" in e.lower() for e in errors)

    def test_completed_snapshot_missing_validation(self):
        """Snapshot sem campo 'validation' deve gerar aviso."""
        snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {"stats": {"files": 100, "lines": 5000}},
        }

        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        # Pode ser válido mas com aviso
        assert any("validation" in e.lower() for e in errors)

    def test_failed_snapshot_with_error(self):
        """Snapshot FAILED com erro deve ser válido."""
        snapshot = {
            "status": "FAILED",
            "updated_at": "2026-01-25T20:00:00",
            "error": "Erro ao executar agente",
            "error_type": "AgentError",
            "initial": {"stats": {"files": 100, "lines": 5000}},
        }

        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        assert valid, f"Snapshot FAILED deveria ser válido, erros: {errors}"

    def test_failed_snapshot_error_without_type(self):
        """Snapshot com erro mas sem error_type deve ser inválido."""
        snapshot = {
            "status": "FAILED",
            "updated_at": "2026-01-25T20:00:00",
            "error": "Erro ao executar agente",
            "initial": {"stats": {"files": 100, "lines": 5000}},
        }

        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        assert not valid
        assert any("error_type" in e.lower() for e in errors)

    def test_invalid_status(self):
        """Snapshot com status inválido deve falhar."""
        snapshot = {
            "status": "INVALID_STATUS",
            "updated_at": "2026-01-25T20:00:00",
        }

        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        assert not valid
        assert any("status" in e.lower() and "inválido" in e.lower() for e in errors)


class TestEnsureMinimalStructure:
    """Testa garantia de estrutura mínima."""

    def test_ensure_adds_missing_status(self):
        """Deve adicionar status se faltar."""
        snapshot = {"updated_at": "2026-01-25T20:00:00"}
        result = ensure_minimal_structure(snapshot)

        assert "status" in result
        assert result["status"] == "UNKNOWN"

    def test_ensure_adds_missing_updated_at(self):
        """Deve adicionar updated_at se faltar."""
        snapshot = {"status": "COMPLETED"}
        result = ensure_minimal_structure(snapshot)

        assert "updated_at" in result
        assert result["updated_at"] is not None

    def test_ensure_adds_missing_initial_stats(self):
        """Deve adicionar initial.stats se faltar."""
        snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {}
        }
        result = ensure_minimal_structure(snapshot)

        assert "initial" in result
        assert "stats" in result["initial"]
        assert result["initial"]["stats"] == {"files": 0, "lines": 0}

    def test_ensure_adds_missing_validation(self):
        """Deve adicionar validation se faltar."""
        snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {"stats": {"files": 100, "lines": 5000}},
        }
        result = ensure_minimal_structure(snapshot)

        assert "validation" in result
        assert "status" in result["validation"]
        assert result["validation"]["status"] == {"staged": 0, "unstaged": 0, "untracked": 0}

    def test_ensure_adds_missing_git_diff(self):
        """Deve adicionar git_diff se faltar."""
        snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {"stats": {"files": 100, "lines": 5000}},
        }
        result = ensure_minimal_structure(snapshot)

        assert "git_diff" in result
        assert "files" in result["git_diff"]
        assert "diffs" in result["git_diff"]
        assert "summary" in result["git_diff"]

    def test_ensure_preserves_existing_fields(self):
        """Deve preservar campos existentes."""
        snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {"stats": {"files": 100, "lines": 5000}},
            "validation": {"status": {"staged": 5, "unstaged": 2, "untracked": 1}},
            "custom_field": "preservado"
        }
        result = ensure_minimal_structure(snapshot)

        assert result["initial"]["stats"]["files"] == 100
        assert result["validation"]["status"]["staged"] == 5
        assert result["custom_field"] == "preservado"


class TestCompletedSnapshotModel:
    """Testa modelo Pydantic para snapshot COMPLETED."""

    def test_valid_completed_snapshot(self):
        """Snapshot COMPLETED válido deve passar."""
        data = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {"stats": {"files": 100, "lines": 5000}},
            "final": {"stats": {"files": 102, "lines": 5150}},
            "validation": {"status": {"staged": 2, "unstaged": 0, "untracked": 0}},
            "git_diff": {
                "files": [{"path": "test.py", "status": "M"}],
                "diffs": {},
                "summary": {"added": 1, "modified": 2, "deleted": 0, "total": 3}
            }
        }

        snapshot = CompletedSnapshot(**data)
        assert snapshot.status == "COMPLETED"
        assert snapshot.initial is not None
        assert snapshot.validation is not None
        assert snapshot.git_diff is not None

    def test_completed_snapshot_with_null_fields(self):
        """Snapshot COMPLETED com campos nulos deve preencher defaults."""
        data = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": None,
            "validation": None,
            "git_diff": None
        }

        snapshot = CompletedSnapshot(**data)
        assert snapshot.initial is not None
        assert snapshot.initial["stats"]["files"] == 0
        assert snapshot.validation is not None
        assert snapshot.validation["status"]["staged"] == 0
        assert snapshot.git_diff is not None
        assert snapshot.git_diff["files"] == []

    def test_invalid_status_rejected(self):
        """Status inválido deve ser rejeitado."""
        data = {
            "status": "INVALID",
            "updated_at": "2026-01-25T20:00:00",
        }

        with pytest.raises(Exception):
            CompletedSnapshot(**data)


class TestFailedSnapshotModel:
    """Testa modelo Pydantic para snapshot FAILED."""

    def test_valid_failed_snapshot(self):
        """Snapshot FAILED válido deve passar."""
        data = {
            "status": "FAILED",
            "updated_at": "2026-01-25T20:00:00",
            "error": "Erro ao executar",
            "error_type": "AgentError",
            "initial": {"stats": {"files": 100, "lines": 5000}},
        }

        snapshot = FailedSnapshot(**data)
        assert snapshot.status == "FAILED"
        assert snapshot.error == "Erro ao executar"
        assert snapshot.error_type == "AgentError"

    def test_failed_snapshot_without_initial(self):
        """Snapshot FAILED sem initial deve preencher default."""
        data = {
            "status": "FAILED",
            "updated_at": "2026-01-25T20:00:00",
            "error": "Erro",
            "error_type": "WorktreeError",
            "initial": None
        }

        snapshot = FailedSnapshot(**data)
        assert snapshot.initial is not None
        assert snapshot.initial["stats"]["files"] == 0


class TestGitDiffData:
    """Testa modelo de dados de diff do git."""

    def test_valid_git_diff(self):
        """Git diff válido deve passar."""
        data = {
            "files": [{"path": "test.py", "status": "M"}],
            "diffs": {"test.py": "--- a/test.py\n+++ b/test.py"},
            "summary": {"added": 1, "modified": 2, "deleted": 0, "total": 3}
        }

        git_diff = GitDiffData(**data)
        assert len(git_diff.files) == 1
        assert git_diff.summary["added"] == 1

    def test_git_diff_with_empty_summary(self):
        """Summary vazio deve preencher defaults."""
        data = {
            "files": [],
            "diffs": {},
            "summary": {}
        }

        git_diff = GitDiffData(**data)
        assert git_diff.summary["added"] == 0
        assert git_diff.summary["modified"] == 0
        assert git_diff.summary["deleted"] == 0
        assert git_diff.summary["total"] == 0

    def test_git_diff_with_null_summary(self):
        """Summary None deve preencher defaults."""
        data = {
            "files": [],
            "diffs": {},
            "summary": None
        }

        git_diff = GitDiffData(**data)
        assert git_diff.summary["added"] == 0


class TestValidationData:
    """Testa modelo de dados de validação."""

    def test_valid_validation(self):
        """Validação válida deve passar."""
        data = {
            "status": {"staged": 2, "unstaged": 1, "untracked": 0},
            "validated": True,
            "can_remove": True,
            "message": "Worktree válido"
        }

        validation = ValidationData(**data)
        assert validation.status["staged"] == 2
        assert validation.validated is True

    def test_validation_with_null_status(self):
        """Status None deve preencher defaults."""
        data = {
            "status": None,
            "validated": True,
        }

        validation = ValidationData(**data)
        assert validation.status is not None
        assert validation.status["staged"] == 0


class TestSnapshotStats:
    """Testa modelo de estatísticas do snapshot."""

    def test_valid_stats(self):
        """Stats válidos devem passar."""
        data = {
            "files": 100,
            "lines": 5000,
            "total_files": 100,
            "total_dirs": 20
        }

        stats = SnapshotStats(**data)
        assert stats.files == 100
        assert stats.lines == 5000

    def test_stats_with_null_fields(self):
        """Stats com campos nulos devem ser válidos."""
        data = {
            "files": None,
            "lines": None,
            "total_files": None,
            "total_dirs": None
        }

        stats = SnapshotStats(**data)
        assert stats.files is None
        assert stats.lines is None


class TestIntegrationWithWebUI:
    """Testes de integração com estrutura esperada pelo Worktrees.tsx."""

    def test_frontend_expected_structure(self):
        """
        Testa que o snapshot tem exatamente a estrutura esperada pelo frontend.

        Baseado no código do Worktrees.tsx:
        - initial.stats.files, initial.stats.lines
        - final.stats.files, final.stats.lines
        - validation.status.staged, validation.status.unstaged, validation.status.untracked
        - git_diff.files[].path, git_diff.files[].status
        - git_diff.diffs[path]
        - git_diff.summary.added, git_diff.summary.modified, git_diff.summary.deleted
        """
        snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {
                "stats": {"files": 100, "lines": 5000},
                "metadata": {"snapshot_id": "initial123"},
                "structure": {"name": "git", "type": "git"}
            },
            "final": {
                "stats": {"files": 102, "lines": 5150},
                "metadata": {"snapshot_id": "final456"},
                "structure": {"name": "git", "type": "git"}
            },
            "validation": {
                "status": {"staged": 2, "unstaged": 1, "untracked": 0},
                "validated": True,
                "can_remove": True
            },
            "git_diff": {
                "files": [
                    {"path": "src/test.py", "status": "M"},
                    {"path": "src/new.py", "status": "A"},
                    {"path": "old.py", "status": "D"}
                ],
                "diffs": {
                    "src/test.py": "--- a/src/test.py\n+++ b/src/test.py\n@@ -1,1 +1,2 @@\n old\n+new",
                    "src/new.py": "--- ARQUIVO NOVO ---\n# New file"
                },
                "summary": {
                    "added": 1,
                    "modified": 1,
                    "deleted": 1,
                    "total": 3
                }
            }
        }

        # Valida via função de validação
        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        assert valid, f"Snapshot deveria ser válido para o WebUI, erros: {errors}"

        # Valida via Pydantic
        completed = CompletedSnapshot(**snapshot)
        assert completed.status == "COMPLETED"

        # Verifica estrutura específica que o frontend espera
        assert "initial" in snapshot
        assert "stats" in snapshot["initial"]
        assert "files" in snapshot["initial"]["stats"]
        assert "lines" in snapshot["initial"]["stats"]

        assert "validation" in snapshot
        assert "status" in snapshot["validation"]
        assert "staged" in snapshot["validation"]["status"]
        assert "unstaged" in snapshot["validation"]["status"]
        assert "untracked" in snapshot["validation"]["status"]

        assert "git_diff" in snapshot
        assert "files" in snapshot["git_diff"]
        assert "diffs" in snapshot["git_diff"]
        assert "summary" in snapshot["git_diff"]

        # Verifica estrutura de arquivos
        for file in snapshot["git_diff"]["files"]:
            assert "path" in file
            assert "status" in file

        # Verifica estrutura de summary
        summary = snapshot["git_diff"]["summary"]
        assert "added" in summary
        assert "modified" in summary
        assert "deleted" in summary

    def test_failed_snapshot_for_frontend(self):
        """
        Testa que snapshot FAILED também funciona no frontend.

        O frontend precisa lidar com snapshots de erro que têm:
        - error, error_type
        - initial (pode ter stats mínimos)
        - Sem final, validation, git_diff
        """
        snapshot = {
            "status": "FAILED",
            "updated_at": "2026-01-25T20:00:00",
            "error": "Erro ao criar worktree",
            "error_type": "WorktreeError",
            "initial": {"stats": {"files": 0, "lines": 0}}
        }

        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        assert valid, f"Snapshot FAILED deveria ser válido, erros: {errors}"

        failed = FailedSnapshot(**snapshot)
        assert failed.error == "Erro ao criar worktree"
