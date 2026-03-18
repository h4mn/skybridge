# -*- coding: utf-8 -*-
"""
Testes de integração para WorkspaceRepository.

TDD Estrito: Testes que documentam o comportamento esperado do repositório.

DOC: ADR024 - data/workspaces.db persiste metadados de workspaces.
DOC: PB013 - Workspaces podem ser criados, listados e deletados.

Estes são testes de integração porque usam SQLite real.
"""
import pytest
from pathlib import Path
import tempfile

from runtime.config.workspace_repository import WorkspaceRepository, Workspace


@pytest.fixture
def temp_db(tmp_path):
    """
    Fixture: Banco temporário para testes.

    Cria um novo banco SQLite para cada teste.
    """
    db_path = tmp_path / "workspaces.db"
    return WorkspaceRepository.create(db_path)


class TestWorkspaceRepositoryInit:
    """Testa inicialização do repositório."""

    def test_repository_creates_table_on_init(self, temp_db):
        """
        DOC: ADR024 - data/workspaces.db tem tabela workspaces.

        Ao criar o repositório, a tabela workspaces deve ser criada.
        """
        # Tabela deve existir após create()
        rows = temp_db.list_all()
        assert isinstance(rows, list)
        # Inicialmente vazia
        assert len(rows) == 0


class TestWorkspaceRepositoryCRUD:
    """Testa operações CRUD do repositório."""

    def test_repository_save_and_retrieve_workspace(self, temp_db):
        """
        DOC: ADR024 - Workspace pode ser salvo e recuperado.

        O método save() deve persistir o workspace no banco.
        O método get() deve recuperar o workspace por ID.
        """
        workspace = Workspace(
            id="trading",
            name="Trading Bot",
            path="workspace/trading",
            description="Bot de trading",
            auto=False,
            enabled=True
        )

        temp_db.save(workspace)
        retrieved = temp_db.get("trading")

        assert retrieved is not None
        assert retrieved.id == "trading"
        assert retrieved.name == "Trading Bot"
        assert retrieved.path == "workspace/trading"
        assert retrieved.description == "Bot de trading"
        assert retrieved.auto is False
        assert retrieved.enabled is True

    def test_repository_save_updates_existing_workspace(self, temp_db):
        """
        DOC: PB013 - save() atualiza workspace se já existe.

        Se salvar um workspace com ID existente, deve atualizar.
        """
        # Criar workspace inicial
        workspace = Workspace(
            id="trading",
            name="Trading Bot",
            path="workspace/trading",
            description="Bot de trading",
            auto=False,
            enabled=True
        )
        temp_db.save(workspace)

        # Atualizar
        updated = Workspace(
            id="trading",
            name="Trading Bot v2",
            path="workspace/trading",
            description="Bot de trading atualizado",
            auto=True,
            enabled=False
        )
        temp_db.save(updated)

        # Verificar atualização
        retrieved = temp_db.get("trading")
        assert retrieved.name == "Trading Bot v2"
        assert retrieved.description == "Bot de trading atualizado"
        assert retrieved.auto is True
        assert retrieved.enabled is False

    def test_repository_workspace_not_found_returns_none(self, temp_db):
        """
        DOC: Workspace inexistente retorna None.

        O método get() deve retornar None se o workspace não existir.
        """
        assert temp_db.get("nonexistent") is None

    def test_repository_list_all_workspaces(self, temp_db):
        """
        DOC: ADR024 - Pode listar todos os workspaces cadastrados.

        O método list_all() deve retornar todos os workspaces.
        """
        ws1 = Workspace(
            id="core",
            name="Core",
            path="workspace/core",
            description="Instancia principal",
            auto=True,
            enabled=True
        )
        ws2 = Workspace(
            id="trading",
            name="Trading",
            path="workspace/trading",
            description="Bot de trading",
            auto=False,
            enabled=True
        )

        temp_db.save(ws1)
        temp_db.save(ws2)

        all_ws = temp_db.list_all()
        assert len(all_ws) == 2
        assert any(ws.id == "core" for ws in all_ws)
        assert any(ws.id == "trading" for ws in all_ws)

    def test_repository_list_empty_when_no_workspaces(self, temp_db):
        """
        DOC: list_all() retorna lista vazia quando não há workspaces.

        """
        all_ws = temp_db.list_all()
        assert len(all_ws) == 0
        assert all_ws == []

    def test_repository_delete_workspace(self, temp_db):
        """
        DOC: PB013 - Workspace pode ser deletado.

        O método delete() deve remover o workspace do banco.
        """
        workspace = Workspace(
            id="temp",
            name="Temp",
            path="workspace/temp",
            description="Temporario",
            auto=False,
            enabled=True
        )
        temp_db.save(workspace)

        # Verificar que existe
        assert temp_db.get("temp") is not None

        # Deletar
        temp_db.delete("temp")

        # Verificar que não existe mais
        assert temp_db.get("temp") is None

    def test_repository_delete_nonexistent_does_not_raise(self, temp_db):
        """
        DOC: Deletar workspace inexistente não levanta erro.

        O método delete() deve ser idempotente.
        """
        # Não deve levantar erro
        temp_db.delete("nonexistent")


