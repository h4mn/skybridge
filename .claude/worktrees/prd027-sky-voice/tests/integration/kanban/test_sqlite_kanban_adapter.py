# -*- coding: utf-8 -*-
"""
Testes TDD para SQLiteKanbanAdapter.

Metodologia: TDD Estrito (PRD023)
- Testes escritos ANTES da implementação
- Testes falham primeiro (RED)
- Implementação mínima para passar (GREEN)
- Refatoração mantendo verde (REFACTOR)

DOC: tests/integration/kanban/sqlite_kanban_adapter.test.py
DOC: core/kanban/domain/schema.sql - Estrutura do banco
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from core.kanban.domain.database import KanbanBoard, KanbanCard, KanbanList
from core.kanban.domain.card import CardStatus
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter


@pytest.fixture
def temp_db_path():
    """Cria banco temporário para testes."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield Path(f.name)
    # Cleanup automático pelo tempfile


@pytest.fixture
def adapter(temp_db_path):
    """Cria adapter conectado ao banco temporário."""
    adapter = SQLiteKanbanAdapter(temp_db_path)
    result = adapter.connect()
    assert result.is_ok, f"Failed to connect: {result.error}"
    yield adapter
    adapter.disconnect()


# =============================================================================
# TESTES: BOARDS
# =============================================================================


async def test_create_board_deve_criar_novo_board(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.create_board()

    Given: Dados válidos de um board
    When: create_board() é chamado
    Then: Board deve ser criado e recuperável via get_board()
    """
    # Given
    board = KanbanBoard(
        id="board-1",
        name="Main Board",
        trello_board_id="trello-123",
        trello_sync_enabled=True,
    )

    # When
    result = adapter.create_board(board)

    # Then
    assert result.is_ok, f"Failed to create board: {result.error}"
    assert result.value.id == "board-1"

    # Verifica que foi persistido
    get_result = adapter.get_board("board-1")
    assert get_result.is_ok
    assert get_result.value.name == "Main Board"
    assert get_result.value.trello_board_id == "trello-123"


async def test_get_board_inexistente_deve_retornar_erro(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.get_board()

    Given: Board não existe no banco
    When: get_board() é chamado com ID inexistente
    Then: Deve retornar Result.err com mensagem de erro
    """
    # When
    result = adapter.get_board("inexistente")

    # Then
    assert result.is_err
    assert "não encontrado" in result.error.lower()


async def test_list_boards_deve_retornar_todos_boards(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.list_boards()

    Given: Múltiplos boards criados
    When: list_boards() é chamado
    Then: Deve retornar todos os boards ordenados por created_at DESC
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Board 1"))
    import time
    time.sleep(0.001)  # Pequeno delay para garantir timestamps diferentes
    adapter.create_board(KanbanBoard(id="board-2", name="Board 2"))

    # When
    result = adapter.list_boards()

    # Then
    assert result.is_ok
    boards = result.value
    assert len(boards) == 2
    assert boards[0].name == "Board 2"  # Criado depois, vem primeiro


# =============================================================================
# TESTES: LISTS
# =============================================================================


async def test_create_list_deve_criar_nova_lista(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.create_list()

    Given: Board existe e dados válidos de lista
    When: create_list() é chamado
    Then: Lista deve ser criada e recuperável
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))

    list_obj = KanbanList(
        id="list-1",
        board_id="board-1",
        name="To Do",
        position=0,
    )

    # When
    result = adapter.create_list(list_obj)

    # Then
    assert result.is_ok
    assert result.value.name == "To Do"


async def test_list_lists_deve_retornar_listas_ordenadas(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.list_lists()

    Given: Múltiplas listas criadas em posições diferentes
    When: list_lists() é chamado
    Then: Deve retornar listas ordenadas por position ASC
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="Done", position=2))
    adapter.create_list(KanbanList(id="list-2", board_id="board-1", name="To Do", position=1))

    # When
    result = adapter.list_lists("board-1")

    # Then
    assert result.is_ok
    lists = result.value
    assert len(lists) == 2
    assert lists[0].name == "To Do"  # position=1
    assert lists[1].name == "Done"  # position=2


