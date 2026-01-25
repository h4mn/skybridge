# -*- coding: utf-8 -*-
"""
Job Queue Factory - Factory Pattern for Job Queue Providers.

PRD018 Fase 2 - INFRA-09: Migration e Factory.

Cria a instância apropriada de JobQueue baseado na configuração.
"""

from __future__ import annotations

import logging
from typing import Literal

from core.webhooks.ports.job_queue_port import JobQueuePort

logger = logging.getLogger(__name__)

# Type alias para os providers disponíveis
JobQueueProvider = Literal["dragonfly", "redis", "sqlite", "file"]


class JobQueueFactory:
    """
    Factory para criar instâncias de JobQueue.

    Suporta múltiplos providers:
    - sqlite: SQLiteJobQueue (recomendado, zero dependências)
    - dragonfly: RedisJobQueue (DragonflyDB)
    - redis: RedisJobQueue (tradicional)
    - file: FileBasedJobQueue (fallback local)
    """

    @staticmethod
    def create(
        provider: JobQueueProvider = "sqlite",
        **kwargs,
    ) -> JobQueuePort:
        """
        Cria instância de JobQueue baseada no provider.

        Args:
            provider: Tipo de provider ("sqlite", "dragonfly", "redis", "file")
            **kwargs: Argumentos específicos do provider

        Returns:
            Instância de JobQueuePort

        Raises:
            ValueError: Se provider inválido
            ImportError: Se dependências não instaladas
        """
        if provider == "sqlite":
            return JobQueueFactory._create_sqlite(**kwargs)
        elif provider == "dragonfly":
            return JobQueueFactory._create_dragonfly(**kwargs)
        elif provider == "redis":
            return JobQueueFactory._create_redis(**kwargs)
        elif provider == "file":
            return JobQueueFactory._create_file(**kwargs)
        else:
            raise ValueError(f"Provider inválido: {provider}")

    @staticmethod
    def _create_sqlite(**kwargs) -> JobQueuePort:
        """Cria SQLiteJobQueue (recomendado, zero dependências)."""
        from infra.webhooks.adapters.sqlite_job_queue import SQLiteJobQueue

        logger.info("Usando SQLite como Job Queue provider")
        return SQLiteJobQueue(**kwargs)

    @staticmethod
    def _create_dragonfly(**kwargs) -> JobQueuePort:
        """Cria RedisJobQueue configurado para DragonflyDB."""
        from infra.webhooks.adapters.redis_job_queue import RedisJobQueue

        logger.info("Usando DragonflyDB como Job Queue provider")
        return RedisJobQueue(**kwargs)

    @staticmethod
    def _create_redis(**kwargs) -> JobQueuePort:
        """Cria RedisJobQueue configurado para Redis tradicional."""
        from infra.webhooks.adapters.redis_job_queue import RedisJobQueue

        logger.info("Usando Redis tradicional como Job Queue provider")
        return RedisJobQueue(**kwargs)

    @staticmethod
    def _create_file(**kwargs) -> JobQueuePort:
        """Cria FileBasedJobQueue (persistência em arquivos)."""
        try:
            from infra.webhooks.adapters.file_based_job_queue import (
                FileBasedJobQueue,
            )

            logger.info("Usando FileBasedJobQueue como Job Queue provider")
            return FileBasedJobQueue()
        except ImportError as e:
            logger.error(f"FileBasedJobQueue não disponível: {e}")
            raise

    @staticmethod
    def create_from_env() -> JobQueuePort:
        """
        Cria JobQueue baseado em variável de ambiente.

        Lê JOB_QUEUE_PROVIDER do ambiente e cria a instância apropriada.

        Returns:
            Instância de JobQueuePort

        Exemplo:
            >>> queue = JobQueueFactory.create_from_env()
        """
        import os

        # Ler provider do ambiente (padrão: sqlite)
        provider = os.getenv("JOB_QUEUE_PROVIDER", "sqlite")

        # Configurações específicas por provider
        if provider == "sqlite":
            kwargs = {
                "db_path": os.getenv("SQLITE_DB_PATH", "data/jobs.db"),
                "timeout_seconds": float(
                    os.getenv("SQLITE_TIMEOUT", "5.0")
                ),
            }
        elif provider in ("dragonfly", "redis"):
            kwargs = {
                "host": os.getenv("DRAGONFLY_HOST", "localhost"),
                "port": int(os.getenv("DRAGONFLY_PORT", "6379")),
                "db": 0,
                "decode_responses": True,
            }
        else:
            kwargs = {}

        return JobQueueFactory.create(provider, **kwargs)


# Função de conveniência para uso rápido
def create_job_queue(
    provider: JobQueueProvider | None = None,
    **kwargs,
) -> JobQueuePort:
    """
    Função de conveniência para criar JobQueue.

    Args:
        provider: Tipo de provider (None = lê do ambiente)
        **kwargs: Argumentos específicos do provider

    Returns:
        Instância de JobQueuePort
    """
    if provider is None:
        return JobQueueFactory.create_from_env()
    return JobQueueFactory.create(provider, **kwargs)
