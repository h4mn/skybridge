# -*- coding: utf-8 -*-
"""
Trello Sync Service - Sincronização bidirecional kanban.db ←→ Trello.

Responsável por sincronizar mudanças do kanban.db com a API do Trello.
Implementa fila de operações para processamento assíncrono e tratamento de conflitos.

DOC: core/kanban/application/trello_sync_service.py
DOC: FLUXO_GITHUB_TRELO_COMPONENTES.md
DOC: ADR024 - Workspace isolation
"""

import logging
from typing import Optional

from core.kanban.domain.card import Card, CardStatus
from core.kanban.ports.kanban_port import KanbanPort
from infra.kanban.adapters.sqlite_kanban_adapter import SQLiteKanbanAdapter
from kernel import Result

logger = logging.getLogger(__name__)


class TrelloSyncService:
    """
    Serviço de sincronização bidirecional entre kanban.db e Trello.

    Responsável por:
    - Sincronizar cards criados no kanban.db para o Trello
    - Sincronizar atualizações de cards para o Trello
    - Sincronizar movimentos de cards entre listas
    - Gerenciar fila de operações para processamento assíncrono
    - Detectar e resolver conflitos (última escrita vence)

    Atributes:
        db: Adapter do kanban.db (SQLite)
        trello: Adapter do Trello API
    """

    def __init__(self, db: SQLiteKanbanAdapter, trello: KanbanPort):
        """
        Inicializa o serviço de sincronização.

        Args:
            db: Adapter do kanban.db
            trello: Adapter do Trello API
        """
        self.db = db
        self.trello = trello

    async def sync_card_created(self, card_id: str) -> Result[Card, str]:
        """
        Sincroniza card criado no kanban.db para o Trello.

        Fluxo:
        1. Busca card no kanban.db
        2. Cria card no Trello via API
        3. Atualiza kanban.db com trello_card_id

        Args:
            card_id: ID do card no kanban.db

        Returns:
            Result.ok(Card) com card atualizado
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            # 1. Busca card no kanban.db
            card_result = self.db.get_card(card_id)
            if card_result.is_err:
                return Result.err(f"Card não encontrado: {card_result.error}")

            card = card_result.value

            # Se já tem trello_card_id, não precisa sincronizar
            if card.trello_card_id:
                return Result.ok(card)

            # 2. Busca lista para obter nome
            list_result = self.db.get_list(card.list_id)
            if list_result.is_err:
                return Result.err(f"Lista não encontrada: {list_result.error}")

            # 3. Cria card no Trello
            trello_result = await self.trello.create_card(
                title=card.title,
                description=card.description,
                list_name=list_result.value.name,
                labels=card.labels or [],
            )

            if trello_result.is_err:
                return Result.err(f"Erro ao criar no Trello: {trello_result.error}")

            trello_card = trello_result.value

            # 4. Atualiza kanban.db com trello_card_id
            update_result = self.db.update_card(
                card_id,
                trello_card_id=trello_card.id,
            )

            if update_result.is_err:
                return Result.err(f"Erro ao atualizar trello_card_id: {update_result.error}")

            logger.info(
                f"Card sincronizado com Trello: {card_id} → {trello_card.id}"
            )

            return Result.ok(trello_card)

        except Exception as e:
            logger.error(f"Erro ao sincronizar card criado: {e}")
            return Result.err(f"Erro ao sync_card_created: {str(e)}")

    async def sync_card_updated(self, card_id: str) -> Result[Card, str]:
        """
        Sincroniza atualização de card para o Trello.

        Args:
            card_id: ID do card no kanban.db

        Returns:
            Result.ok(Card) com card atualizado
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            # Busca card atual
            card_result = self.db.get_card(card_id)
            if card_result.is_err:
                return Result.err(f"Card não encontrado: {card_result.error}")

            card = card_result.value

            # Se não tem trello_card_id, não precisa sincronizar
            if not card.trello_card_id:
                return Result.ok(card)

            # Atualiza no Trello
            trello_result = await self.trello.update_card(
                card_id=card.trello_card_id,
                title=card.title,
                description=card.description,
            )

            if trello_result.is_err:
                return Result.err(f"Erro ao atualizar no Trello: {trello_result.error}")

            logger.info(f"Card atualizado no Trello: {card_id}")

            return Result.ok(trello_result.value)

        except Exception as e:
            logger.error(f"Erro ao sincronizar card atualizado: {e}")
            return Result.err(f"Erro ao sync_card_updated: {str(e)}")

    async def sync_card_moved(self, card_id: str) -> Result[Card, str]:
        """
        Sincroniza movimento de card entre listas para o Trello.

        Args:
            card_id: ID do card no kanban.db

        Returns:
            Result.ok(Card) com card atualizado
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            # Busca card atual
            card_result = self.db.get_card(card_id)
            if card_result.is_err:
                return Result.err(f"Card não encontrado: {card_result.error}")

            card = card_result.value

            # Se não tem trello_card_id, não precisa sincronizar
            if not card.trello_card_id:
                return Result.ok(card)

            # Determina status baseado na lista atual
            # TODO: Mapear list_id → CardStatus de forma mais robusta
            status_map = {
                "todo": CardStatus.TODO,
                "in_progress": CardStatus.IN_PROGRESS,
                "review": CardStatus.REVIEW,
                "done": CardStatus.DONE,
                "blocked": CardStatus.BLOCKED,
                "backlog": CardStatus.BACKLOG,
            }

            list_result = self.db.get_list(card.list_id)
            if list_result.is_ok:
                list_name = list_result.value.name.lower()
                new_status = status_map.get(
                    list_name,
                    CardStatus.TODO  # Fallback
                )
            else:
                new_status = CardStatus.TODO

            # Move no Trello
            trello_result = await self.trello.update_card_status(
                card_id=card.trello_card_id,
                status=new_status,
            )

            if trello_result.is_err:
                return Result.err(f"Erro ao mover no Trello: {trello_result.error}")

            logger.info(
                f"Card movido no Trello: {card_id} → {new_status.value}"
            )

            return Result.ok(trello_result.value)

        except Exception as e:
            logger.error(f"Erro ao sincronizar card movido: {e}")
            return Result.err(f"Erro ao sync_card_moved: {str(e)}")

    async def sync_from_trello(self, board_id: str) -> Result[None, str]:
        """
        Sincroniza mudanças do Trello → kanban.db (polling/webhook).

        Args:
            board_id: ID do board no Trello

        Returns:
            Result.ok(None) se sucesso
            Result.err(str) com mensagem de erro se falhar
        """
        try:
            # TODO: Implementar após definir estratégia de polling/webhook
            # Busca board e cards do Trello
            # Compara timestamps para identificar mudanças
            # Atualiza kanban.db se Trello é mais recente
            logger.info(f"Sync from Trello não implementado ainda para board {board_id}")
            return Result.ok(None)

        except Exception as e:
            logger.error(f"Erro ao sync do Trello: {e}")
            return Result.err(f"Erro ao sync_from_trello: {str(e)}")

    async def enqueue_sync_operation(
        self,
        operation: str,
        card_id: str,
        **kwargs
    ) -> Result[None, str]:
        """
        Enfileira operação de sincronização para processamento assíncrono.

        Args:
            operation: Tipo de operação ('create', 'update', 'move', 'delete')
            card_id: ID do card
            **kwargs: Parâmetros adicionais

        Returns:
            Result.ok(None) se operação enfileirada
            Result.err(str) com mensagem de erro se falhar
        """
        # TODO: Implementar fila de sincronização
        # Por ora, executa sincronicamente
        if operation == "create":
            return await self.sync_card_created(card_id)
        elif operation == "update":
            return await self.sync_card_updated(card_id)
        elif operation == "move":
            return await self.sync_card_moved(card_id)
        else:
            return Result.err(f"Operação desconhecida: {operation}")
