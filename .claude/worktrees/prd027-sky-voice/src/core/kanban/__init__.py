# -*- coding: utf-8 -*-
"""
Kanban Context - Gestão de tarefas via Trello e similares.

Este bounded context é responsável por:
- Acompanhamento de cards/tasks em sistemas Kanban
- Sincronização de status entre sistemas externos e Skybridge
- Gerenciamento de correlation IDs para rastreamento

Domain: Entidades de domínio (Card, Board, List)
Ports: Interfaces para integração com providers
Application: Casos de uso e orquestração
"""

from core.kanban.domain import (
    Board,
    Card,
    CardPriority,
    CardStatus,
    KanbanList,
)
from core.kanban.ports import KanbanPort

__all__ = [
    # Domain
    "Card",
    "CardStatus",
    "CardPriority",
    "Board",
    "KanbanList",
    # Ports
    "KanbanPort",
]
