# -*- coding: utf-8 -*-
"""
Kanban Routes — API Kanban (Fase 2: kanban.db como fonte única da verdade).

DOC: runtime/delivery/kanban_routes.py
DOC: PRD024 - Kanban Cards Vivos
DOC: ADR024 - Workspace isolation via X-Workspace header

Implementa API REST completa para Kanban usando kanban.db (SQLite)
como FONTE ÚNICA DA VERDADE.

Fluxo de dados:
    Frontend (Kanban.tsx) → apiClient.get('/kanban/boards')
        → [X-Workspace: core] adicionado automaticamente
        → KanbanRoutes → SQLiteKanbanAdapter → kanban.db
        → Retorna boards/lists/cards

Sincronização:
    kanban.db ←→ TrelloSyncService ←→ Trello API
    kanban.db ←→ KanbanJobEventHandler ←→ JobOrchestrator

Escopo Fase 2:
    ✅ kanban.db como fonte única da verdade
    ✅ CRUD completo (boards, lists, cards)
    ✅ Cards vivos (being_processed)
    ✅ Respeito a workspace ativo (X-Workspace header)
    ✅ Ordenação correta (vivos primeiro)
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status, Query
from pydantic import BaseModel, Field

from core.kanban.domain.database import KanbanBoard, KanbanCard, KanbanList, CardHistory
from core.kanban.application.kanban_initializer import KanbanInitializer
from core.kanban.application.kanban_event_bus import KanbanEventBus
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter


logger = logging.getLogger(__name__)

# ============================================================================
# EventBus Singleton
# ============================================================================

_event_bus = KanbanEventBus.get_instance()


async def _emit_card_event(event_type: str, card: KanbanCard, workspace_id: str) -> None:
    """
    Emite evento de card no EventBus.

    Args:
        event_type: Tipo do evento (card_created, card_updated, card_deleted)
        card: Objeto de domínio do card
        workspace_id: ID do workspace
    """
    card_data = {
        "id": card.id,
        "list_id": card.list_id,
        "title": card.title,
        "description": card.description,
        "position": card.position,
        "labels": card.labels,
        "due_date": card.due_date.isoformat() if card.due_date else None,
        "being_processed": card.being_processed,
        "processing_started_at": card.processing_started_at.isoformat() if card.processing_started_at else None,
        "processing_job_id": card.processing_job_id,
        "processing_step": card.processing_step,
        "processing_total_steps": card.processing_total_steps,
        "processing_progress_percent": card.processing_progress_percent,
        "issue_number": card.issue_number,
        "issue_url": card.issue_url,
        "pr_url": card.pr_url,
        "trello_card_id": card.trello_card_id,
        "created_at": card.created_at.isoformat() if card.created_at else None,
        "updated_at": card.updated_at.isoformat() if card.updated_at else None,
    }
    await _event_bus.publish(event_type, card_data, workspace_id)
    logger.debug(f"[KanbanEvent] Emetiu {event_type} para card {card.id} (workspace={workspace_id})")


# ============================================================================
# Schemas Pydantic
# ============================================================================

from datetime import datetime


def _serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Serializa datetime para ISO format string."""
    return dt.isoformat() if dt else None


class BoardSchema(BaseModel):
    """Schema de board para resposta da API."""
    id: str
    name: str
    trello_board_id: Optional[str] = None
    trello_sync_enabled: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # Serializadores para datetime
    @classmethod
    def from_domain(cls, board) -> "BoardSchema":
        """Cria schema a partir de domain model."""
        return cls(
            id=board.id,
            name=board.name,
            trello_board_id=board.trello_board_id,
            trello_sync_enabled=board.trello_sync_enabled,
            created_at=_serialize_datetime(board.created_at),
            updated_at=_serialize_datetime(board.updated_at),
        )


