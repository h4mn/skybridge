# -*- coding: utf-8 -*-
"""
Testes TDD para KanbanJobEventHandler.

Metodologia: TDD Estrito (PRD023)
- Testes escritos ANTES da implementação
- Testes falham primeiro (RED)
- Implementação mínima para passar (GREEN)
- Refatoração mantendo verde (REFACTOR)

DOC: tests/integration/kanban/test_kanban_job_event_handler.py
DOC: core/kanban/application/kanban_job_event_handler.py
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from core.kanban.domain.database import KanbanBoard, KanbanCard, KanbanList
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter


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
def mock_event_bus():
    """Mock do EventBus."""
    return AsyncMock()


# =============================================================================
# TESTES: JobStartedEvent → Card "vivo"
# =============================================================================


async def test_job_started_event_deve_criar_card_vivo(adapter, mock_event_bus):
    """
    DOC: KanbanJobEventHandler.handle_job_started()

    Given: JobStartedEvent emitido para issue #123
    When: handler é chamado
    Then: Deve criar card com being_processed=True e position=0
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.job_events import JobStartedEvent

    # Given: Board e lista "Em Andamento" existem
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="Em Andamento", position=0))

    # And: Criar handler
    handler = KanbanJobEventHandler(adapter, mock_event_bus)

    # When: JobStartedEvent é emitido
    event = JobStartedEvent(
        aggregate_id="job-1",
        job_id="job-1",
        issue_number=123,
        repository="h4mn/skybridge",
        agent_type="resolve-issue",
    )

    await handler.handle_job_started(event)

    # Then: Card deve existir com being_processed=True e position=0
    cards_result = adapter.list_cards(list_id="list-1")
    assert cards_result.is_ok
    cards = cards_result.value
    assert len(cards) == 1
    assert cards[0].issue_number == 123
    assert cards[0].being_processed is True
    assert cards[0].position == 0  # Cards vivos ficam no topo
    assert cards[0].processing_job_id == "job-1"


async def test_job_started_event_deve_atualizar_card_existente(adapter, mock_event_bus):
    """
    DOC: KanbanJobEventHandler.handle_job_started() - Card já existe

    Given: Card já existe para issue #123
    When: JobStartedEvent é emitido
    Then: Deve atualizar card existente com being_processed=True
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.job_events import JobStartedEvent

    # Given: Board, lista e card existem
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="Em Andamento", position=0))

    # Card já existe (position=10, being_processed=False)
    existing_card = KanbanCard(
        id="card-123",
        list_id="list-1",
        title="Issue #123",
        issue_number=123,
        being_processed=False,
        position=10,
    )
    adapter.create_card(existing_card)

    handler = KanbanJobEventHandler(adapter, mock_event_bus)

    # When: JobStartedEvent é emitido
    event = JobStartedEvent(
        aggregate_id="job-1",
        job_id="job-1",
        issue_number=123,
        repository="h4mn/skybridge",
        agent_type="resolve-issue",
    )

    await handler.handle_job_started(event)

    # Then: Card deve ser atualizado
    card_result = adapter.get_card("card-123")
    assert card_result.is_ok
    card = card_result.value
    assert card.being_processed is True
    assert card.position == 0  # Card vivo move para o topo
    assert card.processing_job_id == "job-1"


# =============================================================================
# TESTES: JobCompletedEvent → Card normal
# =============================================================================


async def test_job_completed_event_deve_finalizar_card_vivo(adapter, mock_event_bus):
    """
    DOC: KanbanJobEventHandler.handle_job_completed()

    Given: Card está sendo processado (being_processed=True)
    When: JobCompletedEvent é emitido
    Then: Deve atualizar card com being_processed=False
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.job_events import JobCompletedEvent

    # Given: Board, lista e card "vivo" existem
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="Em Andamento", position=0))

    card = KanbanCard(
        id="card-123",
        list_id="list-1",
        title="Issue #123",
        issue_number=123,
        being_processed=True,
        processing_job_id="job-1",
        position=0,
    )
    adapter.create_card(card)

    handler = KanbanJobEventHandler(adapter, mock_event_bus)

    # When: JobCompletedEvent é emitido
    event = JobCompletedEvent(
        aggregate_id="job-1",
        job_id="job-1",
        issue_number=123,
        repository="h4mn/skybridge",
        files_modified=5,
        duration_seconds=120,
        worktree_path="/path/to/worktree",
    )

    await handler.handle_job_completed(event)

    # Then: Card não está mais sendo processado
    card_result = adapter.get_card("card-123")
    assert card_result.is_ok
    card = card_result.value
    assert card.being_processed is False
    assert card.processing_job_id is None


