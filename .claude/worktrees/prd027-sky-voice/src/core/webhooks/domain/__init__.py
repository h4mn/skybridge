# -*- coding: utf-8 -*-
"""
Webhook Domain Layer.

Este módulo contém as entidades de domínio do contexto de webhooks,
seguindo os princípios de Domain-Driven Design (ADR002).

Linguagem Ubíquita:
- WebhookEvent: Evento recebido de uma fonte externa (GitHub, Discord, etc)
- WebhookJob: Job em background para processar um WebhookEvent
- JobStatus: Estado do job (pending, processing, completed, failed)
"""

from core.webhooks.domain.webhook_event import (
    WebhookSource,
    WebhookEvent,
    WebhookJob,
    JobStatus,
    generate_worktree_name,
    generate_branch_name,
)
from .autonomy_level import AutonomyLevel  # noqa: E402

__all__ = [
    "WebhookSource",
    "WebhookEvent",
    "WebhookJob",
    "JobStatus",
    "generate_worktree_name",
    "generate_branch_name",
    "AutonomyLevel",
]