# =============================================================================
# TESTES: CARDS (básico)
# =============================================================================


async def test_create_card_deve_criar_novo_card(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.create_card()

    Given: Lista existe e dados válidos de card
    When: create_card() é chamado
    Then: Card deve ser criado e recuperável
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    card = KanbanCard(
        id="card-1",
        list_id="list-1",
        title="Test card",
        description="Test description",
        labels=["bug", "high-priority"],
    )

    # When
    result = adapter.create_card(card)

    # Then
    assert result.is_ok
    assert result.value.title == "Test card"
    assert result.value.labels == ["bug", "high-priority"]


async def test_update_card_deve_atualizar_campos(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.update_card()

    Given: Card existe
    When: update_card() é chamado com novos valores
    Then: Campos devem ser atualizados e card deve ser recuperado com novos valores
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))
    adapter.create_card(KanbanCard(id="card-1", list_id="list-1", title="Original"))

    # When
    result = adapter.update_card("card-1", title="Updated", description="New description")

    # Then
    assert result.is_ok
    assert result.value.title == "Updated"
    assert result.value.description == "New description"


async def test_delete_card_deve_remover_card(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.delete_card()

    Given: Card existe
    When: delete_card() é chamado
    Then: Card deve ser removido do banco
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))
    adapter.create_card(KanbanCard(id="card-1", list_id="list-1", title="Test"))

    # When
    result = adapter.delete_card("card-1")

    # Then
    assert result.is_ok

    # Verifica que foi removido
    get_result = adapter.get_card("card-1")
    assert get_result.is_err


# =============================================================================
# TESTES: CARDS VIVOS (agent processing)
# =============================================================================


async def test_create_card_being_processed_deve_forcar_position_zero(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.create_card() com being_processed=True

    Given: Card com being_processed=True
    When: create_card() é chamado
    Then: Card deve ser criado com position=0 (forçado pelo adapter)
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="In Progress"))

    card = KanbanCard(
        id="card-1",
        list_id="list-1",
        title="Processing card",
        being_processed=True,
        position=999,  # Deve ser ignorado
    )

    # When
    result = adapter.create_card(card)

    # Then
    assert result.is_ok
    assert result.value.being_processed is True
    assert result.value.position == 0  # Forçado para 0


async def test_list_cards_deve_ordenar_vivos_primeiro(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.list_cards()

    Given: Múltiplos cards na lista, alguns sendo processados
    When: list_cards() é chamado
    Then: Cards sendo processados devem vir PRIMEIRO (being_processed DESC)
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="In Progress"))

    # Cria cards em ordem aleatória
    adapter.create_card(
        KanbanCard(
            id="card-1",
            list_id="list-1",
            title="Normal card 1",
            being_processed=False,
            position=1,
        )
    )
    adapter.create_card(
        KanbanCard(
            id="card-2",
            list_id="list-1",
            title="Processing card",
            being_processed=True,
            position=0,
        )
    )
    adapter.create_card(
        KanbanCard(
            id="card-3",
            list_id="list-1",
            title="Normal card 2",
            being_processed=False,
            position=2,
        )
    )

    # When
    result = adapter.list_cards("list-1")

    # Then
    assert result.is_ok
    cards = result.value
    assert len(cards) == 3

    # Primeiro deve ser o card sendo processado
    assert cards[0].id == "card-2"
    assert cards[0].being_processed is True

    # Depois os normais
    assert cards[1].id == "card-1"
    assert cards[2].id == "card-3"


