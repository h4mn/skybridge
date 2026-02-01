# -*- coding: utf-8 -*-
"""
Testes de integração para validar snapshots reais do sistema.

Garante que os snapshots produzidos pelo job_orchestrator têm a estrutura
correta para exibição no WebUI.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from runtime.observability.snapshot.schemas import (
    validate_snapshot_for_webui,
    ensure_minimal_structure,
)


class TestRealWorldSnapshots:
    """Testa snapshots reais produzidos pelo sistema."""

    def test_validate_snapshot_structure_from_job_orchestrator(self):
        """
        Testa a estrutura de snapshot produzida pelo job_orchestrator.

        Este é o formato exato que o job_orchestrator produz quando
        salva snapshots COMPLETED.
        """
        # Simula snapshot criado pelo job_orchestrator.py:475-485
        snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {
                "metadata": {
                    "snapshot_id": "test_initial_123",
                    "timestamp": "2026-01-25T19:59:00",
                    "subject": "git",
                    "target": "/path/to/worktree",
                    "git_hash": "abc123",
                    "git_branch": "feature/test"
                },
                "stats": {
                    "files": 100,
                    "lines": 5000,
                    "total_files": 100,
                    "total_dirs": 20
                },
                "structure": {
                    "name": "git_status",
                    "type": "git",
                    "status": {
                        "is_clean": False,
                        "has_staged": True,
                        "staged_files": ["test.py"]
                    }
                }
            },
            "final": {
                "metadata": {
                    "snapshot_id": "test_final_456",
                    "timestamp": "2026-01-25T20:00:00",
                    "subject": "git",
                    "target": "/path/to/worktree",
                    "git_hash": "def456",
                    "git_branch": "feature/test"
                },
                "stats": {
                    "files": 102,
                    "lines": 5150,
                    "total_files": 102,
                    "total_dirs": 21
                },
                "structure": {
                    "name": "git_status",
                    "type": "git",
                    "status": {
                        "is_clean": False,
                        "has_staged": True,
                        "staged_files": ["test.py", "new.py"]
                    }
                }
            },
            "validation": {
                "validated": True,
                "can_remove": True,
                "message": "Worktree válido",
                "status": {
                    "staged": 2,
                    "unstaged": 1,
                    "untracked": 0
                }
            },
            "git_diff": {
                "files": [
                    {"path": "test.py", "status": "M"},
                    {"path": "new.py", "status": "A"},
                    {"path": "old.py", "status": "D"}
                ],
                "diffs": {
                    "test.py": "--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,2 @@\n old\n+new",
                    "new.py": "--- ARQUIVO NOVO ---\n# New file\n"
                },
                "summary": {
                    "added": 1,
                    "modified": 1,
                    "deleted": 1,
                    "total": 3
                }
            }
        }

        # Valida a estrutura
        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        assert valid, f"Snapshot do job_orchestrator deve ser válido: {errors}"
        assert len(errors) == 0
        assert len(warnings) == 0

    def test_failed_snapshot_from_job_orchestrator(self):
        """
        Testa snapshot de erro produzido pelo job_orchestrator.

        Este é o formato que o job_orchestrator produz quando há erro
        na execução do agente (linha 373-382).
        """
        # Simula snapshot FAILED criado pelo job_orchestrator.py:373-382
        snapshot = {
            "status": "FAILED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {
                "metadata": {
                    "snapshot_id": "test_initial",
                    "timestamp": "2026-01-25T19:59:00",
                    "subject": "git",
                    "target": "/path/to/worktree"
                },
                "stats": {
                    "files": 100,
                    "lines": 5000,
                    "total_files": 100
                },
                "structure": {}
            },
            "error": "Erro ao executar agente",
            "error_type": "AgentError"
        }

        # Valida a estrutura
        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        assert valid, f"Snapshot FAILED deve ser válido: {errors}"
        assert len(errors) == 0

    def test_processing_snapshot_from_job_orchestrator(self):
        """
        Testa snapshot PROCESSING produzido pelo job_orchestrator.

        Este é o formato quando o worktree foi criado e o snapshot
        inicial foi capturado (linha 323-332).
        """
        # Simula snapshot PROCESSING criado pelo job_orchestrator.py:323-332
        snapshot = {
            "status": "PROCESSING",
            "updated_at": "2026-01-25T20:00:00",
            "metadata": {
                "snapshot_id": "test_initial",
                "timestamp": "2026-01-25T19:59:00",
                "subject": "git",
                "target": "/path/to/worktree"
            },
            "stats": {
                "files": 100,
                "lines": 5000
            },
            "structure": {}
        }

        # PROCESSING não precisa de initial/final/validation/git_diff ainda
        # (estes serão adicionados quando o job completar)
        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        # PROCESSING com apenas status e updated_at é válido
        assert len([e for e in errors if "initial" in e.lower()]) == 0

    def test_minimal_fields_required_by_frontend(self):
        """
        Testa os campos mínimos que o frontend Worktrees.tsx espera.

        Baseado na análise do código do frontend:
        - getSnapshotDiff(): precisa de initial.stats e final.stats
        - getGitDiffData(): precisa de git_diff.files, git_diff.diffs, git_diff.summary
        - getStatusBadge(): precisa de status
        """
        # Snapshot mínimo para o frontend funcionar sem erros
        minimal_snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {
                "stats": {
                    "files": 100,
                    "lines": 5000
                }
            },
            "final": {
                "stats": {
                    "files": 102,
                    "lines": 5150
                }
            },
            "validation": {
                "status": {
                    "staged": 2,
                    "unstaged": 0,
                    "untracked": 0
                }
            },
            "git_diff": {
                "files": [],
                "diffs": {},
                "summary": {
                    "added": 0,
                    "modified": 0,
                    "deleted": 0,
                    "total": 0
                }
            }
        }

        valid, errors, warnings = validate_snapshot_for_webui(minimal_snapshot)
        assert valid, f"Snapshot mínimo deve ser válido: {errors}"

    def test_ensure_minimal_structure_fixes_incomplete_snapshots(self):
        """
        Testa que ensure_minimal_structure() torna snapshots incompletos
        em válidos para o frontend.
        """
        # Snapshot incompleto (faltando campos)
        incomplete = {
            "status": "COMPLETED",
            "initial": {
                "metadata": {"snapshot_id": "test"},
                "structure": {}
                # Faltando stats!
            },
            # Faltando final, validation, git_diff
        }

        # Aplica a função
        completed = ensure_minimal_structure(incomplete)

        # Verifica que os campos foram adicionados
        assert "updated_at" in completed
        assert "stats" in completed["initial"]
        assert "validation" in completed
        assert "git_diff" in completed

        # Agora deve ser válido
        valid, errors, warnings = validate_snapshot_for_webui(completed)
        assert valid, f"Snapshot completado deve ser válido: {errors}"


class TestSnapshotFileReading:
    """Testa leitura de arquivos de snapshot reais do disco."""

    @pytest.mark.skipif(
        not Path("B:\\_repositorios\\skybridge-auto\\skybridge-github-42-e733937c\\.sky\\snapshot.json").exists(),
        reason="Arquivo de snapshot de teste não encontrado"
    )
    def test_real_snapshot_file_is_valid(self):
        """
        Testa que o snapshot real criado para testes é válido.

        Este teste usa o arquivo criado manualmente para validação
        do WebUI.
        """
        snapshot_path = Path("B:\\_repositorios\\skybridge-auto\\skybridge-github-42-e733937c\\.sky\\snapshot.json")

        # Lê o snapshot do disco
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

        # Valida a estrutura
        valid, errors, warnings = validate_snapshot_for_webui(snapshot)
        assert valid, f"Snapshot real deve ser válido: {errors}"

        # Verifica campos específicos que o frontend espera
        assert "status" in snapshot
        assert "updated_at" in snapshot
        assert "initial" in snapshot
        assert "git_diff" in snapshot

        # Verifica estrutura de git_diff
        git_diff = snapshot["git_diff"]
        assert "files" in git_diff
        assert "diffs" in git_diff
        assert "summary" in git_diff

        # Verifica que há pelo menos um arquivo
        assert len(git_diff["files"]) > 0

        # Verifica estrutura dos arquivos
        for file in git_diff["files"]:
            assert "path" in file
            assert "status" in file


class TestWebUICompatibility:
    """Testa compatibilidade específica com o código do frontend."""

    def test_frontend_diff_calculation(self):
        """
        Testa que o snapshot tem os dados necessários para
        getSnapshotDiff() do Worktrees.tsx.
        """
        snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {
                "stats": {"files": 100, "lines": 5000}
            },
            "final": {
                "stats": {"files": 102, "lines": 5150}
            },
            "validation": {
                "status": {"staged": 2, "unstaged": 1, "untracked": 0}
            },
            "git_diff": {
                "files": [],
                "diffs": {},
                "summary": {"added": 1, "modified": 2, "deleted": 0, "total": 3}
            }
        }

        # Simula getSnapshotDiff() do frontend
        initial = snapshot["initial"]
        final = snapshot["final"]
        validation = snapshot["validation"]

        # Verifica que os campos existem
        assert "stats" in initial
        assert "files" in initial["stats"]
        assert "lines" in initial["stats"]

        assert "stats" in final
        assert "files" in final["stats"]
        assert "lines" in final["stats"]

        assert "status" in validation
        assert "staged" in validation["status"]
        assert "unstaged" in validation["status"]
        assert "untracked" in validation["status"]

        # Simula o cálculo de diff
        files_diff = final["stats"]["files"] - initial["stats"]["files"]
        lines_diff = final["stats"]["lines"] - initial["stats"]["lines"]

        assert files_diff == 2
        assert lines_diff == 150

    def test_frontend_git_diff_data(self):
        """
        Testa que o snapshot tem os dados necessários para
        getGitDiffData() do Worktrees.tsx.
        """
        snapshot = {
            "status": "COMPLETED",
            "updated_at": "2026-01-25T20:00:00",
            "initial": {"stats": {"files": 0, "lines": 0}},
            "git_diff": {
                "files": [
                    {"path": "src/test.py", "status": "M"},
                    {"path": "src/new.py", "status": "A"}
                ],
                "diffs": {
                    "src/test.py": "--- a/src/test.py\n+++ b/src/test.py"
                },
                "summary": {
                    "added": 1,
                    "modified": 1,
                    "deleted": 0,
                    "total": 2
                }
            }
        }

        # Simula getGitDiffData() do frontend
        git_diff = snapshot["git_diff"]

        # Verifica estrutura
        assert "files" in git_diff
        assert "diffs" in git_diff
        assert "summary" in git_diff

        # Verifica que files é uma lista
        assert isinstance(git_diff["files"], list)

        # Verifica estrutura de cada arquivo
        for file in git_diff["files"]:
            assert "path" in file
            assert "status" in file

        # Verifica estrutura de summary
        summary = git_diff["summary"]
        assert "added" in summary
        assert "modified" in summary
        assert "deleted" in summary
