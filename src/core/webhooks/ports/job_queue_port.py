# -*- coding: utf-8 -*-
"""
Job Queue Port.

Interface abstrata para fila de processamento de webhooks.
Permite trocar a implementação (in-memory → Redis) sem alterar
o código de domínio.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.webhooks.domain import WebhookJob


class JobQueuePort(ABC):
    """
    Port para fila de jobs de processamento de webhook.

    Implementações:
    - InMemoryJobQueue: Fila em memória (MVP, Phase 1)
    - RedisJobQueue: Fila persistente em Redis (Phase 3)

    A fila garante processamento assíncrono dos webhooks recebidos,
    permitindo que o endpoint HTTP retorne 202 Accepted rapidamente.
    """

    @abstractmethod
    async def enqueue(self, job: "WebhookJob") -> str:
        """
        Adiciona job à fila para processamento.

        Args:
            job: Job a ser enfileirado

        Returns:
            job_id do job enfileirado

        Raises:
            QueueError: Se falhar ao enfileirar
        """
        pass

    @abstractmethod
    async def dequeue(self) -> "WebhookJob | None":
        """
        Remove próximo job da fila para processamento.

        Returns:
            Próximo job ou None se fila vazia

        Raises:
            QueueError: Se falhar ao desenfileirar
        """
        pass

    @abstractmethod
    async def get_job(self, job_id: str) -> "WebhookJob | None":
        """
        Busca job por ID.

        Args:
            job_id: ID do job

        Returns:
            Job encontrado ou None
        """
        pass

    @abstractmethod
    async def complete(self, job_id: str, result: dict | None = None) -> None:
        """
        Marca job como completado com sucesso.

        Args:
            job_id: ID do job
            result: Resultado opcional do processamento
        """
        pass

    @abstractmethod
    async def fail(self, job_id: str, error: str) -> None:
        """
        Marca job como falhou.

        Args:
            job_id: ID do job
            error: Mensagem de erro
        """
        pass

    @abstractmethod
    def size(self) -> int:
        """
        Retorna tamanho atual da fila.

        Returns:
            Número de jobs aguardando processamento
        """
        pass

    @abstractmethod
    async def exists_by_delivery(self, delivery_id: str) -> bool:
        """
        Verifica se já existe job com este delivery ID.

        Args:
            delivery_id: ID único da entrega do webhook

        Returns:
            True se job com este delivery_id já existe, False caso contrário
        """
        pass

    async def update_metadata(self, job_id: str, metadata: dict[str, object]) -> None:
        """
        Atualiza metadata de um job (opcional, implementação default).

        Implementações podem sobrescrever para persistir metadata adicional
        como worktree_path, branch_name, etc.

        Args:
            job_id: ID do job
            metadata: Novo metadata (será mesclado com o existente)
        """
        # Implementação default não-faz-nada (para filas em memória)
        pass


class QueueError(Exception):
    """Erro na operação da fila."""

    pass
