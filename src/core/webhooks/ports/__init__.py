# -*- coding: utf-8 -*-
"""
Webhook Ports.

Interfaces (ports) para integração com infraestrutura externa.
Seguindo a arquitetura hexagonal/Clean Architecture.

Ports:
- JobQueuePort: Interface para fila de jobs (in-memory, Redis, etc)
- WebhookSignaturePort: Interface para verificação de assinatura HMAC
"""

from core.webhooks.ports.job_queue_port import JobQueuePort
from core.webhooks.ports.webhook_signature_port import (
    WebhookSignaturePort,
)

__all__ = [
    "JobQueuePort",
    "WebhookSignaturePort",
]
