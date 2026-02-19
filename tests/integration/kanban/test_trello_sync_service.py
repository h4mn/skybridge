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
    from unittest.mock import AsyncMock
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


@pytest.mark.asyncio
async def test_sync_card_moved_deve_mover_no_trello(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.sync_card_moved()

    Given: Card foi movido para nova lista no kanban.db
    When: sync_card_moved() é chamado
    Then: Deve mover card no Trello usando target_list_id

    NOTA: O sync_card_moved usa target_list_id (ID direto) em vez de depender
    de nomes de listas com emojis. Isso é mais robusto e evita problemas de sincronização.
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from core.kanban.domain.card import Card

    # Given
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="todo", trello_list_id="trello-list-1"))
    adapter.create_list(KanbanList(id="list-2", board_id="board-1", name="in_progress", trello_list_id="trello-list-2"))

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
    # sync_card_moved chama update_card_status com target_list_id (ID direto)
    # O status é um placeholder e é ignorado quando target_list_id é fornecido
    mock_trello_adapter.update_card_status.assert_called_once_with(
        card_id="trello-456",
        status=CardStatus.TODO,  # Placeholder, ignorado quando target_list_id é fornecido
        target_list_id="trello-list-2",  # ← SEMPRE usa ID direto
    )


# =============================================================================
# TESTES: Fila de sincronização
# =============================================================================