class ListSchema(BaseModel):
    """Schema de lista para resposta da API."""
    id: str
    board_id: str
    name: str
    position: int
    trello_list_id: Optional[str] = None

    @classmethod
    def from_domain(cls, lst) -> "ListSchema":
        """Cria schema a partir de domain model."""
        return cls(
            id=lst.id,
            board_id=lst.board_id,
            name=lst.name,
            position=lst.position,
            trello_list_id=lst.trello_list_id,
        )


class CardSchema(BaseModel):
    """Schema de card para resposta da API."""
    id: str
    list_id: str
    title: str
    description: Optional[str] = None
    position: int
    labels: list[str] = Field(default_factory=list)
    due_date: Optional[str] = None
    being_processed: bool = False
    processing_started_at: Optional[str] = None
    processing_job_id: Optional[str] = None
    processing_step: int = 0
    processing_total_steps: int = 0
    processing_progress_percent: float = 0.0
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    pr_url: Optional[str] = None
    trello_card_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_domain(cls, card) -> "CardSchema":
        """Cria schema a partir de domain model."""
        return cls(
            id=card.id,
            list_id=card.list_id,
            title=card.title,
            description=card.description,
            position=card.position,
            labels=card.labels or [],
            due_date=_serialize_datetime(card.due_date),
            being_processed=card.being_processed,
            processing_started_at=_serialize_datetime(card.processing_started_at),
            processing_job_id=card.processing_job_id,
            processing_step=card.processing_step,
            processing_total_steps=card.processing_total_steps,
            processing_progress_percent=card.processing_progress_percent,
            issue_number=card.issue_number,
            issue_url=card.issue_url,
            pr_url=card.pr_url,
            trello_card_id=card.trello_card_id,
            created_at=_serialize_datetime(card.created_at),
            updated_at=_serialize_datetime(card.updated_at),
        )


class CreateCardSchema(BaseModel):
    """Schema para criação de card."""
    list_id: str
    title: str
    description: Optional[str] = None
    position: Optional[int] = None
    labels: list[str] = Field(default_factory=list)
    due_date: Optional[str] = None
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    # Cards Vivos - campos de processamento
    being_processed: Optional[bool] = None
    processing_job_id: Optional[str] = None
    processing_step: Optional[int] = None
    processing_total_steps: Optional[int] = None


class UpdateCardSchema(BaseModel):
    """Schema para atualização de card."""
    title: Optional[str] = None
    description: Optional[str] = None
    list_id: Optional[str] = None  # Mover entre listas
    position: Optional[int] = None
    labels: Optional[list[str]] = None
    due_date: Optional[str] = None
    being_processed: Optional[bool] = None
    processing_job_id: Optional[str] = None
    processing_step: Optional[int] = None
    processing_total_steps: Optional[int] = None


class CreateBoardSchema(BaseModel):
    """Schema para criação de board."""
    id: str
    name: str
    trello_board_id: Optional[str] = None
    trello_sync_enabled: bool = False


class CreateListSchema(BaseModel):
    """Schema para criação de lista."""
    id: str
    board_id: str
    name: str
    position: int = 0
    trello_list_id: Optional[str] = None


class CardHistorySchema(BaseModel):
    """Schema de histórico de card para resposta da API."""
    id: Optional[int] = None
    card_id: str
    event: str
    from_list_id: Optional[str] = None
    to_list_id: Optional[str] = None
    metadata: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_domain(cls, history: CardHistory) -> "CardHistorySchema":
        """Cria schema a partir de domain model."""
        return cls(
            id=history.id,
            card_id=history.card_id,
            event=history.event,
            from_list_id=history.from_list_id,
            to_list_id=history.to_list_id,
            metadata=history.metadata,
            created_at=_serialize_datetime(history.created_at),
        )


# ============================================================================
# Router Factory
# ============================================================================