async def test_update_card_processing_step_deve_atualizar_progresso(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.update_card() com processing_step

    Given: Card sendo processado
    When: update_card() é chamado com processing_step=N
    Then: Card deve ter processing_step atualizado
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="In Progress"))

    card = KanbanCard(
        id="card-1",
        list_id="list-1",
        title="Processing card",
        being_processed=True,
        processing_step=1,
        processing_total_steps=5,
    )
    adapter.create_card(card)

    # When
    result = adapter.update_card("card-1", processing_step=3)

    # Then
    assert result.is_ok
    assert result.value.processing_step == 3

    # Verifica percentual de progresso
    assert result.value.processing_progress_percent == 60.0  # 3/5


async def test_update_card_status_deve_mover_para_nova_lista(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.update_card_status()

    Given: Card está em "todo"
    When: update_card_status() é chamado com "in_progress"
    Then: Card deve ser movido para lista "in_progress"
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="todo"))
    adapter.create_list(KanbanList(id="list-2", board_id="board-1", name="in_progress"))

    adapter.create_card(KanbanCard(id="card-1", list_id="list-1", title="Test"))

    # When
    result = adapter.update_card_status("card-1", CardStatus.IN_PROGRESS)

    # Then
    assert result.is_ok
    assert result.value.list_id == "list-2"  # Movido para in_progress


async def test_list_cards_filter_being_processed_deve_filtrar_corretamente(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.list_cards() com filtro being_processed

    Given: Múltiplos cards, alguns sendo processados
    When: list_cards(being_processed=True) é chamado
    Then: Deve retornar apenas cards sendo processados
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="In Progress"))

    adapter.create_card(KanbanCard(id="card-1", list_id="list-1", title="Normal", being_processed=False))
    adapter.create_card(KanbanCard(id="card-2", list_id="list-1", title="Processing", being_processed=True))

    # When
    result = adapter.list_cards(list_id="list-1", being_processed=True)

    # Then
    assert result.is_ok
    cards = result.value
    assert len(cards) == 1
    assert cards[0].id == "card-2"
    assert cards[0].being_processed is True


# =============================================================================
# TESTES: CARD HISTORY
# =============================================================================


