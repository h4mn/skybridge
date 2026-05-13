# -*- coding: utf-8 -*-
"""
Testes do backup temporal mensal.

Spec: openspec/changes/sqlite-paper-persistence/specs/sqlite-migration/spec.md
"""

from datetime import datetime
from pathlib import Path

import pytest

from src.core.paper.adapters.persistence.sqlite_paper_state import SQLitePaperState


class TestBackupMensal:
    def test_backup_criado_na_primeira_execucao_do_mes(self, tmp_path):
        """Scenario: Backup mensal criado quando não existe."""
        db_path = tmp_path / "paper_state.db"
        state = SQLitePaperState(str(db_path))
        state.save_order({
            "created_at": "2026-01-01T00:00:00", "id": "ord-1",
            "ticker": "BTC-USD", "side": "buy", "quantity": 1,
            "price": "50000", "total_value": "50000", "status": "EXECUTADA",
            "order_type": "open", "broker": "paper", "strategy_name": "guardiao",
        })
        state.create_backup(tmp_path / "backups")

        now = datetime.now()
        expected = tmp_path / "backups" / f"paper_state-{now.strftime('%Y-%m')}.db"
        assert expected.exists()

    def test_backup_nao_duplica_no_mesmo_mes(self, tmp_path):
        """Scenario: Backup não duplica no mesmo mês."""
        db_path = tmp_path / "paper_state.db"
        state = SQLitePaperState(str(db_path))

        backup_dir = tmp_path / "backups"
        state.create_backup(backup_dir)
        state.create_backup(backup_dir)

        backups = list(backup_dir.glob("*.db"))
        assert len(backups) == 1
