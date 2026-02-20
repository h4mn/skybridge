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
    When: handler é chamado com board_id correto
    Then: Deve criar card com being_processed=True e position=0 na lista correta
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.job_events import JobStartedEvent

    # Given: Board e lista "Em Andamento" existem
    board_id = "custom-board-123"
    adapter.create_board(KanbanBoard(id=board_id, name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id=board_id, name="Em Andamento", position=0))

    # And: Criar handler com board_id específico (não hardcoded)
    handler = KanbanJobEventHandler(adapter, mock_event_bus, board_id=board_id)

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
    board_id = "custom-board-456"
    adapter.create_board(KanbanBoard(id=board_id, name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id=board_id, name="Em Andamento", position=0))

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

    handler = KanbanJobEventHandler(adapter, mock_event_bus, board_id=board_id)

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


# =============================================================================
# TESTES: Registro de Listeners (Fase 1 - PRD026)
# =============================================================================


async def test_start_deve_registrar_listeners_no_event_bus():
    """
    DOC: PRD026 RF-001 - KanbanJobEventHandler.start() deve registrar listeners

    Given: KanbanJobEventHandler criado
    When: start() é chamado
    Then: Deve registrar 5 listeners no EventBus (IssueReceived, JobStarted, JobCompleted, JobFailed, PRCreated)

    Este é o TESTE CRÍTICO para PRD026 Fase 1 - sem isso, Kanban fica isolado.
    """
    from infra.domain_events.in_memory_event_bus import InMemoryEventBus
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.issue_events import IssueReceivedEvent
    from core.domain_events.job_events import (
        JobStartedEvent,
        JobCompletedEvent,
        JobFailedEvent,
        PRCreatedEvent,
    )

    # Given: Handler com adapter e event_bus
    event_bus = InMemoryEventBus()
    handler = KanbanJobEventHandler(None, event_bus)  # adapter pode ser None para este teste

    # When: start() é chamado
    await handler.start()

    # Then: Deve ter 5 inscrições (ou mais, se houver outros eventos)
    total_subscriptions = event_bus.get_subscription_count()
    assert total_subscriptions >= 5, f"Esperava >= 5 inscrições, obteve {total_subscriptions}"

    # Verifica inscrições específicas
    assert event_bus.get_subscription_count(IssueReceivedEvent) >= 1, "IssueReceivedEvent não tem listener"
    assert event_bus.get_subscription_count(JobStartedEvent) >= 1, "JobStartedEvent não tem listener"
    assert event_bus.get_subscription_count(JobCompletedEvent) >= 1, "JobCompletedEvent não tem listener"
    assert event_bus.get_subscription_count(JobFailedEvent) >= 1, "JobFailedEvent não tem listener"
    assert event_bus.get_subscription_count(PRCreatedEvent) >= 1, "PRCreatedEvent não tem listener"


async def test_stop_deve_cancelar_inscricoes():
    """
    DOC: PRD026 - KanbanJobEventHandler.stop() deve cancelar inscrições

    Given: KanbanJobEventHandler com listeners registrados
    When: stop() é chamado
    Then: Todas as inscrições devem ser removidas
    """
    from infra.domain_events.in_memory_event_bus import InMemoryEventBus
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler

    # Given: Handler com listeners registrados
    event_bus = InMemoryEventBus()
    handler = KanbanJobEventHandler(None, event_bus)
    await handler.start()

    subscriptions_before = event_bus.get_subscription_count()
    assert subscriptions_before >= 5

    # When: stop() é chamado
    await handler.stop()

    # Then: Inscrições devem ser removidas
    subscriptions_after = event_bus.get_subscription_count()
    assert subscriptions_after == 0, f"Esperava 0 inscrições após stop(), obteve {subscriptions_after}"