def create_kanban_router() -> APIRouter:
    """
    Cria router de Kanban com suporte a workspaces.

    DOC: ADR024 - Cada workspace tem seu próprio kanban.db.
    DOC: ADR024 - X-Workspace header determina qual kanban.db usar.

    Returns:
        APIRouter configurado com endpoints completos do Kanban
    """
    router = APIRouter(prefix="/kanban", tags=["kanban"])

    # ==========================================================================
    # ENDPOINTS: BOARDS
    # ==========================================================================

    @router.get("/boards", response_model=list[BoardSchema])
    async def get_boards(request: Request) -> list[BoardSchema]:
        """
        Lista todos os boards do Kanban.

        Args:
            request: Request FastAPI (usado para X-Workspace header)

        Returns:
            Lista de boards ordenados por created_at DESC
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            result = adapter.list_boards()
            if result.is_err:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

            return [BoardSchema.from_domain(board) for board in result.value]
        finally:
            adapter.disconnect()

    @router.get("/boards/{board_id}", response_model=BoardSchema)
    async def get_board(request: Request, board_id: str) -> BoardSchema:
        """
        Busca um board específico.

        Args:
            request: Request FastAPI
            board_id: ID do board

        Returns:
            Board solicitado

        Raises:
            HTTPException 404: Board não encontrado
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            result = adapter.get_board(board_id)
            if result.is_err:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )

            return BoardSchema.from_domain(result.value)
        finally:
            adapter.disconnect()

    @router.post("/boards", response_model=BoardSchema, status_code=status.HTTP_201_CREATED)
    async def create_board(request: Request, data: CreateBoardSchema) -> BoardSchema:
        """
        Cria um novo board.

        Args:
            request: Request FastAPI
            data: Dados do board

        Returns:
            Board criado
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            board = KanbanBoard(
                id=data.id,
                name=data.name,
                trello_board_id=data.trello_board_id,
                trello_sync_enabled=data.trello_sync_enabled,
            )
            result = adapter.create_board(board)
            if result.is_err:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

            return BoardSchema.from_domain(result.value)
        finally:
            adapter.disconnect()

    # ==========================================================================
    # ENDPOINTS: LISTS
    # ==========================================================================

    @router.get("/lists", response_model=list[ListSchema])
    async def get_lists(
        request: Request,
        board_id: Optional[str] = None
    ) -> list[ListSchema]:
        """
        Lista listas do Kanban.

        Args:
            request: Request FastAPI
            board_id: Filtrar por board (opcional)

        Returns:
            Lista de listas ordenadas por position ASC
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            if board_id:
                result = adapter.list_lists(board_id)
            else:
                # Busca o primeiro board disponível
                boards_result = adapter.list_boards()
                if boards_result.is_ok and boards_result.value:
                    first_board_id = boards_result.value[0].id
                    result = adapter.list_lists(first_board_id)
                else:
                    result = boards_result  # Propaga erro se não houver boards

            if result.is_err:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

            return [ListSchema.from_domain(lst) for lst in result.value]
        finally:
            adapter.disconnect()

    @router.post("/lists", response_model=ListSchema, status_code=status.HTTP_201_CREATED)
    async def create_list(request: Request, data: CreateListSchema) -> ListSchema:
        """
        Cria uma nova lista.

        Args:
            request: Request FastAPI
            data: Dados da lista

        Returns:
            Lista criada
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            list_obj = KanbanList(
                id=data.id,
                board_id=data.board_id,
                name=data.name,
                position=data.position,
                trello_list_id=data.trello_list_id,
            )
            result = adapter.create_list(list_obj)
            if result.is_err:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

            return ListSchema.from_domain(result.value)
        finally:
            adapter.disconnect()

    # ==========================================================================
    # ENDPOINTS: CARDS
    # ==========================================================================

    @router.get("/cards", response_model=list[CardSchema])
    async def get_cards(
        request: Request,
        list_id: Optional[str] = None,
        being_processed: Optional[bool] = None
    ) -> list[CardSchema]:
        """
        Lista cards do Kanban.

        Cards vivos (being_processed=True) são retornados PRIMEIRO.

        Args:
            request: Request FastAPI
            list_id: Filtrar por lista (opcional)
            being_processed: Filtrar por cards sendo processados (opcional)

        Returns:
            Lista de cards (vivos primeiro, depois por position)
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            result = adapter.list_cards(list_id=list_id, being_processed=being_processed)
            if result.is_err:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

            return [CardSchema.from_domain(card) for card in result.value]
        finally:
            adapter.disconnect()

    @router.get("/cards/{card_id}", response_model=CardSchema)
    async def get_card(request: Request, card_id: str) -> CardSchema:
        """
        Busca um card específico.

        Args:
            request: Request FastAPI
            card_id: ID do card

        Returns:
            Card solicitado

        Raises:
            HTTPException 404: Card não encontrado
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            result = adapter.get_card(card_id)
            if result.is_err:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )

            return CardSchema.from_domain(result.value)
        finally:
            adapter.disconnect()

    @router.post("/cards", response_model=CardSchema, status_code=status.HTTP_201_CREATED)
    async def create_card(request: Request, data: CreateCardSchema) -> CardSchema:
        """
        Cria um novo card.

        Args:
            request: Request FastAPI
            data: Dados do card

        Returns:
            Card criado
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            card = KanbanCard(
                id=data.title.lower().replace(" ", "-"),  # ID simples por enquanto
                list_id=data.list_id,
                title=data.title,
                description=data.description,
                position=data.position or 0,
                labels=data.labels,
                due_date=data.due_date,
                issue_number=data.issue_number,
                issue_url=data.issue_url,
                # Cards Vivos
                being_processed=data.being_processed or False,
                processing_job_id=data.processing_job_id,
                processing_step=data.processing_step or 0,
                processing_total_steps=data.processing_total_steps or 0,
            )
            result = adapter.create_card(card)
            if result.is_err:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

            created_card = result.value

            # Emite evento SSE para clientes conectados
            await _emit_card_event("card_created", created_card, workspace_id)

            return CardSchema.from_domain(created_card)
        finally:
            adapter.disconnect()

    @router.patch("/cards/{card_id}", response_model=CardSchema)
    async def update_card(request: Request, card_id: str, data: UpdateCardSchema) -> CardSchema:
        """
        Atualiza um card (mover entre listas, editar campos).

        Args:
            request: Request FastAPI
            card_id: ID do card
            data: Campos a atualizar

        Returns:
            Card atualizado

        Raises:
            HTTPException 404: Card não encontrado
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            # Monta dicionário de updates (apenas campos não-None)
            updates = {}
            if data.title is not None:
                updates["title"] = data.title
            if data.description is not None:
                updates["description"] = data.description
            if data.list_id is not None:
                updates["list_id"] = data.list_id
            if data.position is not None:
                updates["position"] = data.position
            if data.labels is not None:
                updates["labels"] = data.labels
            if data.due_date is not None:
                updates["due_date"] = data.due_date
            if data.being_processed is not None:
                updates["being_processed"] = data.being_processed
            if data.processing_job_id is not None:
                updates["processing_job_id"] = data.processing_job_id
            if data.processing_step is not None:
                updates["processing_step"] = data.processing_step
            if data.processing_total_steps is not None:
                updates["processing_total_steps"] = data.processing_total_steps

            result = adapter.update_card(card_id, **updates)
            if result.is_err:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

            updated_card = result.value

            # Emite evento SSE para clientes conectados
            await _emit_card_event("card_updated", updated_card, workspace_id)

            return CardSchema.from_domain(updated_card)
        finally:
            adapter.disconnect()

    @router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_card(request: Request, card_id: str) -> None:
        """
        Deleta um card.

        Args:
            request: Request FastAPI
            card_id: ID do card

        Raises:
            HTTPException 404: Card não encontrado
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            # Primeiro busca o card para poder enviar os dados no evento
            card_result = adapter.get_card(card_id)
            if card_result.is_ok:
                card_to_delete = card_result.value
                # Emite evento SSE antes de deletar
                await _emit_card_event("card_deleted", card_to_delete, workspace_id)

            result = adapter.delete_card(card_id)
            if result.is_err:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
        finally:
            adapter.disconnect()

    # ==========================================================================
    # ENDPOINTS: CARD HISTORY
    # ==========================================================================

    @router.get("/cards/{card_id}/history", response_model=list[CardHistorySchema])
    async def get_card_history(request: Request, card_id: str) -> list[CardHistorySchema]:
        """
        Busca histórico de movimentos de um card.

        Args:
            request: Request FastAPI
            card_id: ID do card

        Returns:
            Lista de histórico de movimentos ordenada por created_at DESC
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            result = adapter.get_card_history(card_id)
            if result.is_err:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

            return [CardHistorySchema.from_domain(h) for h in result.value]
        finally:
            adapter.disconnect()

    # ==========================================================================
    # ENDPOINTS: SYNC
    # ==========================================================================

    @router.post("/sync/from-trello")
    async def sync_from_trello(request: Request) -> dict:
        """
        Sincroniza manualmente Trello → kanban.db.

        TODO: Implementar após criar TrelloSyncService completo.

        Args:
            request: Request FastAPI

        Returns:
            Status da sincronização
        """
        # TODO: Implementar
        return {"ok": True, "message": "Sync not implemented yet"}

    @router.post("/initialize")
    async def initialize_kanban(request: Request) -> dict:
        """
        Inicializa o kanban.db com board e listas padrão.

        Args:
            request: Request FastAPI

        Returns:
            Status da inicialização
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)

        initializer = KanbanInitializer(db_path)
        initializer.initialize()

        return {"ok": True, "message": "Kanban initialized", "workspace": workspace_id}

    # ==========================================================================
    # ENDPOINTS SSE (Task 7 PRD024 - Server-Sent Events para Kanban)
    # ==========================================================================

    @router.get("/events")
    async def stream_kanban_events(
        request: Request,
        workspace: Optional[str] = Query(None, description="Workspace ID (query parameter para SSE)")
    ):
        """
        Stream eventos de Kanban em tempo real via SSE.

        DOC: PRD024 Task 7 - SSE para atualizações em tempo real
        DOC: ADR024 - Aceita workspace via query parameter (EventSource não suporta headers)

        Eventos enviados:
        - card_created: Novo card criado
        - card_updated: Card atualizado (movido, editado)
        - card_deleted: Card deletado
        - card_processing_started: Card começou a ser processado por agente
        - card_processing_completed: Card terminou processamento
        - card_processing_failed: Processamento do card falhou

        NOTA: Por enquanto envia heartbeat. Implementação completa requer
        EventBus Kanban específico ou polling do kanban.db.
        """
        from fastapi.responses import StreamingResponse
        import asyncio
        import json

        # Usa workspace do query parameter ou do header
        workspace_id = workspace or request.headers.get("X-Workspace", "core")

        logger.info(f"[KanbanSSE] Cliente conectado (workspace={workspace_id})")

        async def kanban_event_generator():
            """Gerador que entrega eventos de Kanban em tempo real."""
            db_path = _get_kanban_db_path(workspace_id)
            adapter = SQLiteKanbanAdapter(db_path)
            adapter.connect()

            try:
                # Primeiro busca o board padrão para obter board_id
                boards_result = adapter.list_boards()
                if boards_result.is_err or not boards_result.value:
                    # Se não há boards, envia snapshots vazios
                    yield f"event: lists_snapshot\ndata: []\n\n"
                    yield f"event: cards_snapshot\ndata: []\n\n"
                    logger.info(f"[KanbanSSE] Histórico enviado, last_count=0")

                    # Envia heartbeat periodicamente para manter conexão viva
                    iteration = 0
                    while True:
                        yield f": heartbeat {iteration}\n\n"
                        iteration += 1
                        await asyncio.sleep(1)  # Heartbeat a cada segundo

                first_board = boards_result.value[0]

                # Envia estado inicial como eventos history
                lists_result = adapter.list_lists(first_board.id)
                cards_result = adapter.list_cards()

                if lists_result.is_ok and cards_result.is_ok:
                    # Envia lists como evento
                    lists_data = [ListSchema.from_domain(lst) for lst in lists_result.value]
                    yield f"event: lists_snapshot\ndata: {json.dumps([lst.model_dump() for lst in lists_data])}\n\n"

                    # Envia cards como eventos individuais
                    for card in cards_result.value:
                        card_data = CardSchema.from_domain(card)
                        yield f"event: card_snapshot\ndata: {card_data.model_dump_json()}\n\n"

                    logger.info(f"[KanbanSSE] Estado inicial enviado: {len(lists_result.value)} lists, {len(cards_result.value)} cards")

                # Consome eventos do EventBus e envia via SSE
                iteration = 0
                async for event in _event_bus.subscribe(workspace_id):
                    # Envia evento real
                    yield event.to_sse_format()

                    # Envia heartbeat periodicamente
                    iteration += 1
                    if iteration % 10 == 0:  # Heartbeat a cada 10 eventos
                        yield f": heartbeat {iteration}\n\n"

            except Exception as e:
                logger.error(f"[KanbanSSE] Erro no generator: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            finally:
                adapter.disconnect()
                logger.info(f"[KanbanSSE] Cliente desconectado (workspace={workspace_id})")

        return StreamingResponse(
            kanban_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Desabilita buffering em nginx
            }
        )

    # ==========================================================================
    # ENDPOINTS LEGADOS (Fase 1 - compatibilidade)
    # ==========================================================================

    @router.get("/board")
    async def get_kanban_board_legacy(request: Request) -> dict:
        """
        Endpoint legado para compatibilidade com Fase 1.

        Retorna board + cards + lists em formato compatível.

        TODO: Remover após migrar frontend para Fase 2.
        """
        workspace_id = request.headers.get("X-Workspace", "core")
        db_path = _get_kanban_db_path(workspace_id)
        adapter = SQLiteKanbanAdapter(db_path)
        adapter.connect()

        try:
            # Busca board padrão
            boards_result = adapter.list_boards()
            if boards_result.is_err or not boards_result.value:
                return {"ok": True, "board": None, "cards": [], "lists": []}

            board = boards_result.value[0]

            # Busca listas
            lists_result = adapter.list_lists(board.id)
            lists_data = lists_result.value if lists_result.is_ok else []

            # Busca cards
            cards_result = adapter.list_cards()
            cards_data = cards_result.value if cards_result.is_ok else []

            # Converte para formato legado
            from core.kanban.domain.database import KanbanCard
            from datetime import datetime

            return {
                "ok": True,
                "board": {
                    "id": board.id,
                    "name": board.name,
                    "url": ""
                },
                "lists": [
                    {
                        "id": lst.id,
                        "name": lst.name,
                        "position": lst.position
                    }
                    for lst in lists_data
                ],
                "cards": [
                    {
                        "id": card.id,
                        "title": card.title,
                        "description": card.description,
                        "status": "todo",  # TODO: mapear status corretamente
                        "labels": card.labels or [],
                        "due_date": card.due_date.isoformat() if card.due_date else None,
                        "url": "",
                        "list_name": "",  # TODO: buscar nome da lista
                        "created_at": card.created_at.isoformat() if isinstance(card.created_at, datetime) else str(card.created_at)
                    }
                    for card in cards_data
                ]
            }
        finally:
            adapter.disconnect()

    return router


# ============================================================================
# Helpers
# ============================================================================

def _get_kanban_db_path(workspace_id: str) -> Path:
    """
    Retorna o caminho para o kanban.db do workspace.

    DOC: ADR024 - Cada workspace tem seu próprio kanban.db em workspace/{id}/data/

    Args:
        workspace_id: ID do workspace (ex: "core", "trading")

    Returns:
        Path para o kanban.db do workspace
    """
    # ADR024: kanban.db fica em workspace/{workspace_id}/data/kanban.db
    return Path("workspace") / workspace_id / "data" / "kanban.db"
