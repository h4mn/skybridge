# -*- coding: utf-8 -*-
"""
Domain Entities for Kanban Context.

Cards, Boards, Lists e Labels são conceitos centrais de sistemas Kanban.
Este módulo define as entidades de domínio independentes de implementação.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class CardStatus(Enum):
    """Status possíveis de um Card no fluxo Kanban."""

    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    CHALLENGE = "challenge"  # Fase de desafio/validação adversarial (SPEC009)
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class CardPriority(Enum):
    """Níveis de prioridade para Cards."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Card:
    """
    Card representa uma tarefa/item em um sistema Kanban.

    Attributes:
        id: Identificador único do card (ID externo do provider)
        title: Título breve da tarefa
        description: Descrição detalhada (opcional)
        status: Status atual no fluxo
        priority: Nível de prioridade
        labels: Lista de tags/labels para categorização
        due_date: Data de vencimento (opcional)
        url: Link para o card no sistema externo
        correlation_id: ID de correlação para rastreamento (opcional)
        external_source: Nome do provider externo (trello, github, etc)
        created_at: Timestamp de criação
        updated_at: Timestamp da última atualização
    """

    id: str
    title: str
    description: Optional[str] = None
    status: CardStatus = CardStatus.TODO
    priority: CardPriority = CardPriority.MEDIUM
    labels: list[str] | None = None
    due_date: Optional[datetime] = None
    url: str = ""
    correlation_id: Optional[str] = None
    external_source: str = "unknown"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Inicializa valores padrão."""
        if self.labels is None:
            self.labels = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_blocked(self) -> bool:
        """Verifica se o card está bloqueado."""
        return self.status == CardStatus.BLOCKED

    def is_completed(self) -> bool:
        """Verifica se o card está completo."""
        return self.status == CardStatus.DONE

    def is_overdue(self) -> bool:
        """Verifica se o card está atrasado (tem due_date e já passou)."""
        if self.due_date is None:
            return False
        return datetime.utcnow() > self.due_date

    def add_label(self, label: str) -> None:
        """Adiciona uma label ao card (evita duplicatas)."""
        if label not in self.labels:
            self.labels.append(label)
            self.updated_at = datetime.utcnow()

    def remove_label(self, label: str) -> bool:
        """Remove uma label do card. Retorna True se removeu."""
        if label in self.labels:
            self.labels.remove(label)
            self.updated_at = datetime.utcnow()
            return True
        return False


@dataclass
class Board:
    """
    Board representa um quadro Kanban com múltiplas lists.

    Attributes:
        id: Identificador único do board
        name: Nome do board
        url: Link para o board no sistema externo
        external_source: Nome do provider externo
    """

    id: str
    name: str
    url: str = ""
    external_source: str = "unknown"


@dataclass
class KanbanList:
    """
    List representa uma coluna/lista dentro de um Board Kanban.

    Attributes:
        id: Identificador único da lista
        name: Nome da lista (ex: "To Do", "In Progress")
        position: Posição da lista no board (ordem)
        board_id: ID do board pai
    """

    id: str
    name: str
    position: int = 0
    board_id: str = ""
