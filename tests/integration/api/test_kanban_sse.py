# -*- coding: utf-8 -*-
"""
Testes de Integração: Kanban SSE - EventBus Integration.

DOC: PRD024 Task 7 - SSE com eventos dinâmicos
DOC: runtime/delivery/kanban_routes.py - Eventos CRUD → SSE

Testa que operações CRUD emitem eventos para o EventBus.
NOTA: Testes de GET no SSE endpoint removidos pois causam loop infinito com TestClient.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from fastapi.testclient import TestClient

from src.core.kanban.application.kanban_initializer import KanbanInitializer
from src.core.kanban.application.kanban_event_bus import KanbanEventBus


@pytest.fixture
def workspace_id() -> str:
    return "test-kanban-sse"


@pytest.fixture
def kanban_db_path(workspace_id: str, tmp_path: Path) -> Path:
    db_path = tmp_path / "workspace" / workspace_id / "data" / "kanban.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    initializer = KanbanInitializer(str(db_path))
    initializer.initialize()
    return db_path


@pytest.fixture
def mock_event_bus():
    mock = Mock(spec=KanbanEventBus)
    async def mock_publish(event_type, data, workspace_id):
        pass
    mock.publish = AsyncMock(side_effect=mock_publish)
    mock.get_subscribers_count = Mock(return_value=0)
    return mock


@pytest.fixture
def app_client(kanban_db_path: Path, workspace_id: str, mock_event_bus, monkeypatch) -> TestClient:
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


class TestKanbanEventBusIntegration:
    """
    Testes de integração EventBus com operações Kanban.

    Verifica que operações CRUD emitem eventos para o EventBus.
    """

    def test_create_card_emite_card_created_event(
        self, app_client: TestClient, workspace_id: str
    ):
        """DOC: POST /cards emite card_created no EventBus."""
        from src.runtime.delivery import kanban_routes
        event_bus_mock = kanban_routes._event_bus

        response = app_client.post(
            "/api/kanban/cards",
            json={"list_id": "brainstorm", "title": "Test Card", "description": "Test"},
            headers={"X-Workspace": workspace_id},
        )

        assert response.status_code == 201
        assert response.json()["title"] == "Test Card"

        event_bus_mock.publish.assert_called_once()
        call_args = event_bus_mock.publish.call_args
        assert call_args[0][0] == "card_created"
        assert call_args[0][2] == workspace_id

    def test_update_card_emite_card_updated_event(
        self, app_client: TestClient, workspace_id: str
    ):
        """DOC: PATCH /cards emite card_updated no EventBus."""
        from src.runtime.delivery import kanban_routes
        event_bus_mock = kanban_routes._event_bus

        create_response = app_client.post(
            "/api/kanban/cards",
            json={"list_id": "brainstorm", "title": "Original"},
            headers={"X-Workspace": workspace_id},
        )
        card_id = create_response.json()["id"]

        event_bus_mock.publish.reset_mock()

        update_response = app_client.patch(
            f"/api/kanban/cards/{card_id}",
            json={"title": "Updated"},
            headers={"X-Workspace": workspace_id},
        )

        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated"

        event_bus_mock.publish.assert_called_once()
        call_args = event_bus_mock.publish.call_args
        assert call_args[0][0] == "card_updated"

    def test_delete_card_emite_card_deleted_event(
        self, app_client: TestClient, workspace_id: str
    ):
        """DOC: DELETE /cards emite card_deleted no EventBus."""
        from src.runtime.delivery import kanban_routes
        event_bus_mock = kanban_routes._event_bus

        create_response = app_client.post(
            "/api/kanban/cards",
            json={"list_id": "brainstorm", "title": "To Delete"},
            headers={"X-Workspace": workspace_id},
        )
        card_id = create_response.json()["id"]

        event_bus_mock.publish.reset_mock()

        delete_response = app_client.delete(
            f"/api/kanban/cards/{card_id}",
            headers={"X-Workspace": workspace_id},
        )

        assert delete_response.status_code == 204

        event_bus_mock.publish.assert_called_once()
        call_args = event_bus_mock.publish.call_args
        assert call_args[0][0] == "card_deleted"

    def test_move_card_emite_card_updated_event(
        self, app_client: TestClient, workspace_id: str
    ):
        """DOC: Mover card entre listas emite card_updated."""
        from src.runtime.delivery import kanban_routes
        event_bus_mock = kanban_routes._event_bus

        create_response = app_client.post(
            "/api/kanban/cards",
            json={"list_id": "brainstorm", "title": "Move Test"},
            headers={"X-Workspace": workspace_id},
        )
        card_id = create_response.json()["id"]

        event_bus_mock.publish.reset_mock()

        move_response = app_client.patch(
            f"/api/kanban/cards/{card_id}",
            json={"list_id": "a-fazer"},
            headers={"X-Workspace": workspace_id},
        )

        assert move_response.status_code == 200
        assert move_response.json()["list_id"] == "a-fazer"

        event_bus_mock.publish.assert_called_once()
        call_args = event_bus_mock.publish.call_args
        assert call_args[0][0] == "card_updated"

    def test_card_processing_emite_card_updated_event(
        self, app_client: TestClient, workspace_id: str
    ):
        """DOC: Atualizar being_processed emite card_updated."""
        from src.runtime.delivery import kanban_routes
        event_bus_mock = kanban_routes._event_bus

        create_response = app_client.post(
            "/api/kanban/cards",
            json={"list_id": "brainstorm", "title": "Processing Test"},
            headers={"X-Workspace": workspace_id},
        )
        card_id = create_response.json()["id"]

        event_bus_mock.publish.reset_mock()

        update_response = app_client.patch(
            f"/api/kanban/cards/{card_id}",
            json={"being_processed": True, "processing_step": 1, "processing_total_steps": 5},
            headers={"X-Workspace": workspace_id},
        )

        assert update_response.status_code == 200
        assert update_response.json()["being_processed"] == True

        event_bus_mock.publish.assert_called_once()
        call_args = event_bus_mock.publish.call_args
        assert call_args[0][0] == "card_updated"
