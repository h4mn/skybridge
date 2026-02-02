# -*- coding: utf-8 -*-
"""
Kanban Routes — API de visualização Kanban (Fase 1: Leitura).

DOC: runtime/delivery/kanban_routes.py - GET /api/kanban/board
DOC: ADR024 - Workspace isolation via X-Workspace header

Implementa visualização Kanban em modo leitura que reflete o estado
atual do board Trello, respeitando o isolamento de workspaces.

Fluxo de dados:
    Frontend (Kanban.tsx) → useQuery(['kanban-board'])
        → apiClient.get('/kanban/board')
        → [X-Workspace: core] adicionado automaticamente
        → WorkspaceMiddleware carrega .env do workspace
        → kanban_routes.get_kanban_board()
        → TrelloAdapter → API Trello
        → Retorna board + cards + lists
        → Frontend renderiza colunas com cards

Escopo Fase 1:
    ✅ Apenas leitura (sem drag & drop)
    ✅ Espelho do Trello
    ✅ Cards organizados por lista/coluna
    ✅ Respeito a workspace ativo (X-Workspace header)
    ❌ SEM criação/edição de cards
    ❌ SEM drag & drop (Fase 2)
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from core.kanban.domain import CardStatus
from infra.kanban.adapters.trello_adapter import TrelloAdapter
from kernel import Result
from runtime.config.config import get_trello_config


logger = logging.getLogger(__name__)


# ============================================================================
# Schemas Pydantic
# ============================================================================

class KanbanBoardSchema(BaseModel):
    """Schema do board Trello."""
    id: str
    name: str
    url: str


class KanbanCardSchema(BaseModel):
    """Schema de card Kanban."""
    id: str
    title: str
    description: Optional[str] = None
    status: str = Field(..., description="CardStatus: backlog, todo, in_progress, review, done, blocked, challenge")
    labels: list[str] = Field(default_factory=list)
    due_date: Optional[str] = None
    url: str
    list_name: str = Field(..., description="Nome da lista Trello original")
    created_at: Optional[str] = None


class KanbanListSchema(BaseModel):
    """Schema de lista Kanban."""
    id: str
    name: str
    position: int


class KanbanBoardResponse(BaseModel):
    """Resposta do endpoint /api/kanban/board."""
    ok: bool
    board: Optional[KanbanBoardSchema] = None
    cards: list[KanbanCardSchema] = Field(default_factory=list)
    lists: list[KanbanListSchema] = Field(default_factory=list)
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Resposta de erro."""
    ok: bool = False
    error: str


# ============================================================================
# Router Factory
# ============================================================================

def _create_trello_adapter(api_key: str, api_token: str, board_id: str) -> TrelloAdapter:
    """
    Factory function para criar TrelloAdapter.

    Esta função pode ser mockeada em testes para isolar a lógica do endpoint.

    Args:
        api_key: API Key do Trello
        api_token: Token de autenticação
        board_id: ID do board padrão

    Returns:
        TrelloAdapter instanciado
    """
    return TrelloAdapter(api_key=api_key, api_token=api_token, board_id=board_id)


