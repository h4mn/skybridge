# -*- coding: utf-8 -*-
"""
Testes TDD para Kanban API endpoints.

Metodologia: TDD Estrito (PRD023)
- Testes escritos ANTES da implementação
- Testes falham primeiro (RED)
- Implementação mínima para passar (GREEN)
- Refatoração mantendo verde (REFACTOR)

DOC: tests/integration/api/test_kanban_api.py
DOC: PRD024 - Kanban Cards Vivos
"""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.kanban.application.kanban_initializer import KanbanInitializer
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter


@pytest.fixture
def temp_db():
    """Cria banco temporário para testes."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup - tentar deletar, ignora se ainda estiver sendo usado (Windows)
    try:
        db_path.unlink()
    except PermissionError:
        pass  # Windows pode deixar o arquivo locked brevemente


@pytest.fixture
def initialized_kanban(temp_db):
    """Inicializa kanban.db com board e listas padrão."""
    initializer = KanbanInitializer(temp_db)
    initializer.initialize()
    yield temp_db
    initializer.disconnect()


@pytest.fixture
def kanban_router(initialized_kanban):
    """Cria router Kanban para testes."""
    from runtime.delivery.kanban_routes import create_kanban_router
    from fastapi import FastAPI
    import runtime.delivery.kanban_routes as routes_module

    # Monkey patch _get_kanban_db_path ANTES de criar o router
    original_get_path = routes_module._get_kanban_db_path

    def mock_get_path(workspace_id: str):
        """Usa banco temporário ignorando workspace_id."""
        return initialized_kanban

    routes_module._get_kanban_db_path = mock_get_path

    app = FastAPI()
    router = create_kanban_router()
    app.include_router(router)

    yield TestClient(app)

    # Restore original function
    routes_module._get_kanban_db_path = original_get_path


# =============================================================================
# TESTES: Boards
# =============================================================================


async def test_get_boards_deve_retornar_todos_boards(kanban_router):
    """
    DOC: GET /kanban/boards

    Given: Board "Skybridge" existe
    When: GET /kanban/boards é chamado
    Then: Deve retornar lista com board "Skybridge"
    """
    # When
    response = kanban_router.get("/kanban/boards")

    # Then
    assert response.status_code == 200
    boards = response.json()
    assert len(boards) == 1
    assert boards[0]["name"] == "Skybridge"


async def test_get_board_inexistente_deve_retornar_404(kanban_router):
    """
    DOC: GET /kanban/boards/{id} - Board não existe

    Given: Board não existe
    When: GET /kanban/boards/inexistente é chamado
    Then: Deve retornar 404
    """
    # When
    response = kanban_router.get("/kanban/boards/inexistente")

    # Then
    assert response.status_code == 404


# =============================================================================
# TESTES: Lists
# =============================================================================


async def test_get_lists_deve_retornar_6_listas_padrao(kanban_router):
    """
    DOC: GET /kanban/lists

    Given: Board "Skybridge" tem 6 listas padrão
    When: GET /kanban/lists é chamado
    Then: Deve retornar 6 listas ordenadas por position
    """
    # When
    response = kanban_router.get("/kanban/lists")

    # Then
    assert response.status_code == 200
    lists = response.json()
    assert len(lists) == 6

    # Verifica ordenação por position
    for i in range(len(lists) - 1):
        assert lists[i]["position"] <= lists[i + 1]["position"]

    # Verifica nomes das listas
    list_names = [lst["name"] for lst in lists]
    assert "Issues" in list_names
    assert "Brainstorm" in list_names
    assert "A Fazer" in list_names
    assert "Em Andamento" in list_names
    assert "Em Revisão" in list_names
    assert "Publicar" in list_names


# =============================================================================
# TESTES: Cards
# =============================================================================


async def test_get_cards_deve_retornar_cards_filtrados(kanban_router, initialized_kanban):
    """
    DOC: GET /kanban/cards - Filtro por lista

    Given: Cards existem em múltiplas listas
    When: GET /kanban/cards?list_id=xxx é chamado
    Then: Deve retornar apenas cards da lista especificada
    """
    from core.kanban.domain.database import KanbanCard

    # Given: Criar card em cada lista
    adapter = SQLiteKanbanAdapter(initialized_kanban)
    adapter.connect()

    try:
        # Busca listas
        lists_result = adapter.list_lists("skybridge-main")
        lists = lists_result.value

        # Cria 1 card em cada lista
        for lst in lists[:3]:  # Apenas nas 3 primeiras listas
            card = KanbanCard(
                id=f"card-{lst.id}",
                list_id=lst.id,
                title=f"Card em {lst.name}",
            )
            adapter.create_card(card)

        # When: Busca cards da primeira lista
        first_list = lists[0]
        response = kanban_router.get(f"/kanban/cards?list_id={first_list.id}")

        # Then
        assert response.status_code == 200
        cards = response.json()
        assert len(cards) == 1
        assert cards[0]["list_id"] == first_list.id
    finally:
        adapter.disconnect()


async def test_get_cards_vivos_deve_vir_primeiro(kanban_router, initialized_kanban):
    """
    DOC: GET /kanban/cards - Cards vivos primeiro

    Given: Lista tem cards normais e cards "vivos" (being_processed=True)
    When: GET /kanban/cards é chamado
    Then: Cards vivos devem vir PRIMEIRO na resposta
    """
    from core.kanban.domain.database import KanbanCard

    # Given
    adapter = SQLiteKanbanAdapter(initialized_kanban)
    adapter.connect()

    try:
        # Busca primeira lista
        lists_result = adapter.list_lists("skybridge-main")
        first_list = lists_result.value[0]

        # Cria card normal
        normal_card = KanbanCard(
            id="card-normal",
            list_id=first_list.id,
            title="Card Normal",
            being_processed=False,
            position=10,
        )
        adapter.create_card(normal_card)

        # Cria card vivo
        live_card = KanbanCard(
            id="card-vivo",
            list_id=first_list.id,
            title="Card Vivo",
            being_processed=True,
            position=0,
        )
        adapter.create_card(live_card)

        # When
        response = kanban_router.get("/kanban/cards")

        # Then
        assert response.status_code == 200
        cards = response.json()
        assert len(cards) == 2

        # Primeiro card deve ser o vivo
        assert cards[0]["being_processed"] is True
        assert cards[0]["id"] == "card-vivo"

        # Segundo card deve ser o normal
        assert cards[1]["being_processed"] is False
        assert cards[1]["id"] == "card-normal"
    finally:
        adapter.disconnect()


async def test_create_card_deve_criar_novo_card(kanban_router, initialized_kanban):
    """
    DOC: POST /kanban/cards

    Given: Dados válidos de card
    When: POST /kanban/cards é chamado
    Then: Deve criar card e retornar card criado
    """
    # Given
    adapter = SQLiteKanbanAdapter(initialized_kanban)
    adapter.connect()

    try:
        lists_result = adapter.list_lists("skybridge-main")
        first_list = lists_result.value[0]

        # When
        response = kanban_router.post(
            "/kanban/cards",
            json={
                "list_id": first_list.id,
                "title": "Novo Card Teste",
                "description": "Descrição do card",
                "labels": ["bug", "high-priority"],
            }
        )

        # Then
        assert response.status_code == 201
        card = response.json()
        assert card["title"] == "Novo Card Teste"
        assert card["description"] == "Descrição do card"
        assert "bug" in card["labels"]
    finally:
        adapter.disconnect()


async def test_update_card_deve_atualizar_titulo(kanban_router, initialized_kanban):
    """
    DOC: PATCH /kanban/cards/{id}

    Given: Card existe
    When: PATCH /kanban/cards/{id} é chamado com novo título
    Then: Deve atualizar card e retornar card atualizado
    """
    from core.kanban.domain.database import KanbanCard

    # Given: Cria card
    adapter = SQLiteKanbanAdapter(initialized_kanban)
    adapter.connect()

    try:
        lists_result = adapter.list_lists("skybridge-main")
        first_list = lists_result.value[0]

        card = KanbanCard(
            id="card-update-test",
            list_id=first_list.id,
            title="Título Original",
        )
        adapter.create_card(card)

        # When: Atualiza título
        response = kanban_router.patch(
            "/kanban/cards/card-update-test",
            json={"title": "Título Atualizado"}
        )

        # Then
        assert response.status_code == 200
        updated_card = response.json()
        assert updated_card["title"] == "Título Atualizado"
    finally:
        adapter.disconnect()


async def test_delete_card_deve_remover_card(kanban_router, initialized_kanban):
    """
    DOC: DELETE /kanban/cards/{id}

    Given: Card existe
    When: DELETE /kanban/cards/{id} é chamado
    Then: Card deve ser removido do banco
    """
    from core.kanban.domain.database import KanbanCard

    # Given: Cria card
    adapter = SQLiteKanbanAdapter(initialized_kanban)
    adapter.connect()

    try:
        lists_result = adapter.list_lists("skybridge-main")
        first_list = lists_result.value[0]

        card = KanbanCard(
            id="card-delete-test",
            list_id=first_list.id,
            title="Card Para Deletar",
        )
        adapter.create_card(card)

        # When: Deleta card
        response = kanban_router.delete("/kanban/cards/card-delete-test")

        # Then: Deve retornar 204
        assert response.status_code == 204

        # Verifica que card foi removido
        get_response = kanban_router.get("/kanban/cards/card-delete-test")
        assert get_response.status_code == 404
    finally:
        adapter.disconnect()


async def test_initialize_kanban_deve_criar_estrutura(kanban_router):
    """
    DOC: POST /kanban/initialize

    Given: Workspace sem kanban.db
    When: POST /kanban/initialize é chamado
    Then: Deve criar board e 6 listas padrão
    """
    # When
    response = kanban_router.post("/kanban/initialize")

    # Then
    assert response.status_code == 200
    result = response.json()
    assert result["ok"] is True

    # Verifica que board foi criado
    boards_response = kanban_router.get("/kanban/boards")
    assert boards_response.status_code == 200
    boards = boards_response.json()
    assert len(boards) == 1
    assert boards[0]["name"] == "Skybridge"

    # Verifica que 6 listas foram criadas
    lists_response = kanban_router.get("/kanban/lists")
    assert lists_response.status_code == 200
    lists = lists_response.json()
    assert len(lists) == 6


# =============================================================================
# TESTES: Card History
# =============================================================================


async def test_get_card_history_deve_retornar_historico_vazio(kanban_router, initialized_kanban):
    """
    DOC: GET /kanban/cards/{id}/history

    Given: Card existe sem histórico manual
    When: GET /kanban/cards/{id}/history é chamado
    Then: Deve retornar histórico (pelo menos evento "created" automático)
    """
    from core.kanban.domain.database import KanbanCard

    # Given: Cria card
    adapter = SQLiteKanbanAdapter(initialized_kanban)
    adapter.connect()

    try:
        lists_result = adapter.list_lists("skybridge-main")
        first_list = lists_result.value[0]

        card = KanbanCard(
            id="card-history-test",
            list_id=first_list.id,
            title="Card Teste Histórico",
        )
        adapter.create_card(card)

        # When: Busca histórico
        response = kanban_router.get("/kanban/cards/card-history-test/history")

        # Then
        assert response.status_code == 200
        history = response.json()
        assert isinstance(history, list)
        # Deve ter pelo menos o evento "created" automático
        assert len(history) >= 1
    finally:
        adapter.disconnect()


async def test_get_card_history_apos_mover_card(kanban_router, initialized_kanban):
    """
    DOC: GET /kanban/cards/{id}/history - Card movido

    Given: Card foi movido entre listas
    When: GET /kanban/cards/{id}/history é chamado
    Then: Deve conter evento "moved" com from_list_id e to_list_id
    """
    from core.kanban.domain.database import KanbanCard

    # Given: Cria e move card
    adapter = SQLiteKanbanAdapter(initialized_kanban)
    adapter.connect()

    try:
        lists_result = adapter.list_lists("skybridge-main")
        lists = lists_result.value

        card = KanbanCard(
            id="card-move-history-api",
            list_id=lists[0].id,
            title="Card Move Histórico API",
        )
        adapter.create_card(card)

        # Move card
        adapter.update_card("card-move-history-api", list_id=lists[1].id)

        # When: Busca histórico
        response = kanban_router.get("/kanban/cards/card-move-history-api/history")

        # Then
        assert response.status_code == 200
        history = response.json()

        # Deve ter evento "moved"
        moved_events = [h for h in history if h["event"] == "moved"]
        assert len(moved_events) >= 1

        # Verifica from_list_id e to_list_id
        moved = moved_events[0]
        assert moved["from_list_id"] == lists[0].id
        assert moved["to_list_id"] == lists[1].id
    finally:
        adapter.disconnect()


async def test_get_card_history_apos_processamento(kanban_router, initialized_kanban):
    """
    DOC: GET /kanban/cards/{id}/history - Card processado

    Given: Card foi marcado como being_processed e depois completado
    When: GET /kanban/cards/{id}/history é chamado
    Then: Deve conter eventos "processing_started" e "processing_completed"
    """
    from core.kanban.domain.database import KanbanCard

    # Given: Cria e marca card como processado
    adapter = SQLiteKanbanAdapter(initialized_kanban)
    adapter.connect()

    try:
        lists_result = adapter.list_lists("skybridge-main")
        first_list = lists_result.value[0]

        card = KanbanCard(
            id="card-processing-history-api",
            list_id=first_list.id,
            title="Card Processing Histórico API",
        )
        adapter.create_card(card)

        # Marca como sendo processado
        adapter.update_card(
            "card-processing-history-api",
            being_processed=True,
            processing_job_id="job-api-test",
            processing_step=1,
            processing_total_steps=3,
        )

        # Marca como completo
        adapter.update_card(
            "card-processing-history-api",
            being_processed=False,
            processing_step=3,
        )

        # When: Busca histórico
        response = kanban_router.get("/kanban/cards/card-processing-history-api/history")

        # Then
        assert response.status_code == 200
        history = response.json()

        # Deve ter eventos de processamento
        started_events = [h for h in history if h["event"] == "processing_started"]
        completed_events = [h for h in history if h["event"] == "processing_completed"]

        assert len(started_events) >= 1
        assert len(completed_events) >= 1
    finally:
        adapter.disconnect()


async def test_get_card_history_card_inexistente(kanban_router):
    """
    DOC: GET /kanban/cards/{id}/history - Card não existe

    Given: Card não existe
    When: GET /kanban/cards/{id}/history é chamado
    Then: Deve retornar lista vazia (não 404)
    """
    # When
    response = kanban_router.get("/kanban/cards/card-inexistente/history")

    # Then: Retorna lista vazia (não 404 para evitar vazamento de info)
    assert response.status_code == 200
    history = response.json()
    assert isinstance(history, list)
    assert len(history) == 0