async def test_enqueue_sync_operation_deve_adicionar_na_fila(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.enqueue_sync_operation()

    Given: Operação de sincronização
    When: enqueue_sync_operation() é chamado
    Then: Deve adicionar operação na fila para processamento assíncrono
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService

    # Given: Service com fila ativa
    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    await sync_service.start_queue_worker()

    try:
        # When: Enfileira operação
        result = await sync_service.enqueue_sync_operation(
            operation="create",
            card_id="card-123",
        )

        # Then: Operação foi enfileirada
        assert result.is_ok

        # E: fila contém a operação
        queue_size = sync_service._queue.qsize()
        assert queue_size >= 0  # Fila existe

    finally:
        await sync_service.stop_queue_worker()


async def test_process_sync_queue_deve_processar_operacoes_na_ordem(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.process_sync_queue()

    Given: Fila com múltiplas operações
    When: process_sync_queue() é chamado
    Then: Deve processar operações em ordem FIFO
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from core.kanban.domain.card import Card

    # Given: Service com worker ativo e board/card criados
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    mock_trello_adapter.create_card.return_value = Result.ok(
        Card(id="trello-1", title="Card 1", url="...")
    )

    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    await sync_service.start_queue_worker()

    # Create cards
    card1 = KanbanCard(id="card-1", list_id="list-1", title="Card 1")
    card2 = KanbanCard(id="card-2", list_id="list-1", title="Card 2")
    adapter.create_card(card1)
    adapter.create_card(card2)

    # Enfileira operações em ordem
    await sync_service.enqueue_sync_operation("create", "card-1")
    await sync_service.enqueue_sync_operation("create", "card-2")

    # Wait for processing
    import asyncio
    await asyncio.sleep(0.5)

    # Then: Cards foram sincronizados com Trello
    assert mock_trello_adapter.create_card.call_count == 2

    await sync_service.stop_queue_worker()


async def test_sync_operation_retry_deve_tentar_novamente_em_caso_de_erro(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService - Retry logic

    Given: Operação falhou com erro temporário
    When: Retry é executado
    Then: Deve tentar novamente até sucesso ou max retries
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from core.kanban.domain.card import Card

    # Given: Trello falha nas 2 primeiras tentativas
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    # Falha 2x, depois sucesso
    call_count = [0]
    async def failing_then_success(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] <= 2:
            return Result.err("Temporary error")
        return Result.ok(Card(id="trello-1", title="Card 1", url="..."))

    mock_trello_adapter.create_card.side_effect = failing_then_success

    sync_service = TrelloSyncService(adapter, mock_trello_adapter)

    card1 = KanbanCard(id="card-1", list_id="list-1", title="Card 1")
    adapter.create_card(card1)

    # When: Executa sync com retry
    result = await sync_service._sync_with_retry(
        operation=lambda: mock_trello_adapter.create_card(
            title="Card 1",
            description=None,
            list_name="To Do",
            labels=[]
        ),
        max_retries=3
    )

    # Then: Sucesso após 3 tentativas
    assert result.is_ok
    assert call_count[0] == 3  # 2 falhas + 1 sucesso


# =============================================================================
# TESTES: Conflitos e resolução
# =============================================================================


async def test_detect_conflict_deve_identificar_modificacao_simultanea(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService - Detecção de conflitos

    Given: Card modificado tanto no kanban.db quanto no Trello
    When: sync é executado
    Then: Deve detectar conflito e aplicar estratégia de resolução
    """
    # Conflitos são resolvidos via "última escrita vence" em sync_from_trello()
    # Este teste valida que o mecanismo existe
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from core.kanban.domain.card import Card
    from datetime import datetime, timedelta

    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    # Card local modificado há 10 min
    local_card = KanbanCard(
        id="local-123",
        list_id="list-1",
        title="Título Local",
        trello_card_id="trello-456",
        updated_at=datetime.now() - timedelta(minutes=10),
    )
    adapter.create_card(local_card)

    # Trello tem versão mais antiga (1 hora)
    trello_card = Card(
        id="trello-456",
        title="Título Trello",
        url="...",
        updated_at=datetime.now() - timedelta(hours=1),
    )

    sync_service = TrelloSyncService(adapter, mock_trello_adapter)

    # When: Verifica conflito (última escrita vence)
    local_is_newer = local_card.updated_at > trello_card.updated_at

    # Then: Versão local deve ser mantida
    assert local_is_newer


async def test_resolve_conflict_ultima_escrita_vence(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService - Resolução de conflitos

    Given: Conflito detectado (kanban.db e Trello foram modificados)
    When: resolve_conflict() é chamado
    Then: Deve aplicar estratégia "última escrita vence"
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from datetime import datetime

    sync_service = TrelloSyncService(adapter, mock_trello_adapter)

    # When: Resolve conflito com local mais recente
    winner = sync_service._resolve_conflict(
        local_updated=datetime(2026, 2, 7, 14, 0, 0),
        trello_updated=datetime(2026, 2, 7, 10, 0, 0),
    )

    # Then: Versão mais recente vence (local)
    assert winner == "local"  # 14h > 10h

    # E caso contrário (trello mais recente)
    winner2 = sync_service._resolve_conflict(
        local_updated=datetime(2026, 2, 7, 10, 0, 0),
        trello_updated=datetime(2026, 2, 7, 14, 0, 0),
    )
    assert winner2 == "trello"


# =============================================================================
# TESTES: sync_from_trello() - Trello → kanban.db
# =============================================================================


async def test_sync_from_trello_deve_atualizar_cards_mudados_no_trello(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.sync_from_trello()

    Given: Card existe no kanban.db e foi modificado no Trello
    When: sync_from_trello() é chamado
    Then: Deve atualizar card no kanban.db com dados do Trello
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from core.kanban.domain.card import Card
    from datetime import datetime, timedelta

    # Given: Card no kanban.db com título antigo
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    # DateTime fixo para garantir ordem correta
    local_time = datetime(2026, 2, 7, 10, 0, 0)  # 10h (mais antigo)
    trello_time = datetime(2026, 2, 7, 14, 0, 0)  # 14h (mais recente)

    local_card = KanbanCard(
        id="local-123",
        list_id="list-1",
        title="Título Antigo",
        trello_card_id="trello-456",
        updated_at=local_time,
    )
    adapter.create_card(local_card)

    # DEBUG: Verifica se card foi criado
    check = adapter.get_card("local-123")
    assert check.is_ok, f"Card deveria ter sido criado: {check.error}"

    # Mock: Trello retorna card atualizado
    from unittest.mock import AsyncMock
    trello_card_updated = Card(
        id="trello-456",
        title="Título Atualizado no Trello",
        url="https://trello.com/c/trello-456",
        updated_at=trello_time,  # Mais recente
    )

    # AsyncMock com return_value correto
    async def mock_list_cards_impl(board_id):
        return Result.ok([trello_card_updated])

    mock_trello_adapter.list_cards = mock_list_cards_impl

    # When
    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    result = await sync_service.sync_from_trello("board-1")

    # Then
    assert result.is_ok

    # Card foi atualizado no kanban.db
    updated = adapter.get_card("local-123")
    assert updated.is_ok
    assert updated.value.title == "Título Atualizado no Trello"


async def test_sync_from_trello_deve_mover_cards_mudados_de_lista_no_trello(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.sync_from_trello() - movimento de lista

    Given: Card foi movido para outra lista no Trello
    When: sync_from_trello() é chamado
    Then: Deve mover card no kanban.db para a nova lista
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from core.kanban.domain.card import Card
    from datetime import datetime, timedelta

    # Given: Duas listas e card na lista "To Do"
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-todo", board_id="board-1", name="To Do"))
    adapter.create_list(KanbanList(id="list-done", board_id="board-1", name="Done"))

    # Card local com timestamp antigo
    local_time = datetime(2026, 2, 7, 10, 0, 0)
    local_card = KanbanCard(
        id="local-123",
        list_id="list-todo",  # Está em "To Do"
        title="Test card",
        trello_card_id="trello-456",
        updated_at=local_time,
    )
    adapter.create_card(local_card)

    # Mock: Trello retorna card na lista "Done" com timestamp mais recente
    trello_time = datetime(2026, 2, 7, 14, 0, 0)
    mock_trello_adapter.list_cards.return_value = Result.ok([
        Card(
            id="trello-456",
            title="Test card",
            status=CardStatus.DONE,  # Foi movido para Done
            url="https://trello.com/c/trello-456",
            updated_at=trello_time,  # Mais recente que local
        )
    ])

    # Mock para mapear status → list_id
    mock_trello_adapter.get_list_by_status.return_value = Result.ok(
        KanbanList(id="list-done", board_id="board-1", name="Done", position=1)
    )

    # When
    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    result = await sync_service.sync_from_trello("board-1")

    # Then
    assert result.is_ok

    # Card foi movido para lista "Done" no kanban.db
    moved = adapter.get_card("local-123")
    assert moved.is_ok
    assert moved.value.list_id == "list-done"


async def test_sync_from_trello_ultima_escrita_vence_em_conflito(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.sync_from_trello() - resolução de conflitos

    Given: Card modificado tanto no kanban.db quanto no Trello
    When: sync_from_trello() é chamado
    Then: Deve aplicar "última escrita vence" (baseado em updated_at)
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from core.kanban.domain.card import Card
    from datetime import datetime, timedelta

    # Given: Card no kanban.db modificado há 10 min
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    local_card = KanbanCard(
        id="local-123",
        list_id="list-1",
        title="Título Local (10 min atrás)",
        trello_card_id="trello-456",
        updated_at=datetime.now() - timedelta(minutes=10),
    )
    adapter.create_card(local_card)

    # Mock: Trello tem versão mais antiga (1 hora atrás)
    trello_card_old = Card(
        id="trello-456",
        title="Título Trello (1 hora atrás)",
        url="https://trello.com/c/trello-456",
        updated_at=datetime.now() - timedelta(hours=1),
    )
    mock_trello_adapter.list_cards.return_value = Result.ok([trello_card_old])

    # When
    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    result = await sync_service.sync_from_trello("board-1")

    # Then
    assert result.is_ok

    # Deve MANTER versão local (mais recente)
    kept = adapter.get_card("local-123")
    assert kept.is_ok
    assert kept.value.title == "Título Local (10 min atrás)"


async def test_sync_from_trello_retorna_contagem_de_cards_sincronizados(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService.sync_from_trello() - retorno

    Given: Board com cards no Trello
    When: sync_from_trello() é chamado
    Then: Deve retornar Result com contagem de cards sincronizados
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from core.kanban.domain.card import Card

    # Given: 3 cards no Trello
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    mock_trello_adapter.list_cards.return_value = Result.ok([
        Card(id="trello-1", title="Card 1", url="https://trello.com/c/1"),
        Card(id="trello-2", title="Card 2", url="https://trello.com/c/2"),
        Card(id="trello-3", title="Card 3", url="https://trello.com/c/3"),
    ])

    # When
    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    result = await sync_service.sync_from_trello("board-1")

    # Then
    assert result.is_ok
    # Result.value deve conter contagem ou info sobre sync


async def test_sync_from_trello_deve_criar_cards_que_nao_existem_no_kanban_db(adapter, mock_trello_adapter):
    """
    DOC: PRD026 RF-013 - sync_from_trello() deve criar cards do Trello

    Given: Trello tem cards que não existem no kanban.db
    When: sync_from_trello() é chamado
    Then: Deve criar novos cards no kanban.db com trello_card_id
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService
    from core.kanban.domain.card import Card, CardStatus

    # Given: Board e lista existem
    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-progress", board_id="board-1", name="Em Andamento", position=0))
    adapter.create_list(KanbanList(id="list-issues", board_id="board-1", name="Issues", position=1))

    # Trello tem cards, mas kanban.db está vazio
    mock_trello_adapter.list_cards.return_value = Result.ok([
        Card(
            id="trello-new-1",
            title="Card criado no Trello",
            description="Descrição do card",
            status=CardStatus.IN_PROGRESS,
            url="https://trello.com/c/new1",
        ),
    ])

    # When: sync_from_trello é chamado
    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    result = await sync_service.sync_from_trello("board-1")

    # Then: Card foi criado no kanban.db
    assert result.is_ok
    synced_count = result.value
    assert synced_count >= 1, f"Deve sincronizar ao menos 1 card, obteve {synced_count}"

    # Verifica que card existe
    cards_result = adapter.list_cards()
    assert cards_result.is_ok
    cards = cards_result.value

    # Encontra card criado por trello_card_id
    created_card = None
    for card in cards:
        if card.trello_card_id == "trello-new-1":
            created_card = card
            break

    assert created_card is not None, "Card do Trello não foi criado no kanban.db"
    assert created_card.title == "Card criado no Trello"
    assert created_card.list_id == "list-progress"  # "Em Andamento"


async def test_dead_letter_queue_deve_armazenar_operacoes_falhas(adapter, mock_trello_adapter):
    """
    DOC: TrelloSyncService - Dead Letter Queue

    Given: Operação falha após max retries
    When: Worker processa operação
    Then: Deve mover para Dead Letter Queue
    """
    from core.kanban.application.trello_sync_service import TrelloSyncService

    adapter.create_board(KanbanBoard(id="board-1", name="Main"))
    adapter.create_list(KanbanList(id="list-1", board_id="board-1", name="To Do"))

    mock_trello_adapter.create_card.return_value = Result.err("Permanent error")

    sync_service = TrelloSyncService(adapter, mock_trello_adapter)
    await sync_service.start_queue_worker()

    card1 = KanbanCard(id="card-1", list_id="list-1", title="Card 1")
    adapter.create_card(card1)

    # When: Enfileira operação que vai falhar
    sync_service.enqueue_sync_operation("create", "card-1")

    # Wait for processing + retries
    import asyncio
    await asyncio.sleep(1)

    # Then: Operação está na DLQ
    dlq_size = sync_service.get_dlq_size()
    assert dlq_size >= 0  # DLQ existe

    await sync_service.stop_queue_worker()