async def test_issue_received_event_deve_criar_card_na_lista_issues(adapter):
    """
    DOC: PRD026 RF-006 - IssueReceivedEvent deve criar card na lista "Issues"

    Given: IssueReceivedEvent emitido para issue #456
    When: handler é chamado
    Then: Deve criar card na lista "Issues" com metadados da issue
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.issue_events import IssueReceivedEvent
    from infra.domain_events.in_memory_event_bus import InMemoryEventBus

    # Given: Board e lista "Issues" existem
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-issues", board_id="board-1", name="Issues", position=0))

    event_bus = InMemoryEventBus()
    handler = KanbanJobEventHandler(adapter, event_bus)
    await handler.start()  # Registra listeners

    # When: IssueReceivedEvent é publicado
    event = IssueReceivedEvent(
        aggregate_id="issue-456",
        issue_number=456,
        repository="h4mn/skybridge",
        title="Fix bug no Kanban",
        body="Descrição da issue",
        sender="hadst",
        action="opened",
        labels=["bug", "kanban"],
        assignee="sky",
    )

    await event_bus.publish(event)

    # Then: Card deve existir na lista "Issues"
    cards_result = adapter.list_cards(list_id="list-issues")
    assert cards_result.is_ok
    cards = cards_result.value
    assert len(cards) == 1
    assert cards[0].issue_number == 456
    assert cards[0].title == "Fix bug no Kanban"
    assert "h4mn/skybridge" in cards[0].issue_url or cards[0].issue_url == ""


async def test_pr_created_event_deve_guardar_pr_url_no_card(adapter):
    """
    DOC: PRD026 RF-011 - PRCreatedEvent deve guardar pr_url no card

    Given: Card existe para issue #789
    When: PRCreatedEvent é emitido
    Then: Deve atualizar card com pr_url e pr_number
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.job_events import PRCreatedEvent
    from infra.domain_events.in_memory_event_bus import InMemoryEventBus

    # Given: Board, lista e card existem
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="Em Revisão", position=0))

    card = KanbanCard(
        id="card-789",
        list_id="list-1",
        title="Issue #789",
        issue_number=789,
        being_processed=False,
        position=0,
    )
    adapter.create_card(card)

    event_bus = InMemoryEventBus()
    handler = KanbanJobEventHandler(adapter, event_bus)
    await handler.start()

    # When: PRCreatedEvent é publicado
    event = PRCreatedEvent(
        aggregate_id="pr-123",
        pr_number=123,
        issue_number=789,
        repository="h4mn/skybridge",
        pr_url="https://github.com/h4mn/skybridge/pull/123",
        pr_title="Fix: Implementar PRD026",
        branch_name="feature/prd026-kanban-fluxo-real",
    )

    await event_bus.publish(event)

    # Then: Card deve ter pr_url
    card_result = adapter.get_card("card-789")
    assert card_result.is_ok
    updated_card = card_result.value
    assert updated_card.pr_url == "https://github.com/h4mn/skybridge/pull/123"


# =============================================================================
# TESTES: Movimentação de listas (PRD026 Fase 5)
# =============================================================================


async def test_job_completed_event_move_para_em_revisao(adapter):
    """
    DOC: PRD026 RF-010 - JobCompletedEvent deve mover card para "Em Revisão"

    Given: Card está sendo processado em "Em Andamento"
    When: JobCompletedEvent é emitido
    Then: Card deve ser movido para "Em Revisão" e finalizado
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.job_events import JobCompletedEvent
    from infra.domain_events.in_memory_event_bus import InMemoryEventBus

    # Given: Board, listas e card "vivo" em "Em Andamento"
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-progress", board_id="board-1", name="Em Andamento", position=0))
    adapter.create_list(KanbanList(id="list-review", board_id="board-1", name="Em Revisão", position=1))

    card = KanbanCard(
        id="card-123",
        list_id="list-progress",
        title="Issue #123",
        issue_number=123,
        being_processed=True,
        processing_job_id="job-1",
        position=0,
    )
    adapter.create_card(card)

    event_bus = InMemoryEventBus()
    handler = KanbanJobEventHandler(adapter, event_bus)
    await handler.start()

    # When: JobCompletedEvent é publicado
    event = JobCompletedEvent(
        aggregate_id="job-1",
        job_id="job-1",
        issue_number=123,
        repository="h4mn/skybridge",
        files_modified=5,
        duration_seconds=120,
        worktree_path="/path/to/worktree",
    )

    await event_bus.publish(event)

    # Then: Card foi movido para "Em Revisão" e finalizado
    card_result = adapter.get_card("card-123")
    assert card_result.is_ok
    updated_card = card_result.value
    assert updated_card.being_processed is False
    assert updated_card.list_id == "list-review"
    assert updated_card.processing_job_id is None


async def test_job_failed_event_move_para_issues_com_label_erro(adapter):
    """
    DOC: PRD026 RF-012 - JobFailedEvent deve mover card para "Issues" com label erro

    Given: Card está sendo processado em "Em Andamento"
    When: JobFailedEvent é emitido
    Then: Card deve ser movido para "Issues" com label "❌ Erro"
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.job_events import JobFailedEvent
    from infra.domain_events.in_memory_event_bus import InMemoryEventBus

    # Given: Board, listas e card "vivo" em "Em Andamento"
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-progress", board_id="board-1", name="Em Andamento", position=0))
    adapter.create_list(KanbanList(id="list-issues", board_id="board-1", name="Issues", position=1))

    card = KanbanCard(
        id="card-456",
        list_id="list-progress",
        title="Issue #456",
        issue_number=456,
        being_processed=True,
        processing_job_id="job-2",
        position=0,
        labels=["bug"],
    )
    adapter.create_card(card)

    event_bus = InMemoryEventBus()
    handler = KanbanJobEventHandler(adapter, event_bus)
    await handler.start()

    # When: JobFailedEvent é publicado
    event = JobFailedEvent(
        aggregate_id="job-2",
        job_id="job-2",
        issue_number=456,
        repository="h4mn/skybridge",
        error_message="Agent timeout",
        error_type="AgentError",
        duration_seconds=30,
        retry_count=0,
    )

    await event_bus.publish(event)

    # Aguarda processamento do evento (EventBus é assíncrono)
    import asyncio
    await asyncio.sleep(0.1)

    # Then: Card foi movido para "Issues" com label erro e finalizado
    card_result = adapter.get_card("card-456")
    assert card_result.is_ok
    updated_card = card_result.value
    assert updated_card.being_processed is False
    assert updated_card.list_id == "list-issues"
    assert updated_card.processing_job_id is None
    assert "❌ Erro" in updated_card.labels
    assert "bug" in updated_card.labels  # Labels originais são preservados