def create_kanban_router(
    trello_adapter_factory: Optional[callable] = None
) -> APIRouter:
    """
    Cria router de Kanban com injeção de dependências.

    DOC: ADR024 - Usa get_trello_config() que lê do workspace ativo.
    DOC: ADR024 - X-Workspace header determina qual .env usar.

    Args:
        trello_adapter_factory: Factory function para criar TrelloAdapter
            (opcional, usa _create_trello_adapter por padrão)
            Útil para testes, pode-se passar um mock.

    Returns:
        APIRouter configurado com endpoint /kanban/board
    """
    # Usa factory padrão se não fornecida
    adapter_factory = trello_adapter_factory or _create_trello_adapter

    router = APIRouter(prefix="/kanban", tags=["kanban"])

    @router.get("/board", response_model=KanbanBoardResponse)
    async def get_kanban_board(request: Request) -> KanbanBoardResponse:
        """
        Busca board Kanban do Trello.

        DOC: runtime/delivery/kanban_routes.py - GET /api/kanban/board

        Retorna board + cards + lists do Trello configurado no workspace.
        Cards são mapeados com base nas listas do board usando o cache
        de status do TrelloAdapter.

        Args:
            request: Request FastAPI (usado para X-Workspace header)

        Returns:
            KanbanBoardResponse com board + cards + lists

        Raises:
            HTTPException 503: Trello não configurado
            HTTPException 500: Erro na API Trello
        """
        # Busca configuração do Trello (do workspace ativo via ADR024)
        trello_config = get_trello_config()

        # Verifica se Trello está configurado
        if not trello_config or not trello_config.is_valid():
            logger.warning("Trello não configurado: credenciais ausentes")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trello not configured. Set TRELLO_API_KEY, TRELLO_API_TOKEN, and TRELLO_BOARD_ID."
            )

        # Cria adapter Trello via factory (testável)
        try:
            trello_adapter = adapter_factory(
                api_key=trello_config.api_key,
                api_token=trello_config.api_token,
                board_id=trello_config.board_id
            )
        except Exception as e:
            logger.error(f"Erro ao criar TrelloAdapter: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Trello configuration error: {str(e)}"
            )

        # Busca board
        board_result = await trello_adapter.get_board(trello_config.board_id)
        if board_result.is_err:
            logger.error(f"Erro ao buscar board Trello: {board_result.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching Trello board: {board_result.error}"
            )

        board = board_result.value

        # Inicializa cache de status (mapeamento listas → CardStatus)
        cache_result = await trello_adapter.initialize_status_cache(trello_config.board_id)
        if cache_result.is_err:
            logger.error(f"Erro ao inicializar cache de status: {cache_result.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error initializing status cache: {cache_result.error}"
            )

        # Busca cards do board
        cards_result = await trello_adapter.list_cards(board_id=trello_config.board_id)
        if cards_result.is_err:
            logger.error(f"Erro ao buscar cards Trello: {cards_result.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching Trello cards: {cards_result.error}"
            )

        cards = cards_result.value

        # Busca listas do board (para retornar no response)
        lists_result = await _fetch_board_lists(trello_adapter, trello_config.board_id)
        if lists_result.is_err:
            logger.error(f"Erro ao buscar listas Trello: {lists_result.error}")
            # Não falha o endpoint se listas falharem
            board_lists = []
        else:
            board_lists = lists_result.value

        # Mapeia cards para schema
        card_schemas = []
        for card in cards:
            # Card do domínio já tem status mapeado
            # Não precisamos buscar via cache de listas
            card_schema = KanbanCardSchema(
                id=card.id,
                title=card.title,
                description=card.description,
                status=card.status.value,
                labels=card.labels or [],
                due_date=card.due_date.isoformat() if card.due_date else None,
                url=card.url,
                list_name="",  # Card do domínio não tem list_name, deixamos vazio por ora
                created_at=card.created_at.isoformat() if card.created_at else None
            )
            card_schemas.append(card_schema)

        # Mapeia listas para schema
        list_schemas = []
        for lst in board_lists:
            list_schema = KanbanListSchema(
                id=lst["id"],
                name=lst["name"],
                position=lst.get("pos", 0)
            )
            list_schemas.append(list_schema)

        # Mapeia board para schema
        board_schema = KanbanBoardSchema(
            id=board.id,
            name=board.name,
            url=board.url
        )

        return KanbanBoardResponse(
            ok=True,
            board=board_schema,
            cards=card_schemas,
            lists=list_schemas
        )

    return router


# ============================================================================
# Helpers
# ============================================================================

async def _fetch_board_lists(trello_adapter: TrelloAdapter, board_id: str) -> Result[list[dict], str]:
    """
    Busca listas do board Trello.

    Args:
        trello_adapter: Adapter Trello configurado
        board_id: ID do board

    Returns:
        Result com lista de listas ou erro
    """
    try:
        response = await trello_adapter._client.get(f"/boards/{board_id}/lists")
        response.raise_for_status()
        return Result.ok(response.json())
    except Exception as e:
        return Result.err(f"Error fetching lists: {str(e)}")


def _map_card_status(trello_adapter: TrelloAdapter, list_id: str) -> CardStatus:
    """
    Mapeia ID da lista Trello para CardStatus.

    Usa o cache populado por initialize_status_cache().

    Args:
        trello_adapter: Adapter com cache de status inicializado
        list_id: ID da lista Trello

    Returns:
        CardStatus correspondente (fallback: TODO)
    """
    # Tenta buscar do cache
    if list_id in trello_adapter._list_status_cache:
        return trello_adapter._list_status_cache[list_id]

    # Fallback: TODO se não encontrou
    logger.warning(f"Lista {list_id} não encontrada no cache, usando TODO como fallback")
    return CardStatus.TODO
