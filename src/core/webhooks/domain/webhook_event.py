# -*- coding: utf-8 -*-
"""
Webhook Domain Entities.

Entidades de domínio para o contexto de webhooks.
Define a linguagem ubíqua e os invariantes do domínio.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class WebhookSource(Enum):
    """Fontes de webhook suportadas."""

    GITHUB = "github"
    # Phase 2: Adicionar Discord, YouTube, Stripe
    # DISCORD = "discord"
    # YOUTUBE = "youtube"
    # STRIPE = "stripe"


class JobStatus(Enum):
    """Estado de um job de processamento de webhook."""

    PENDING = "pending"
    """Job enfileirado, aguardando processamento."""

    PROCESSING = "processing"
    """Job sendo processado atualmente."""

    COMPLETED = "completed"
    """Job completado com sucesso."""

    FAILED = "failed"
    """Job falhou durante o processamento."""

    CLEANUP_FAILED = "cleanup_failed"
    """Job completou mas falhou cleanup do worktree."""


@dataclass
class WebhookEvent:
    """
    Evento de webhook recebido de uma fonte externa.

    Representa um evento raw recebido via HTTP POST de uma fonte
    como GitHub, Discord, YouTube, etc.

    Attributes:
        source: Fonte do webhook (GitHub, Discord, etc)
        event_type: Tipo do evento (ex: "issues.opened", "message.create")
        event_id: ID único do evento na fonte externa
        payload: Payload completo do evento (JSON)
        received_at: Timestamp de recebimento
        signature: Assinatura HMAC para verificação (se aplicável)
        delivery_id: ID único da entrega (para evitar duplicação)
    """

    source: WebhookSource
    event_type: str
    event_id: str
    payload: dict[str, Any]
    received_at: datetime
    signature: str | None = None
    delivery_id: str | None = None

    def get_issue_number(self) -> int | None:
        """
        Extrai número da issue se for um evento de issue do GitHub.

        Returns:
            Número da issue ou None se não aplicável
        """
        if self.source == WebhookSource.GITHUB and self.event_type.startswith("issues."):
            try:
                return int(self.payload.get("issue", {}).get("number"))
            except (TypeError, ValueError, AttributeError):
                return None
        return None

    def get_repository(self) -> tuple[str, str] | None:
        """
        Extrai informações do repositório se disponível.

        Returns:
            Tupla (owner, repo_name) ou None se não disponível
        """
        repo = self.payload.get("repository")
        if repo:
            owner = repo.get("owner", {}).get("login")
            name = repo.get("name")
            if owner and name:
                return (owner, name)
        return None


@dataclass
class WebhookJob:
    """
    Job em background para processar um WebhookEvent.

    Representa uma unidade de trabalho que será processada
    de forma assíncrona pelo worker.

    Attributes:
        job_id: ID único do job (UUID)
        event: Evento de webhook original
        status: Estado atual do job
        correlation_id: ID de correlação para rastreamento distribuído (derivado de delivery_id)
        worktree_path: Caminho para o worktree isolado (se criado)
        branch_name: Nome da branch criada (se aplicável)
        issue_number: Número da issue (se aplicável)
        initial_snapshot: Snapshot inicial do worktree (antes do trabalho)
        final_snapshot: Snapshot final do worktree (após o trabalho)
        metadata: Metadados adicionais (ex: trello_card_id)
        created_at: Timestamp de criação do job
        started_at: Timestamp de início do processamento
        completed_at: Timestamp de conclusão
        error_message: Mensagem de erro (se falhou)
    """

    job_id: str
    event: WebhookEvent
    status: JobStatus
    correlation_id: str | None = None
    worktree_path: str | None = None
    branch_name: str | None = None
    issue_number: int | None = None
    initial_snapshot: dict[str, Any] | None = None
    final_snapshot: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None

    @classmethod
    def create(cls, event: WebhookEvent) -> "WebhookJob":
        """
        Cria um novo job a partir de um evento.

        Args:
            event: Evento de webhook

        Returns:
            Nova instância de WebhookJob com ID único
        """
        # Usa delivery_id como correlation_id para rastreamento distribuído
        # Se não tiver delivery_id, usa o job_id como fallback
        job_id = f"{event.source.value}-{event.event_type}-{uuid4().hex[:8]}"
        correlation_id = event.delivery_id or job_id

        return cls(
            job_id=job_id,
            event=event,
            status=JobStatus.PENDING,
            correlation_id=correlation_id,
            issue_number=event.get_issue_number(),
        )

    def can_cleanup(self) -> bool:
        """
        Verifica se o worktree pode ser limpo.

        Returns:
            True se o worktree pode ser removido com segurança
        """
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED)

    def mark_processing(self) -> None:
        """Marca o job como em processamento."""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Marca o job como completado com sucesso."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """
        Marca o job como falhou.

        Args:
            error: Mensagem de erro
        """
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error


def generate_worktree_name(job: WebhookJob) -> str:
    """
    Gera nome único para o worktree de um job.

    Args:
        job: Job de webhook

    Returns:
        Nome do worktree (ex: "skybridge-github-225-cf560ba0")

    Note:
        Inclui sufixo do job_id para garantir unicidade mesmo para issues repetidas.
        Permite investigação posterior de tentativas anteriores.
    """
    # Extrai últimos 8 caracteres do job_id como sufixo único
    job_suffix = job.job_id.split("-")[-1] if "-" in job.job_id else job.job_id[:8]

    if job.issue_number:
        return f"skybridge-{job.event.source.value}-{job.issue_number}-{job_suffix}"
    return f"skybridge-{job.event.source.value}-{job.job_id}"


def generate_branch_name(job: WebhookJob) -> str:
    """
    Gera nome único para a branch de um job.

    Args:
        job: Job de webhook

    Returns:
        Nome da branch (ex: "webhook/github/issue/225/cf560ba0")

    Note:
        Inclui sufixo do job_id para garantir unicidade e permitir rastreamento.
        Worktrees de tentativas anteriores são preservados para investigação.
    """
    # Extrai últimos 8 caracteres do job_id como sufixo único
    job_suffix = job.job_id.split("-")[-1] if "-" in job.job_id else job.job_id[:8]

    if job.issue_number:
        return f"webhook/{job.event.source.value}/issue/{job.issue_number}/{job_suffix}"
    return f"webhook/{job.event.source.value}/{job.job_id}"