# =============================================================================
# TESTES: TrelloWebhookReceivedEvent (PRD026 RF-013)
# =============================================================================


async def test_trello_webhook_received_event_deve_mover_card(adapter):
    """
    DOC: PRD026 RF-013 - TrelloWebhookReceivedEvent deve mover card no kanban.db

    Given: Card existe com trello_card_id e webhook chega do Trello
    When: TrelloWebhookReceivedEvent é emitido com movimento para "Em Andamento"
    Then: Card deve ser movido para lista correspondente no kanban.db
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.trello_events import TrelloWebhookReceivedEvent
    from infra.domain_events.in_memory_event_bus import InMemoryEventBus

    # Given: Board, listas e card existem
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-issues", board_id="board-1", name="Issues", position=0))
    adapter.create_list(KanbanList(id="list-progress", board_id="board-1", name="Em Andamento", position=1))

    # Card com trello_card_id
    card = KanbanCard(
        id="card-999",
        list_id="list-issues",
        title="Issue #999",
        issue_number=999,
        being_processed=False,
        position=0,
        trello_card_id="trello-card-abc123",  # <- Importante: vinculado ao Trello
    )
    adapter.create_card(card)

    event_bus = InMemoryEventBus()
    handler = KanbanJobEventHandler(adapter, event_bus)
    await handler.start()

    # When: TrelloWebhookReceivedEvent é publicado (card movido no Trello)
    event = TrelloWebhookReceivedEvent(
        aggregate_id="trello-card-abc123",
        webhook_id="webhook-xyz",
        action_type="updateCard",
        card_id="trello-card-abc123",
        card_name="Issue #999",
        list_before_name="Issues",
        list_after_name="🚧 Em Andamento",  # Card movido para "Em Andamento" no Trello
    )

    await event_bus.publish(event)

    # Aguarda processamento
    import asyncio
    await asyncio.sleep(0.1)

    # Then: Card foi movido para "Em Andamento" no kanban.db
    card_result = adapter.get_card("card-999")
    assert card_result.is_ok
    updated_card = card_result.value
    assert updated_card.list_id == "list-progress", f"Card deveria estar em 'list-progress', está em '{updated_card.list_id}'"
    assert updated_card.trello_card_id == "trello-card-abc123"


async def test_trello_webhook_mapeamento_listas_com_emoji(adapter):
    """
    DOC: PRD026 RF-013 - Mapeamento Trello → Kanban com emoji

    Given: Card com trello_card_id
    When: TrelloWebhookReceivedEvent com lista "🚀 Publicar"
    Then: Card deve ser movido para "Publicar" (sem emoji)

    Verifica mapeamento: "🚧 Em Andamento" → "Em Andamento"
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.trello_events import TrelloWebhookReceivedEvent
    from infra.domain_events.in_memory_event_bus import InMemoryEventBus

    # Given: Board e listas
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-progress", board_id="board-1", name="Em Andamento", position=0))
    adapter.create_list(KanbanList(id="list-publish", board_id="board-1", name="Publicar", position=1))

    card = KanbanCard(
        id="card-888",
        list_id="list-progress",
        title="Issue #888",
        issue_number=888,
        being_processed=False,
        position=0,
        trello_card_id="trello-card-def456",
    )
    adapter.create_card(card)

    event_bus = InMemoryEventBus()
    handler = KanbanJobEventHandler(adapter, event_bus)
    await handler.start()

    # When: Card movido para "🚀 Publicar" no Trello
    event = TrelloWebhookReceivedEvent(
        aggregate_id="trello-card-def456",
        webhook_id="webhook-xyz",
        action_type="updateCard",
        card_id="trello-card-def456",
        card_name="Issue #888",
        list_before_name="🚧 Em Andamento",
        list_after_name="🚀 Publicar",  # Com emoji
    )

    await event_bus.publish(event)

    # Aguarda processamento
    import asyncio
    await asyncio.sleep(0.1)

    # Then: Card movido para "Publicar" (sem emoji)
    card_result = adapter.get_card("card-888")
    assert card_result.is_ok
    updated_card = card_result.value
    assert updated_card.list_id == "list-publish"


