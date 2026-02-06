# -*- coding: utf-8 -*-
"""
Testes de Integração: Kanban SSE com EventBus.

DOC: PRD024 Task 7 - SSE com eventos dinâmicos
DOC: core/kanban/application/kanban_event_bus.py
DOC: runtime/delivery/kanban_routes.py - Eventos CRUD → SSE

Testa que operações CRUD emitem eventos que são entregues via SSE.

NOTA: Usa mock do EventBus para testar com TestClient (que não roda event loop).
"""
import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from fastapi.testclient import TestClient

from src.core.kanban.application.kanban_initializer import KanbanInitializer
from src.core.kanban.application.kanban_event_bus import KanbanEventBus


@pytest.fixture
def workspace_id() -> str:
    """ID do workspace para testes."""
    return "test-sse-integration"


@pytest.fixture
def kanban_db_path(workspace_id: str, tmp_path: Path) -> Path:
    """Cria kanban.db temporário para testes."""
    db_path = tmp_path / "workspace" / workspace_id / "data" / "kanban.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    initializer = KanbanInitializer(str(db_path))
    initializer.initialize()

    return db_path


@pytest.fixture
def mock_event_bus():
    """Mock do EventBus para testes síncronos."""
    mock = Mock(spec=KanbanEventBus)

    # Mock publish como async
    async def mock_publish(event_type, data, workspace_id):
        pass

    mock.publish = AsyncMock(side_effect=mock_publish)
    mock.get_subscribers_count = Mock(return_value=0)

    return mock


@pytest.fixture
def app_client(kanban_db_path: Path, workspace_id: str, mock_event_bus, monkeypatch) -> TestClient:
    """Cria TestClient com app FastAPI configurado."""
    def mock_get_db_path(ws_id: str) -> Path:
        if ws_id == workspace_id:
            return kanban_db_path
        from pathlib import Path
        return Path("workspace") / ws_id / "data" / "kanban.db"

    import src.runtime.delivery.kanban_routes as kanban_routes
    monkeypatch.setattr(kanban_routes, "_get_kanban_db_path", mock_get_db_path)
    monkeypatch.setattr(kanban_routes, "_event_bus", mock_event_bus)

    from src.runtime.delivery.kanban_routes import create_kanban_router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(create_kanban_router(), prefix="/api")

    client = TestClient(app)
    client.db_path = kanban_db_path
    return client


class TestKanbanSSEIntegration:
    """
    Testes de integração SSE com EventBus.

    Verifica que operações CRUD emitem eventos via EventBus.
    """

    def test_create_card_emite_evento_sse(
        self, app_client: TestClient, workspace_id: str
    ):
        """
        DOC: kanban_routes.py - POST /cards emite card_created
        DOC: kanban_event_bus.py - publish()

        Testa que:
        - POST /cards emite evento card_created no EventBus
        - EventBus.publish é chamado com dados corretos
        """
        # Arrange: Obtém mock do EventBus
        from src.runtime.delivery import kanban_routes
        event_bus_mock = kanban_routes._event_bus

        # Act: Cria card via API
        response = app_client.post(
            "/api/kanban/cards",
            json={
                "list_id": "brainstorm",
                "title": "SSE Integration Test",
                "description": "Testing SSE events",
            },
            headers={"X-Workspace": workspace_id},
        )

        # Assert: Card criado
        assert response.status_code == 201
        card_data = response.json()
        assert card_data["title"] == "SSE Integration Test"

        # Assert: EventBus.publish foi chamado
        event_bus_mock.publish.assert_called_once()
        call_args = event_bus_mock.publish.call_args
        assert call_args[0][0] == "card_created"
        assert call_args[0][1]["title"] == "SSE Integration Test"
        assert call_args[0][2] == workspace_id

    def test_update_card_emite_evento_sse(
        self, app_client: TestClient, workspace_id: str
    ):
        """
        DOC: kanban_routes.py - PATCH /cards emite card_updated

        Testa que:
        - PATCH /cards emite evento card_updated
        - Evento contém dados atualizados
        """
        from src.runtime.delivery import kanban_routes
        event_bus_mock = kanban_routes._event_bus

        # Arrange: Cria card
        create_response = app_client.post(
            "/api/kanban/cards",
            json={"list_id": "brainstorm", "title": "Original Title"},
            headers={"X-Workspace": workspace_id},
        )
        assert create_response.status_code == 201
        card_id = create_response.json()["id"]

        # Reset mock para ignorar card_created
        event_bus_mock.publish.reset_mock()

        # Act: Atualiza card
        update_response = app_client.patch(
            f"/api/kanban/cards/{card_id}",
            json={"title": "Updated Title"},
            headers={"X-Workspace": workspace_id},
        )

        # Assert: Card atualizado (PATCH retorna 200 OK)
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Title"

        # Assert: EventBus.publish foi chamado com card_updated
        event_bus_mock.publish.assert_called_once()
        call_args = event_bus_mock.publish.call_args
        assert call_args[0][0] == "card_updated"
        assert call_args[0][1]["title"] == "Updated Title"

    def test_delete_card_emite_evento_sse(
        self, app_client: TestClient, workspace_id: str
    ):
        """
        DOC: kanban_routes.py - DELETE /cards emite card_deleted

        Testa que:
        - DELETE /cards emite evento card_deleted
        - Evento contém dados do card antes de deletar
        """
        from src.runtime.delivery import kanban_routes
        event_bus_mock = kanban_routes._event_bus

        # Arrange: Cria card
        create_response = app_client.post(
            "/api/kanban/cards",
            json={"list_id": "brainstorm", "title": "To Delete"},
            headers={"X-Workspace": workspace_id},
        )
        assert create_response.status_code == 201
        card_id = create_response.json()["id"]

        # Reset mock
        event_bus_mock.publish.reset_mock()

        # Act: Deleta card
        delete_response = app_client.delete(
            f"/api/kanban/cards/{card_id}",
            headers={"X-Workspace": workspace_id},
        )

        # Assert: Card deletado
        assert delete_response.status_code == 204

        # Assert: EventBus.publish foi chamado com card_deleted
        event_bus_mock.publish.assert_called_once()
        call_args = event_bus_mock.publish.call_args
        assert call_args[0][0] == "card_deleted"
        assert call_args[0][1]["id"] == card_id
        assert call_args[0][1]["title"] == "To Delete"