class TestWorkspaceRepositoryPersistence:
    """Testa persistência entre instâncias."""

    def test_repository_persists_across_instances(self, tmp_path):
        """
        DOC: Workspaces persistem entre instâncias do repositório.

        Ao criar uma nova instância com o mesmo caminho,
        os workspaces devem estar disponíveis.
        """
        db_path = tmp_path / "workspaces.db"

        # Primeira instância - salvar
        repo1 = WorkspaceRepository.create(db_path)
        workspace = Workspace(
            id="persistent",
            name="Persistent",
            path="workspace/persistent",
            description="Persiste entre instancias",
            auto=False,
            enabled=True
        )
        repo1.save(workspace)

        # Segunda instância - recuperar
        repo2 = WorkspaceRepository.create(db_path)
        retrieved = repo2.get("persistent")

        assert retrieved is not None
        assert retrieved.name == "Persistent"
        assert retrieved.description == "Persiste entre instancias"


class TestWorkspaceRepositoryBooleanFields:
    """Testa armazenamento correto de campos booleanos."""

    def test_repository_stores_boolean_auto_correctly(self, temp_db):
        """
        DOC: Campo auto deve ser armazenado como boolean.

        SQLite não tem tipo nativo boolean, mas deve armazenar
        como 0 (False) ou 1 (True).
        """
        ws_true = Workspace(
            id="auto_true",
            name="Auto True",
            path="workspace/auto_true",
            description="Auto verdadeiro",
            auto=True,
            enabled=True
        )
        ws_false = Workspace(
            id="auto_false",
            name="Auto False",
            path="workspace/auto_false",
            description="Auto falso",
            auto=False,
            enabled=True
        )

        temp_db.save(ws_true)
        temp_db.save(ws_false)

        retrieved_true = temp_db.get("auto_true")
        retrieved_false = temp_db.get("auto_false")

        assert retrieved_true.auto is True
        assert retrieved_false.auto is False

    def test_repository_stores_boolean_enabled_correctly(self, temp_db):
        """
        DOC: Campo enabled deve ser armazenado como boolean.
        """
        ws_enabled = Workspace(
            id="enabled_ws",
            name="Enabled",
            path="workspace/enabled",
            description="Habilitado",
            auto=False,
            enabled=True
        )
        ws_disabled = Workspace(
            id="disabled_ws",
            name="Disabled",
            path="workspace/disabled",
            description="Desabilitado",
            auto=False,
            enabled=False
        )

        temp_db.save(ws_enabled)
        temp_db.save(ws_disabled)

        retrieved_enabled = temp_db.get("enabled_ws")
        retrieved_disabled = temp_db.get("disabled_ws")

        assert retrieved_enabled.enabled is True
        assert retrieved_disabled.enabled is False
