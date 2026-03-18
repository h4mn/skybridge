# -*- coding: utf-8 -*-
"""
Testes para SQLiteJobQueue.from_context().

TDD Estrito: Testes que documentam o comportamento esperado do from_context.

DOC: ADR024 - JobQueue usa workspace do contexto.
DOC: ADR024 - Sem workspace, usa core por padrão.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from infra.webhooks.adapters.sqlite_job_queue import SQLiteJobQueue
from runtime.workspace.workspace_context import set_workspace


class TestSQLiteJobQueueFromContext:
    """Testa from_context() - criação baseada no workspace."""

    def test_job_queue_uses_workspace_from_context(self, tmp_path):
        """
        DOC: ADR024 - JobQueue usa workspace do contexto.

        O método from_context() deve criar JobQueue com caminho
        baseado no workspace do request.state.
        """
        # Criar request mock com workspace definido
        request = MagicMock()
        set_workspace(request, "trading")

        queue = SQLiteJobQueue.from_context(request, base_path=tmp_path)

        # Banco deve estar em workspace/trading/data/jobs.db
        assert queue._db_path == tmp_path / "workspace" / "trading" / "data" / "jobs.db"

    def test_job_queue_falls_back_to_core(self, tmp_path):
        """
        DOC: ADR024 - Sem workspace, usa core por padrão.

        Se request.state.workspace não estiver definido,
        from_context() deve usar 'core' como padrão.
        """
        # Criar request sem workspace definido
        class MockRequestWithoutWorkspace:
            class State:
                pass
            state = State()

        request = MockRequestWithoutWorkspace()

        queue = SQLiteJobQueue.from_context(request, base_path=tmp_path)

        assert queue._db_path == tmp_path / "workspace" / "core" / "data" / "jobs.db"

    def test_job_queue_creates_parent_directories(self, tmp_path):
        """
        DOC: from_context() deve criar diretórios pai se não existirem.

        O caminho completo workspace/<id>/data/ deve ser criado.
        """
        request = MagicMock()
        set_workspace(request, "futura")

        # O diretório não existe ainda
        data_dir = tmp_path / "workspace" / "futura" / "data"
        assert not data_dir.exists()

        queue = SQLiteJobQueue.from_context(request, base_path=tmp_path)

        # Após criar, o diretório deve existir
        assert data_dir.exists()
        assert queue._db_path.parent == data_dir


class TestSQLiteJobQueueWorkspaceIsolation:
    """Testa isolamento entre workspaces."""

    def test_job_queue_different_workspace_different_db(self, tmp_path):
        """
        DOC: ADR024 - Cada workspace tem seu próprio jobs.db.

        Workspaces diferentes devem usar bancos diferentes.
        """
        request_core = MagicMock()
        set_workspace(request_core, "core")

        request_trading = MagicMock()
        set_workspace(request_trading, "trading")

        queue_core = SQLiteJobQueue.from_context(request_core, base_path=tmp_path)
        queue_trading = SQLiteJobQueue.from_context(request_trading, base_path=tmp_path)

        # Caminhos devem ser diferentes
        assert queue_core._db_path != queue_trading._db_path
        assert "core" in str(queue_core._db_path)
        assert "trading" in str(queue_trading._db_path)

    @pytest.mark.asyncio
    async def test_job_queue_core_jobs_not_in_trading(self, tmp_path):
        """
        DOC: ADR024 - Jobs de core não aparecem em trading.

        Jobs adicionados em um workspace não devem aparecer em outro.
        """
        from core.webhooks.domain import WebhookJob, WebhookEvent, WebhookSource
        from datetime import datetime

        # Criar filas para workspaces diferentes
        request_core = MagicMock()
        set_workspace(request_core, "core")
        queue_core = SQLiteJobQueue.from_context(request_core, base_path=tmp_path)

        request_trading = MagicMock()
        set_workspace(request_trading, "trading")
        queue_trading = SQLiteJobQueue.from_context(request_trading, base_path=tmp_path)

        # Adicionar job no core
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="push",
            event_id="123",
            payload={},
            received_at=datetime.utcnow()
        )
        job = WebhookJob(
            job_id="test-job",
            correlation_id="test-corr",
            created_at=datetime.utcnow(),
            status="pending",
            event=event,
            issue_number=None,
            metadata={}
        )

        await queue_core.enqueue(job)

        # Core deve ter o job
        assert await queue_core.get_job("test-job") is not None

        # Trading NÃO deve ter o job
        assert await queue_trading.get_job("test-job") is None
