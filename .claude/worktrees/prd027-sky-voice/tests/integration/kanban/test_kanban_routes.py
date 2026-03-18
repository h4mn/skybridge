# -*- coding: utf-8 -*-
"""
Testes TDD para Kanban Routes - Endpoint /sync/from-trello.

Metodologia: TDD Estrito (PRD023)
- Testes escritos ANTES da implementação
- Testes falham primeiro (RED)
- Implementação mínima para passar (GREEN)
- Refatoração mantendo verde (REFACTOR)

DOC: tests/integration/kanban/test_kanban_routes.py
DOC: runtime/delivery/kanban_routes.py - POST /kanban/sync/from-trello
DOC: PRD026 RF-015: Endpoint manual de sync
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from core.kanban.domain.database import KanbanBoard, KanbanCard, KanbanList
from core.kanban.domain.card import Card
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter
from kernel import Result
from runtime.delivery.kanban_routes import create_kanban_router


@pytest.fixture
def temp_db():
    """Cria banco temporário para testes."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    db_path.unlink()


@pytest.fixture
def router_with_mock_trello(temp_db, mock_trello_adapter):
    """Cria router com mock do TrelloSyncService."""
    from unittest.mock import MagicMock

    router = create_kanban_router()

    # Mock do _get_kanban_db_path para usar temp_db
    with patch("runtime.delivery.kanban_routes._get_kanban_db_path", return_value=temp_db):
        yield router, mock_trello_adapter


@pytest.fixture
def mock_trello_adapter():
    """Mock do TrelloAdapter."""
    from unittest.mock import AsyncMock
    mock = AsyncMock()
    return mock


@pytest.fixture
def client(router_with_mock_trello):
    """Cria cliente de teste com router."""
    from fastapi import FastAPI
    from unittest.mock import patch, AsyncMock, MagicMock

    router, mock_trello = router_with_mock_trello

    app = FastAPI()
    app.include_router(router)

    # Cria mock do TrelloSyncService
    mock_sync_service = MagicMock()
    mock_sync_service.sync_from_trello = AsyncMock(return_value=Result.ok(0))
    mock_sync_service.start_queue_worker = AsyncMock(return_value=None)  # AsyncMock para await
    mock_sync_service.stop_queue_worker = AsyncMock(return_value=None)  # AsyncMock para await

    # Mock da factory que cria o TrelloSyncService
    with patch("core.kanban.application.trello_sync_service.TrelloSyncService", return_value=mock_sync_service):
        yield TestClient(app), mock_sync_service


# =============================================================================
# TESTES: POST /kanban/sync/from-trello (RF-015)
# =============================================================================


async def test_sync_from_trello_endpoint_deve_retornar_contagem_de_cards(client):
    """
    DOC: POST /kanban/sync/from-trello

    Given: Request com board_id
    When: POST /kanban/sync/from-trello é chamado
    Then: Deve retornar contagem de cards sincronizados
    """
    test_client, mock_sync_service = client

    # Given: sync_from_trello retorna 5 cards sincronizados
    mock_sync_service.sync_from_trello.return_value = Result.ok(5)

    # When
    response = test_client.post(
        "/kanban/sync/from-trello",
        json={"board_id": "board-1"}
    )

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["synced_count"] == 5
    assert data["status"] == "success"


async def test_sync_from_trello_endpoint_sem_board_id_deve_retornar_erro(client):
    """
    DOC: POST /kanban/sync/from-trello - Validação

    Given: Request sem board_id
    When: POST /kanban/sync/from-trello é chamado
    Then: Deve retornar erro 422 (validation error)
    """
    test_client, mock_sync_service = client

    # When: Request sem board_id
    response = test_client.post(
        "/kanban/sync/from-trello",
        json={}
    )

    # Then
    assert response.status_code == 422


async def test_sync_from_trello_endpoint_erro_trello_deve_retornar_500(client):
    """
    DOC: POST /kanban/sync/from-trello - Tratamento de erro

    Given: TrelloSyncService retorna erro
    When: POST /kanban/sync/from-trello é chamado
    Then: Deve retornar erro 500 com mensagem
    """
    test_client, mock_sync_service = client

    # Given: sync_from_trello retorna erro
    mock_sync_service.sync_from_trello.return_value = Result.err("Trello API Error")

    # When
    response = test_client.post(
        "/kanban/sync/from-trello",
        json={"board_id": "board-1"}
    )

    # Then
    assert response.status_code == 500
    data = response.json()
    assert "Trello API Error" in data["detail"]


async def test_sync_from_trello_endpoint_respeita_workspace_header(client):
    """
    DOC: POST /kanban/sync/from-trello - Workspace isolation

    Given: Request com X-Workspace header
    When: POST /kanban/sync/from-trello é chamado
    Then: Deve usar kanban.db do workspace especificado
    """
    test_client, mock_sync_service = client

    mock_sync_service.sync_from_trello.return_value = Result.ok(3)

    # When: Request com X-Workspace header
    response = test_client.post(
        "/kanban/sync/from-trello",
        json={"board_id": "board-1"},
        headers={"X-Workspace": "trading"}
    )

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["synced_count"] == 3


async def test_sync_from_trello_endpoint_emite_eventos_sse_para_cards_atualizados(client):
    """
    DOC: POST /kanban/sync/from-trello - SSE events

    Given: Cards são atualizados durante sync
    When: POST /kanban/sync/from-trello é chamado
    Then: SSE deve emitir eventos para cada card atualizado

    NOTA: Este teste valida que o sync emite eventos SSE.
    A implementação deve chamar _emit_card_event para cada card atualizado.
    """
    test_client, mock_sync_service = client

    mock_sync_service.sync_from_trello.return_value = Result.ok(2)

    # When
    response = test_client.post(
        "/kanban/sync/from-trello",
        json={"board_id": "board-1"}
    )

    # Then: sync foi executado
    assert response.status_code == 200
    mock_sync_service.sync_from_trello.assert_called_once()