async def test_add_card_history_deve_criar_registro_historico(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.add_card_history()

    Given: Card existe
    When: add_card_history() é chamado com evento
    Then: Registro de histórico deve ser criado
    """
    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))
    adapter.create_card(KanbanCard(id="card-1", list_id="list-1", title="Test"))

    # When
    result = adapter.add_card_history(
        "card-1",
        "created",
        metadata={"step": 1, "total": 5},
    )

    # Then
    assert result.is_ok
    assert result.value.event == "created"
    assert result.value.card_id == "card-1"


async def test_get_card_history_deve_retornar_historico_do_card(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.get_card_history()

    Given: Card com histórico de eventos
    When: get_card_history() é chamado
    Then: Deve retornar lista de histórico ordenada por created_at DESC
    """
    # Given: Cria card (já adiciona evento "created")
    card = KanbanCard(
        id="card-history-test",
        list_id="brainstorm",
        title="Card para Histórico",
    )
    adapter.create_card(card)

    # Adiciona evento de movimento manualmente
    adapter.add_card_history("card-history-test", "moved", from_list_id="brainstorm", to_list_id="a-fazer")

    # When: Busca histórico
    result = adapter.get_card_history("card-history-test")

    # Then
    assert result.is_ok
    history = result.value
    assert len(history) >= 2  # created + moved

    # Verifica que ambos eventos existem
    events = [h.event for h in history]
    assert "created" in events
    assert "moved" in events


async def test_create_card_deve_adicionar_historico_created(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.create_card() adiciona histórico

    Given: Card válido
    When: create_card() é chamado
    Then: Evento "created" deve ser adicionado ao histórico
    """
    # Given
    card = KanbanCard(
        id="card-create-history",
        list_id="brainstorm",
        title="Card Teste Create",
        being_processed=True,
    )

    # When
    adapter.create_card(card)

    # Then: Verifica que histórico foi criado
    result = adapter.get_card_history("card-create-history")
    assert result.is_ok
    history = result.value

    # Deve ter pelo menos um evento "created"
    created_events = [h for h in history if h.event == "created"]
    assert len(created_events) >= 1

    # Verifica metadados
    first_created = created_events[0]
    assert first_created.to_list_id == "brainstorm"
    assert first_created.metadata is not None


async def test_update_card_movendo_deve_adicionar_historico_moved(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.update_card() adiciona histórico ao mover

    Given: Card em uma lista
    When: Card é movido para outra lista
    Then: Evento "moved" deve ser adicionado ao histórico
    """
    # Given: Cria card
    card = KanbanCard(
        id="card-move-history",
        list_id="brainstorm",
        title="Card Teste Move",
    )
    adapter.create_card(card)

    # When: Move card para outra lista
    adapter.update_card("card-move-history", list_id="a-fazer")

    # Then: Verifica que histórico "moved" foi criado
    result = adapter.get_card_history("card-move-history")
    assert result.is_ok
    history = result.value

    moved_events = [h for h in history if h.event == "moved"]
    assert len(moved_events) >= 1

    # Verifica from_list_id e to_list_id
    moved = moved_events[0]
    assert moved.from_list_id == "brainstorm"
    assert moved.to_list_id == "a-fazer"


async def test_update_card_being_processed_deve_adicionar_historico_processing(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.update_card() adiciona histórico de processamento

    Given: Card normal
    When: being_processed muda para True
    Then: Evento "processing_started" deve ser adicionado
    """
    # Given: Cria card normal
    card = KanbanCard(
        id="card-processing-history",
        list_id="em-andamento",
        title="Card Teste Processing",
        being_processed=False,
    )
    adapter.create_card(card)

    # When: Marca como sendo processado
    adapter.update_card(
        "card-processing-history",
        being_processed=True,
        processing_job_id="job-123",
        processing_step=1,
        processing_total_steps=5,
    )

    # Then: Verifica que histórico "processing_started" foi criado
    result = adapter.get_card_history("card-processing-history")
    assert result.is_ok
    history = result.value

    processing_events = [h for h in history if h.event == "processing_started"]
    assert len(processing_events) >= 1

    # Verifica metadados
    processing = processing_events[0]
    assert processing.metadata is not None


async def test_update_card_completing_processing_deve_adicionar_historico_completed(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.update_card() adiciona histórico ao completar

    Given: Card sendo processado
    When: being_processed muda para False
    Then: Evento "processing_completed" deve ser adicionado
    """
    # Given: Cria card sendo processado
    card = KanbanCard(
        id="card-complete-history",
        list_id="em-andamento",
        title="Card Teste Complete",
        being_processed=True,
        processing_step=5,
        processing_total_steps=5,
    )
    adapter.create_card(card)

    # When: Marca como não sendo mais processado
    adapter.update_card("card-complete-history", being_processed=False)

    # Then: Verifica que histórico "processing_completed" foi criado
    result = adapter.get_card_history("card-complete-history")
    assert result.is_ok
    history = result.value

    completed_events = [h for h in history if h.event == "processing_completed"]
    assert len(completed_events) >= 1


async def test_delete_card_deve_adicionar_historico_deleted(adapter: SQLiteKanbanAdapter):
    """
    DOC: SQLiteKanbanAdapter.delete_card() adiciona histórico

    Given: Card existe
    When: delete_card() é chamado
    Then: Evento "deleted" deve ser adicionado ao histórico
    """
    # Given: Cria card
    card = KanbanCard(
        id="card-delete-history",
        list_id="brainstorm",
        title="Card Teste Delete",
    )
    adapter.create_card(card)

    # When: Deleta card
    adapter.delete_card("card-delete-history")

    # Then: Verifica que histórico "deleted" foi criado
    result = adapter.get_card_history("card-delete-history")
    assert result.is_ok
    history = result.value

    deleted_events = [h for h in history if h.event == "deleted"]
    assert len(deleted_events) >= 1

    # Verifica metadados contém título
    deleted = deleted_events[0]
    assert deleted.metadata is not None
