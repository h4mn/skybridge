# -*- coding: utf-8 -*-
"""
Testes TDD para TrelloSyncService.

Metodologia: TDD Estrito (PRD023)
- Testes escritos ANTES da implementação
- Testes falham primeiro (RED)
- Implementação mínima para passar (GREEN)
- Refatoração mantendo verde (REFACTOR)

DOC: tests/integration/kanban/test_trello_sync_service.test.py
DOC: core/kanban/application/trello_sync_service.py
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.kanban.domain.database import KanbanBoard, KanbanCard, KanbanList
from core.kanban.domain.card import CardStatus
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter
from kernel import Result


@pytest.fixture
def temp_db():
    """Cria banco temporário para testes."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    db_path.unlink()


@pytest.fixture
def adapter(temp_db):
    """Cria adapter conectado ao banco temporário."""
    adapter = SQLiteKanbanAdapter(temp_db)
    result = adapter.connect()
    assert result.is_ok
    yield adapter
    adapter.disconnect()


@pytest.fixture
def mock_trello_adapter():
    """Mock do TrelloAdapter."""
    mock = AsyncMock()
    return mock


# =============================================================================
# TESTES: Sincronização CREATE
# =============================================================================


async def test_sync_card_created_deve_criar_no_trello_e_atualizar_db(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.sync_card_created()

    Given: Card criado no kanban.db (sem trello_card_id)
    When: sync_card_created() é chamado
    Then: Deve criar card no Trello E atualizar kanban.db com trello_card_id
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService

    # Given: Board, lista e card existem no kanban.db
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    card = KanbanCard(
        id="local-123",
        list_id="list-1",
        title="Test card",
        trello_card_id=None,  # Ainda não sincronizado
    )
    adapter.create_card(card)

    # Mock Trello API
    from core.kanban.domain.card import Card
    mock_trello_adapter.create_card.return_value = Result.ok(
        Card(
            id="trello-456",
            title="Test card",
            url="https://trello.com/c/trello-456"
        )
    )
    mock_trello_adapter.get_list.return_value = Result.ok(KanbanList(id="list-1", board_id="board-1", name="To Do", position=0))

    # When
    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    result = await sync_service.sync_card_created("local-123")

    # Then: Trello foi chamado
    mock_trello_adapter.create_card.assert_called_once_with(
        title="Test card",
        description=None,
        list_name="To Do",
        labels=[]
    )

    # And: kanban.db foi atualizado com trello_card_id
    updated_card = adapter.get_card("local-123")
    assert updated_card.is_ok
    assert updated_card.value.trello_card_id == "trello-456"


async def test_sync_card_created_trello_error_deve_retornar_erro(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.sync_card_created() - Tratamento de erro

    Given: Trello API retorna erro
    When: sync_card_created() é chamado
    Then: Deve retornar Result.err com mensagem de erro
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from kernel import Result

    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    card = KanbanCard(
        id="local-123",
        list_id="list-1",
        title="Test card",
        trello_card_id=None,
    )
    adapter.create_card(card)

    # Mock Trello API retornando erro
    mock_trello_adapter.create_card.return_value = Result.err("Trello API Error")

    # When
    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    result = await sync_service.sync_card_created("local-123")

    # Then
    assert result.is_err
    assert "Trello API Error" in result.error


# =============================================================================
# TESTES: Sincronização UPDATE
# =============================================================================


async def test_sync_card_updated_deve_atualizar_trello(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.sync_card_updated()

    Given: Card atualizado no kanban.db
    When: sync_card_updated() é chamado
    Then: Deve atualizar card no Trello
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from core.kanban.domain.card import Card

    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    card = KanbanCard(
        id="local-123",
        list_id="list-1",
        title="Original Title",
        trello_card_id="trello-456",
    )
    adapter.create_card(card)

    mock_trello_adapter.update_card.return_value = Result.ok(
        Card(id="trello-456", title="Updated Title", url="...")
    )

    # When
    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    result = await sync_service.sync_card_updated("local-123")

    # Then
    assert result.is_ok
    mock_trello_adapter.update_card.assert_called_once()


async def test_sync_card_updated_trello_error_deve_manter_rollback(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.sync_card_updated() - Rollback em caso de erro

    Given: Trello API retorna erro
    When: sync_card_updated() é chamado
    Then: Deve manter card original no kanban.db (rollback)
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService

    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    card = KanbanCard(
        id="local-123",
        list_id="list-1",
        title="Original Title",
        trello_card_id="trello-456",
    )
    adapter.create_card(card)

    mock_trello_adapter.update_card.return_value = Result.err("Trello API Error")

    # When
    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    result = await sync_service.sync_card_updated("local-123")

    # Then
    assert result.is_err

    # Verifica que card não foi alterado no banco
    card_result = adapter.get_card("local-123")
    assert card_result.is_ok
    assert card_result.value.title == "Original Title"


# =============================================================================
# TESTES: Sincronização MOVE (status change)
# =============================================================================


async def test_sync_card_moved_deve_mover_no_trello(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.sync_card_moved()

    Given: Card foi movido para nova lista no kanban.db
    When: sync_card_moved() é chamado
    Then: Deve mover card no Trello
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from core.kanban.domain.card import Card

    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="todo"))
    adapter.create_list(KanbanList(id="list-2", board_id="board-1", name="in_progress"))

    card = KanbanCard(
        id="local-123",
        list_id="list-1",  # Está em "todo"
        title="Test card",
        trello_card_id="trello-456",
    )
    adapter.create_card(card)

    mock_trello_adapter.update_card_status.return_value = Result.ok(
        Card(id="trello-456", title="Test card", status=CardStatus.IN_PROGRESS, url="...")
    )

    # When: Card foi movido para "in_progress" no kanban.db
    adapter.update_card("local-123", list_id="list-2")

    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    result = await sync_service.sync_card_moved("local-123")

    # Then
    assert result.is_ok
    mock_trello_adapter.update_card_status.assert_called_once_with(
        card_id="trello-456",
        status=CardStatus.IN_PROGRESS
    )


# =============================================================================
# TESTES: Fila de sincronização
# =============================================================================


async def test_enqueue_sync_operation_deve_adicionar_na_fila():
    """
    DOC: TrelloSyncService.enqueue_sync_operation()

    Given: Operação de sincronização
    When: enqueue_sync_operation() é chamado
    Then: Deve adicionar operação na fila para processamento assíncrono
    """
    # TODO: Implementar após criar a fila de sincronização
    pass


async def test_process_sync_queue_deve_processar_operacoes_na_ordem():
    """
    DOC: TrelloSyncService.process_sync_queue()

    Given: Fila com múltiplas operações
    When: process_sync_queue() é chamado
    Then: Deve processar operações em ordem FIFO
    """
    # TODO: Implementar após criar a fila de sincronização
    pass


async def test_sync_operation_retry_deve_tentar_novamente_em_caso_de_erro():
    """
    DOC: TrelloSyncService - Retry logic

    Given: Operação falhou com erro temporário
    When: Retry é executado
    Then: Deve tentar novamente até sucesso ou max retries
    """
    # TODO: Implementar após criar lógica de retry
    pass


# =============================================================================
# TESTES: Conflitos e resolução
# =============================================================================


async def test_detect_conflict_deve_identificar_modificacao_simultanea():
    """
    DOC: TrelloSyncService - Detecção de conflitos

    Given: Card modificado tanto no kanban.db quanto no Trello
    When: sync é executado
    Then: Deve detectar conflito e aplicar estratégia de resolução
    """
    # TODO: Implementar após criar lógica de detecção de conflitos
    pass


async def test_resolve_conflict_ultima_escrita_vence():
    """
    DOC: TrelloSyncService - Resolução de conflitos

    Given: Conflito detectado (kanban.db e Trello foram modificados)
    When: resolve_conflict() é chamado
    Then: Deve aplicar estratégia "última escrita vence"
    """
    # TODO: Implementar após criar lógica de resolução de conflitos
    pass