# =============================================================================
# TESTES: JobFailedEvent → Card normal
# =============================================================================


async def test_job_failed_event_deve_finalizar_card_vivo(adapter, mock_event_bus):
    """
    DOC: KanbanJobEventHandler.handle_job_failed()

    Given: Card está sendo processado (being_processed=True)
    When: JobFailedEvent é emitido
    Then: Deve atualizar card com being_processed=False
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.job_events import JobFailedEvent

    # Given: Board, lista e card "vivo" existem
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="Em Andamento", position=0))

    card = KanbanCard(
        id="card-123",
        list_id="list-1",
        title="Issue #123",
        issue_number=123,
        being_processed=True,
        processing_job_id="job-1",
        position=0,
    )
    adapter.create_card(card)

    handler = KanbanJobEventHandler(adapter, mock_event_bus)

    # When: JobFailedEvent é emitido
    event = JobFailedEvent(
        aggregate_id="job-1",
        job_id="job-1",
        issue_number=123,
        repository="h4mn/skybridge",
        error_message="Agent timeout",
        error_type="AgentError",
        duration_seconds=30,
        retry_count=0,
    )

    await handler.handle_job_failed(event)

    # Then: Card não está mais sendo processado
    card_result = adapter.get_card("card-123")
    assert card_result.is_ok
    card = card_result.value
    assert card.being_processed is False
    assert card.processing_job_id is None


# =============================================================================
# TESTES: Mapeamento de listas
# =============================================================================


async def test_agent_type_deve_determinar_lista_destino(adapter, mock_event_bus):
    """
    DOC: KanbanJobEventHandler - Mapeamento agent_type → lista

    Given: Diferentes agent_types
    When: JobStartedEvent é emitido
    Then: Card deve ser criado na lista correta

    Mapeamento:
    - analyze-issue → "Brainstorm"
    - resolve-issue → "Em Andamento"
    - review-issue → "Em Revisão"
    - publish-issue → "Publicar"
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.job_events import JobStartedEvent

    # Given: Board e listas existem
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-brainstorm", board_id="board-1", name="Brainstorm", position=0))
    adapter.create_list(KanbanList(id="list-progress", board_id="board-1", name="Em Andamento", position=1))
    adapter.create_list(KanbanList(id="list-review", board_id="board-1", name="Em Revisão", position=2))
    adapter.create_list(KanbanList(id="list-publish", board_id="board-1", name="Publicar", position=3))

    handler = KanbanJobEventHandler(adapter, mock_event_bus)

    # When: analyze-issue
    event = JobStartedEvent(
        aggregate_id="job-1",
        job_id="job-1",
        issue_number=100,
        repository="h4mn/skybridge",
        agent_type="analyze-issue",
    )
    await handler.handle_job_started(event)

    # Then: Card criado em "Brainstorm"
    cards = adapter.list_cards(list_id="list-brainstorm").value
    assert len(cards) == 1
    assert cards[0].issue_number == 100

    # When: resolve-issue
    event = JobStartedEvent(
        aggregate_id="job-2",
        job_id="job-2",
        issue_number=200,
        repository="h4mn/skybridge",
        agent_type="resolve-issue",
    )
    await handler.handle_job_started(event)

    # Then: Card criado em "Em Andamento"
    cards = adapter.list_cards(list_id="list-progress").value
    assert len(cards) == 1
    assert cards[0].issue_number == 200

    # When: review-issue
    event = JobStartedEvent(
        aggregate_id="job-3",
        job_id="job-3",
        issue_number=300,
        repository="h4mn/skybridge",
        agent_type="review-issue",
    )
    await handler.handle_job_started(event)

    # Then: Card criado em "Em Revisão"
    cards = adapter.list_cards(list_id="list-review").value
    assert len(cards) == 1
    assert cards[0].issue_number == 300

    # When: publish-issue
    event = JobStartedEvent(
        aggregate_id="job-4",
        job_id="job-4",
        issue_number=400,
        repository="h4mn/skybridge",
        agent_type="publish-issue",
    )
    await handler.handle_job_started(event)

    # Then: Card criado em "Publicar"
    cards = adapter.list_cards(list_id="list-publish").value
    assert len(cards) == 1
    assert cards[0].issue_number == 400