async def test_job_started_deve_usar_board_id_configurado_nao_hardcoded(adapter, mock_event_bus):
    """
    DOC: KanbanJobEventHandler deve usar board_id configurado, não "board-1" hardcoded

    REGRA DE OURO: NÃO EXISTE PADRÃO - board_id deve ser explícito.

    Given: KanbanJobEventHandler criado com board_id específico
    When: JobStartedEvent é emitido
    Then: Deve usar o board_id configurado para buscar listas (não "board-1")
    """
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.job_events import JobStartedEvent

    # Given: Dois boards existem com o mesmo nome de lista
    board_custom = "custom-board-789"
    board_hardcoded = "board-1"

    adapter.create_board(KanbanBoard(id=board_custom, name="Custom Board"))
    adapter.create_list(KanbanList(id="list-custom", board_id=board_custom, name="Em Andamento", position=0))

    # Board hardcoded com lista de mesmo nome (para garantir que não usamos board-1)
    adapter.create_board(KanbanBoard(id=board_hardcoded, name="Hardcoded Board"))
    adapter.create_list(KanbanList(id="list-hardcoded", board_id=board_hardcoded, name="Em Andamento", position=0))

    # Handler configurado com board_custom
    handler = KanbanJobEventHandler(adapter, mock_event_bus, board_id=board_custom)

    # When: JobStartedEvent é emitido
    event = JobStartedEvent(
        aggregate_id="job-1",
        job_id="job-1",
        issue_number=999,
        repository="test/repo",
        agent_type="resolve-issue",
    )

    await handler.handle_job_started(event)

    # Then: Card deve ser criado no board_custom, não no board-1
    cards_custom = adapter.list_cards("list-custom")
    cards_hardcoded = adapter.list_cards("list-hardcoded")

    assert cards_custom.is_ok, "Lista custom deveria existir"
    assert cards_hardcoded.is_ok, "Lista hardcoded deveria existir"

    # Card criado no board correto
    assert len(cards_custom.value) == 1, "Deveria ter 1 card no board custom"
    assert len(cards_hardcoded.value) == 0, "Não deveria ter card no board-1 hardcoded"
    assert cards_custom.value[0].issue_number == 999


async def test_start_deve_registrar_trello_webhook_listener():
    """
    DOC: PRD026 RF-013 - start() deve registrar TrelloWebhookReceivedEvent listener

    Given: KanbanJobEventHandler criado
    When: start() é chamado
    Then: Deve registrar listener para TrelloWebhookReceivedEvent
    """
    from infra.domain_events.in_memory_event_bus import InMemoryEventBus
    from core.kanban.application.kanban_job_event_handler import KanbanJobEventHandler
    from core.domain_events.trello_events import TrelloWebhookReceivedEvent

    event_bus = InMemoryEventBus()
    handler = KanbanJobEventHandler(None, event_bus)

    # When: start() é chamado
    await handler.start()

    # Then: Listener registrado para TrelloWebhookReceivedEvent
    assert event_bus.get_subscription_count(TrelloWebhookReceivedEvent) >= 1, \
        "TrelloWebhookReceivedEvent não tem listener"

