# -*- coding: utf-8 -*-
"""
Application Layer - Worker Orchestrator.

Implementa use cases e handlers para orquestrar workers:

Commands:
- StartWorkerCommand: Inicia um worker
- StopWorkerCommand: Para um worker

Handlers:
- StartWorkerHandler: Processa StartWorkerCommand
- StopWorkerHandler: Processa StopWorkerCommand

Use Cases:
- OrchestrateWorkersUseCase: Coordena execução de ticks
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
import asyncio

from ..domain.worker import (
    WorkerId,
    WorkerStatus,
    Worker,
    WorkerRegistry,
    WorkerNotFoundError,
)


# ═══════════════════════════════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class StartWorkerCommand:
    """
    Command para iniciar um Worker.

    Attributes:
        worker_id: ID do worker a iniciar
    """

    worker_id: WorkerId


@dataclass(frozen=True)
class StopWorkerCommand:
    """
    Command para parar um Worker.

    Attributes:
        worker_id: ID do worker a parar
        reason: Razão da parada (opcional)
    """

    worker_id: WorkerId
    reason: str | None = None


# ═══════════════════════════════════════════════════════════════════════
# Results
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class HandlerResult:
    """
    Resultado de um Handler.

    Attributes:
        is_success: Se operação foi bem-sucedida
        worker_id: ID do worker afetado
        error_message: Mensagem de erro (se houver)
    """

    is_success: bool
    worker_id: WorkerId
    error_message: str | None = None

    @classmethod
    def success(cls, worker_id: WorkerId) -> "HandlerResult":
        """Cria resultado de sucesso."""
        return cls(is_success=True, worker_id=worker_id)

    @classmethod
    def failure(cls, worker_id: WorkerId, error: str) -> "HandlerResult":
        """Cria resultado de falha."""
        return cls(is_success=False, worker_id=worker_id, error_message=error)


@dataclass(frozen=True)
class WorkerOrchestrationResult:
    """
    Resultado da orquestração de Workers.

    Attributes:
        is_success: Se operação foi bem-sucedida
        workers_ticked: Número de workers que executaram tick
        error_message: Mensagem de erro (se houver)
    """

    is_success: bool
    workers_ticked: int
    error_message: str | None = None

    @classmethod
    def success(cls, workers_ticked: int) -> "WorkerOrchestrationResult":
        """Cria resultado de sucesso."""
        return cls(is_success=True, workers_ticked=workers_ticked)

    @classmethod
    def failure(cls, error: str) -> "WorkerOrchestrationResult":
        """Cria resultado de falha."""
        return cls(is_success=False, workers_ticked=0, error_message=error)


# ═══════════════════════════════════════════════════════════════════════
# Handlers
# ═══════════════════════════════════════════════════════════════════════

class StartWorkerHandler:
    """
    Handler para StartWorkerCommand.

    Responsabilidades:
    - Buscar worker no registry
    - Executar worker.start()
    - Retornar resultado

    Attributes:
        registry: WorkerRegistry para buscar workers
    """

    def __init__(self, registry: WorkerRegistry):
        self._registry = registry

    async def handle(self, command: StartWorkerCommand) -> HandlerResult:
        """
        Processa comando de iniciar worker.

        Args:
            command: StartWorkerCommand

        Returns:
            HandlerResult
        """
        try:
            worker = self._registry.get(command.worker_id)
            worker.start()
            return HandlerResult.success(worker.id)
        except WorkerNotFoundError:
            return HandlerResult.failure(
                command.worker_id,
                f"Worker '{command.worker_id}' não encontrado"
            )
        except Exception as e:
            return HandlerResult.failure(
                command.worker_id,
                f"Erro ao iniciar: {e}"
            )


class StopWorkerHandler:
    """
    Handler para StopWorkerCommand.

    Responsabilidades:
    - Buscar worker no registry
    - Executar worker.stop()
    - Retornar resultado

    Attributes:
        registry: WorkerRegistry para buscar workers
    """

    def __init__(self, registry: WorkerRegistry):
        self._registry = registry

    async def handle(self, command: StopWorkerCommand) -> HandlerResult:
        """
        Processa comando de parar worker.

        Args:
            command: StopWorkerCommand

        Returns:
            HandlerResult
        """
        try:
            worker = self._registry.get(command.worker_id)
            worker.stop(reason=command.reason)
            return HandlerResult.success(worker.id)
        except WorkerNotFoundError:
            return HandlerResult.failure(
                command.worker_id,
                f"Worker '{command.worker_id}' não encontrado"
            )
        except Exception as e:
            return HandlerResult.failure(
                command.worker_id,
                f"Erro ao parar: {e}"
            )


# ═══════════════════════════════════════════════════════════════════════
# Use Cases
# ═══════════════════════════════════════════════════════════════════════

class OrchestrateWorkersUseCase:
    """
    Use Case para orquestrar execução de Workers.

    Responsabilidades:
    - Buscar workers RUNNING no registry
    - Executar tick() em cada worker
    - Coletar resultados
    - Retornar resumo da execução

    Attributes:
        registry: WorkerRegistry para buscar workers
    """

    def __init__(self, registry: WorkerRegistry):
        self._registry = registry

    async def execute(self) -> WorkerOrchestrationResult:
        """
        Executa um ciclo de orquestração.

        Busca todos workers RUNNING e executa tick() em cada um.

        Returns:
            WorkerOrchestrationResult com resumo
        """
        try:
            # Buscar workers RUNNING
            running_workers = self._registry.list_by_status(WorkerStatus.RUNNING)

            if not running_workers:
                return WorkerOrchestrationResult.success(workers_ticked=0)

            # Executar tick em cada worker
            ticked_count = 0
            for worker in running_workers:
                try:
                    worker.tick()
                    ticked_count += 1
                except Exception:
                    # Erro em worker não deve interromper orquestração
                    pass

            return WorkerOrchestrationResult.success(workers_ticked=ticked_count)

        except Exception as e:
            return WorkerOrchestrationResult.failure(
                f"Erro na orquestração: {e}"
            )


__all__ = [
    # Commands
    "StartWorkerCommand",
    "StopWorkerCommand",
    # Results
    "HandlerResult",
    "WorkerOrchestrationResult",
    # Handlers
    "StartWorkerHandler",
    "StopWorkerHandler",
    # Use Cases
    "OrchestrateWorkersUseCase",
]
