# -*- coding: utf-8 -*-
"""
Testes de integração para WorkspacesAPI.

TDD Estrito: Testes que documentam o comportamento esperado da API.

DOC: ADR024 - GET /api/workspaces lista todos.
DOC: PB013 - POST /api/workspaces cria nova instância.
DOC: PB013 - DELETE /api/workspaces/:id deleta workspace.
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


@pytest.fixture
def mock_workspace_config():
    """Fixture: WorkspaceConfig mock para testes."""
    from runtime.config.workspace_config import Workspace

    core_ws = Workspace(
        id="core",
        name="Skybridge Core",
        path="workspace/core",
        description="Instancia principal",
        auto=True,
        enabled=True
    )

    config = Mock()
    config.default = "core"
    config.workspaces = {
        "core": core_ws,
    }
    return config


@pytest.fixture
def mock_workspace_repository():
    """Fixture: WorkspaceRepository mock para testes."""
    repo = Mock()
    repo.list_all.return_value = []
    repo.get.return_value = None
    return repo


@pytest.fixture
def mock_workspace_initializer():
    """Fixture: WorkspaceInitializer mock para testes."""
    init = Mock()
    return init


@pytest.fixture
def client(mock_workspace_config, mock_workspace_repository, mock_workspace_initializer):
    """
    Fixture: Client de teste para API de workspaces.

    Cria um TestClient com as dependências mockadas.
    """
    from runtime.delivery.workspaces_routes import create_router

    router = create_router(
        config=mock_workspace_config,
        repository=mock_workspace_repository,
        initializer=mock_workspace_initializer
    )

    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)

    return TestClient(app)


class TestListWorkspaces:
    """Testa GET /api/workspaces."""

    def test_list_workspaces(self, client, mock_workspace_repository):
        """
        DOC: ADR024 - GET /api/workspaces lista todos.

        Deve retornar lista de todos os workspaces cadastrados.
        """
        from runtime.config.workspace_config import Workspace

        # Mockar workspaces
        core_ws = Workspace(
            id="core",
            name="Skybridge Core",
            path="workspace/core",
            description="Instancia principal",
            auto=True,
            enabled=True
        )
        trading_ws = Workspace(
            id="trading",
            name="Trading Bot",
            path="workspace/trading",
            description="Bot de trading",
            auto=False,
            enabled=True
        )

        mock_workspace_repository.list_all.return_value = [core_ws, trading_ws]

        response = client.get("/api/workspaces")

        assert response.status_code == 200
        data = response.json()
        assert "workspaces" in data
        assert len(data["workspaces"]) == 2
        assert any(ws["id"] == "core" for ws in data["workspaces"])
        assert any(ws["id"] == "trading" for ws in data["workspaces"])

    def test_list_workspaces_empty(self, client, mock_workspace_repository):
        """
        DOC: Lista vazia quando não há workspaces.

        """
        mock_workspace_repository.list_all.return_value = []

        response = client.get("/api/workspaces")

        assert response.status_code == 200
        data = response.json()
        assert data["workspaces"] == []


class TestCreateWorkspace:
    """Testa POST /api/workspaces."""

    def test_create_workspace(self, client, mock_workspace_repository, mock_workspace_initializer):
        """
        DOC: PB013 - POST /api/workspaces cria nova instância.

        Deve criar estrutura de diretórios e salvar no repositório.
        """
        payload = {
            "id": "trading",
            "name": "Trading Bot",
            "path": "workspace/trading",
            "description": "Bot de trading automatizado"
        }

        response = client.post("/api/workspaces", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "trading"
        assert data["name"] == "Trading Bot"

        # Verificar que initializer foi chamado
        mock_workspace_initializer.create.assert_called_once_with(
            "trading",
            "Trading Bot",
            auto=False
        )

    def test_create_workspace_missing_required_field(self, client):
        """
        DOC: Campos obrigatórios devem ser validados.

        """
        payload = {
            "id": "incomplete"
            # Falta: name, path
        }

        response = client.post("/api/workspaces", json=payload)

        assert response.status_code == 422  # Validation error


class TestDeleteWorkspace:
    """Testa DELETE /api/workspaces/:id."""

    def test_delete_workspace(self, client, mock_workspace_repository):
        """
        DOC: PB013 - DELETE /api/workspaces/:id deleta workspace.

        Deve remover do repositório e opcionalmente fazer backup.
        """
        # Mockar workspace existente
        from runtime.config.workspace_config import Workspace

        temp_ws = Workspace(
            id="temp",
            name="Temp",
            path="workspace/temp",
            description="Temporario",
            auto=False,
            enabled=True
        )
        mock_workspace_repository.get.return_value = temp_ws

        # Deletar
        response = client.delete("/api/workspaces/temp")

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verificar que delete foi chamado no repositório
        mock_workspace_repository.delete.assert_called_with("temp")

    def test_delete_workspace_not_found(self, client, mock_workspace_repository):
        """
        DOC: Deletar workspace inexistente retorna 404.

        """
        mock_workspace_repository.get.return_value = None

        response = client.delete("/api/workspaces/nonexistent")

        assert response.status_code == 404


class TestGetWorkspace:
    """Testa GET /api/workspaces/:id."""

    def test_get_workspace_by_id(self, client, mock_workspace_repository):
        """
        DOC: GET /api/workspaces/:id retorna workspace específico.

        """
        from runtime.config.workspace_config import Workspace

        trading_ws = Workspace(
            id="trading",
            name="Trading Bot",
            path="workspace/trading",
            description="Bot de trading",
            auto=False,
            enabled=True
        )

        mock_workspace_repository.get.return_value = trading_ws

        response = client.get("/api/workspaces/trading")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "trading"
        assert data["name"] == "Trading Bot"

    def test_get_workspace_not_found(self, client, mock_workspace_repository):
        """
        DOC: GET /api/workspaces/:id retorna 404 se não existe.

        """
        mock_workspace_repository.get.return_value = None

        response = client.get("/api/workspaces/nonexistent")

        assert response.status_code == 404
