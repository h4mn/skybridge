# -*- coding: utf-8 -*-
"""
Domain Models para Kanban Database (SQLite).

Define as models que representam as tabelas do kanban.db,
que é a FONTE ÚNICA DA VERDADE do sistema Kanban Skybridge.

DOC: ADR024 - kanban.db localizado em workspace/skybridge/
DOC: FLUXO_GITHUB_TRELO_COMPONENTES.md - Kanban como fonte da verdade
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class KanbanBoard:
    """
    Modelo de Board Kanban (tabela: boards).

    Attributes:
        id: Identificador único do board (UUID)
        name: Nome do board
        trello_board_id: ID do board no Trello (opcional, para sincronização)
        trello_sync_enabled: Se sincronização com Trello está ativa
        created_at: Timestamp de criação
        updated_at: Timestamp da última atualização
    """

    id: str
    name: str
    trello_board_id: Optional[str] = None
    trello_sync_enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Inicializa timestamps."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


@dataclass
class KanbanList:
    """
    Modelo de Lista Kanban (tabela: lists).

    Attributes:
        id: Identificador único da lista (UUID)
        board_id: ID do board pai
        name: Nome da lista (ex: "To Do", "In Progress")
        position: Posição da lista no board (ordem de exibição)
        trello_list_id: ID da lista no Trello (opcional, para sincronização)
        created_at: Timestamp de criação
        updated_at: Timestamp da última atualização
    """

    id: str
    board_id: str
    name: str
    position: int = 0
    trello_list_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Inicializa timestamps."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


@dataclass
class KanbanCard:
    """
    Modelo de Card Kanban (tabela: cards) - VERSÃO COMPLETA COM "CARDS VIVOS".

    Attributes:
        id: Identificador único do card (UUID)
        list_id: ID da lista onde o card está
        title: Título breve da tarefa
        description: Descrição detalhada (opcional)
        position: Posição do card na lista (ordem de exibição)
        labels: Lista de tags/labels para categorização
        due_date: Data de vencimento (opcional)

        # Campos para "CARDS VIVOS" (agent processing)
        being_processed: Se o card está sendo processado por um agente
        processing_started_at: Timestamp de quando o processamento iniciou
        processing_job_id: ID do job de webhook que está processando
        processing_step: Etapa atual do processamento (1-N)
        processing_total_steps: Total de etapas esperadas

        # Integração com GitHub e Trello
        issue_number: Número da issue no GitHub
        issue_url: URL da issue no GitHub
        pr_url: URL da Pull Request criada
        trello_card_id: ID do card no Trello (para sincronização)

        # Metadados
        created_at: Timestamp de criação
        updated_at: Timestamp da última atualização
    """

    id: str
    list_id: str
    title: str
    description: Optional[str] = None
    position: int = 0
    labels: list[str] | None = None
    due_date: Optional[datetime] = None

    # Cards Vivos - Agent Processing
    being_processed: bool = False
    processing_started_at: Optional[datetime] = None
    processing_job_id: Optional[str] = None
    processing_step: int = 0
    processing_total_steps: int = 0

    # Integração GitHub
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    pr_url: Optional[str] = None

    # Integração Trello
    trello_card_id: Optional[str] = None

    # Metadados
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Inicializa valores padrão."""
        if self.labels is None:
            self.labels = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @property
    def processing_progress_percent(self) -> float:
        """Calcula percentual de progresso do processamento."""
        if self.processing_total_steps == 0:
            return 0.0
        return (self.processing_step / self.processing_total_steps) * 100


@dataclass
class CardHistory:
    """
    Histórico de mudanças de um card (tabela: card_history).

    Attributes:
        id: Identificador único do registro (auto-increment)
        card_id: ID do card
        event: Tipo de evento ('created', 'moved', 'updated', 'processing_started', 'processing_completed')
        from_list_id: ID da lista de origem (para eventos 'moved')
        to_list_id: ID da lista de destino (para eventos 'moved')
        metadata: Metadados adicionais em JSON (opcional)
        created_at: Timestamp do evento
    """

    id: Optional[int] = None
    card_id: str = ""
    event: str = ""
    from_list_id: Optional[str] = None
    to_list_id: Optional[str] = None
    metadata: Optional[str] = None  # JSON string
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Inicializa timestamp."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
