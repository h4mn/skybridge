# -*- coding: utf-8 -*-
"""
Ports (Interfaces) para Kanban Context.

Define os contratos que implementações de infraestrutura devem seguir
para integração com sistemas Kanban externos (Trello, GitHub Projects, etc).
"""

from abc import ABC, abstractmethod
from typing import Optional

from kernel import Result
from core.kanban.domain import Board, Card, CardStatus, KanbanList


class KanbanPort(ABC):
    """
    Interface abstrata para integração com sistemas Kanban.

    Esta interface define o contrato que qualquer adapter (Trello, GitHub, etc)
    deve implementar para fornecer funcionalidades Kanban ao domínio.

    Princípio: O domínio depende de abstrações, não de implementações concretas.
    """

    @abstractmethod
    async def get_card(self, card_id: str) -> Result[Card, str]:
        """
        Busca um card por seu ID.

        Args:
            card_id: ID do card no sistema externo

        Returns:
            Result.ok(Card) se encontrado
            Result.err(str) com mensagem de erro se falhar
        """
        pass

    @abstractmethod
    async def create_card(
        self,
        title: str,
        description: Optional[str] = None,
        list_name: str = "To Do",
        labels: Optional[list[str]] = None,
        due_date: Optional[str] = None,
    ) -> Result[Card, str]:
        """
        Cria um novo card no sistema Kanban.

        Args:
            title: Título do card
            description: Descrição detalhada
            list_name: Nome da lista/coluna onde criar (default: "To Do")
            labels: Lista de labels/tags
            due_date: Data de vencimento (ISO 8601 string)

        Returns:
            Result.ok(Card) com o card criado
            Result.err(str) com mensagem de erro se falhar
        """
        pass

    @abstractmethod
    async def update_card_status(
        self,
        card_id: str,
        status: CardStatus,
        correlation_id: Optional[str] = None,
        target_list_id: Optional[str] = None,
    ) -> Result[Card, str]:
        """
        Atualiza o status de um card.

        Args:
            card_id: ID do card a atualizar
            status: Novo status
            correlation_id: ID opcional para rastreamento
            target_list_id: ID direto da lista no Trello (RECOMENDADO - usa ID direto
                            em vez de buscar por nome para evitar problemas com emojis)

        Returns:
            Result.ok(Card) com o card atualizado
            Result.err(str) com mensagem de erro se falhar
        """
        pass

    @abstractmethod
    async def add_card_comment(
        self,
        card_id: str,
        comment: str,
    ) -> Result[None, str]:
        """
        Adiciona um comentário a um card.

        Args:
            card_id: ID do card
            comment: Texto do comentário

        Returns:
            Result.ok(None) se sucesso
            Result.err(str) com mensagem de erro se falhar
        """
        pass

    @abstractmethod
    async def get_board(self, board_id: str) -> Result[Board, str]:
        """
        Busca um board por seu ID.

        Args:
            board_id: ID do board no sistema externo

        Returns:
            Result.ok(Board) se encontrado
            Result.err(str) com mensagem de erro se falhar
        """
        pass

    @abstractmethod
    async def list_cards(
        self,
        board_id: Optional[str] = None,
        list_name: Optional[str] = None,
        label: Optional[str] = None,
    ) -> Result[list[Card], str]:
        """
        Lista cards com filtros opcionais.

        Args:
            board_id: Filtrar por board específico
            list_name: Filtrar por lista/coluna específica
            label: Filtrar por label específica

        Returns:
            Result.ok(list[Card]) com cards encontrados
            Result.err(str) com mensagem de erro se falhar
        """
        pass
