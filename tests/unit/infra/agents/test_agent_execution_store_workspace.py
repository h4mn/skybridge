# -*- coding: utf-8 -*-
"""
Testes para AgentExecutionStore.from_context().

TDD Estrito: Testes que documentam o comportamento esperado do from_context.

DOC: ADR024 - executions.db é por workspace.
DOC: ADR024 - Sem workspace, usa core por padrão.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from infra.agents.agent_execution_store import AgentExecutionStore
from runtime.workspace.workspace_context import set_workspace


class TestAgentExecutionStoreFromContext:
    """Testa from_context() - criação baseada no workspace."""

    def test_execution_store_uses_workspace_from_context(self, tmp_path):
        """
        DOC: ADR024 - executions.db é por workspace.

        O método from_context() deve criar store com caminho
        baseado no workspace do request.state.
        """
        request = MagicMock()
        set_workspace(request, "trading")

        store = AgentExecutionStore.from_context(request, base_path=tmp_path)

        # Banco deve estar em workspace/trading/data/agent_executions.db
        assert store._db_path == tmp_path / "workspace" / "trading" / "data" / "agent_executions.db"

    def test_execution_store_falls_back_to_core(self, tmp_path):
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

        store = AgentExecutionStore.from_context(request, base_path=tmp_path)

        assert store._db_path == tmp_path / "workspace" / "core" / "data" / "agent_executions.db"


class TestAgentExecutionStoreWorkspaceIsolation:
    """Testa isolamento entre workspaces."""

    def test_execution_store_different_workspace_different_db(self, tmp_path):
        """
        DOC: ADR024 - Cada workspace tem seu próprio executions.db.

        Workspaces diferentes devem usar bancos diferentes.
        """
        request_core = MagicMock()
        set_workspace(request_core, "core")

        request_trading = MagicMock()
        set_workspace(request_trading, "trading")

        store_core = AgentExecutionStore.from_context(request_core, base_path=tmp_path)
        store_trading = AgentExecutionStore.from_context(request_trading, base_path=tmp_path)

        # Caminhos devem ser diferentes
        assert store_core._db_path != store_trading._db_path
        assert "core" in str(store_core._db_path)
        assert "trading" in str(store_trading._db_path)
