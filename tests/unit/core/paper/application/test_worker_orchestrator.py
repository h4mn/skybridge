# -*- coding: utf-8 -*-
"""
Testes unitários para Application Layer - Worker Orchestrator.

Testa use cases e handlers para orquestrar workers:
- OrchestrateWorkersUseCase
- StartWorkerHandler
- StopWorkerHandler

TDD: RED → GREEN → REFACTOR
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.core.paper.domain.worker import (
    WorkerId,
    WorkerName,
    WorkerStatus,
    Worker,
    WorkerRegistry,
)
from src.core.paper.application.worker_orchestrator import (
    OrchestrateWorkersUseCase,
    StartWorkerCommand,
    StopWorkerCommand,
    WorkerOrchestrationResult,
)


# =============================================================================
# Testes: StartWorkerHandler
# =============================================================================

class TestStartWorkerHandler:
    """Testes para handler de iniciar worker."""

    @pytest.fixture
    def registry(self):
        """Registry com worker registrado."""
        registry = WorkerRegistry()
        worker = Worker(
            id=WorkerId("test-worker"),
            name=WorkerName("TestWorker"),
            status=WorkerStatus.STOPPED,
        )
        registry.register(worker)
        return registry

    @pytest.mark.asyncio
    async def test_start_worker_muda_status_para_running(self, registry):
        """Handler deve iniciar worker."""
        from src.core.paper.application.worker_orchestrator import StartWorkerHandler

        handler = StartWorkerHandler(registry=registry)
        command = StartWorkerCommand(worker_id=WorkerId("test-worker"))

        result = await handler.handle(command)

        assert result.is_success
        assert result.worker_id.value == "test-worker"

        # Worker deve estar RUNNING
        worker = registry.get(WorkerId("test-worker"))
        assert worker.status == WorkerStatus.RUNNING

    @pytest.mark.asyncio
    async def test_start_worker_inexistente_erro(self, registry):
        """Handler deve falhar se worker não existe."""
        from src.core.paper.application.worker_orchestrator import StartWorkerHandler

        handler = StartWorkerHandler(registry=registry)
        command = StartWorkerCommand(worker_id=WorkerId("inexistente"))

        result = await handler.handle(command)

        assert not result.is_success
        assert "não encontrado" in result.error_message.lower()


# =============================================================================
# Testes: StopWorkerHandler
# =============================================================================

class TestStopWorkerHandler:
    """Testes para handler de parar worker."""

    @pytest.fixture
    def registry(self):
        """Registry com worker running."""
        registry = WorkerRegistry()
        worker = Worker(
            id=WorkerId("test-worker"),
            name=WorkerName("TestWorker"),
            status=WorkerStatus.RUNNING,
        )
        registry.register(worker)
        return registry

    @pytest.mark.asyncio
    async def test_stop_worker_muda_status_para_stopped(self, registry):
        """Handler deve parar worker."""
        from src.core.paper.application.worker_orchestrator import StopWorkerHandler

        handler = StopWorkerHandler(registry=registry)
        command = StopWorkerCommand(
            worker_id=WorkerId("test-worker"),
            reason="user_requested"
        )

        result = await handler.handle(command)

        assert result.is_success

        # Worker deve estar STOPPED
        worker = registry.get(WorkerId("test-worker"))
        assert worker.status == WorkerStatus.STOPPED


# =============================================================================
# Testes: OrchestrateWorkersUseCase
# =============================================================================

class TestOrchestrateWorkersUseCase:
    """Testes para OrchestrateWorkersUseCase."""

    @pytest.fixture
    def registry(self):
        """Registry com múltiplos workers."""
        registry = WorkerRegistry()
        registry.register(Worker(
            id=WorkerId("worker1"),
            name=WorkerName("Worker1"),
            status=WorkerStatus.RUNNING,
        ))
        registry.register(Worker(
            id=WorkerId("worker2"),
            name=WorkerName("Worker2"),
            status=WorkerStatus.RUNNING,
        ))
        registry.register(Worker(
            id=WorkerId("worker3"),
            name=WorkerName("Worker3"),
            status=WorkerStatus.STOPPED,
        ))
        return registry

    @pytest.mark.asyncio
    async def test_orchestrate_executa_tick_em_workers_running(self, registry):
        """Use case deve executar tick em todos workers RUNNING."""
        use_case = OrchestrateWorkersUseCase(registry=registry)

        result = await self._execute_orchestration(use_case)

        assert result.is_success
        assert result.workers_ticked == 2  # Apenas RUNNING

        # tick_count incrementado
        worker1 = registry.get(WorkerId("worker1"))
        worker2 = registry.get(WorkerId("worker2"))
        worker3 = registry.get(WorkerId("worker3"))

        assert worker1.tick_count == 1
        assert worker2.tick_count == 1
        assert worker3.tick_count == 0  # STOPPED não executou

    @pytest.mark.asyncio
    async def test_orchestrate_zero_workers_retorna_sucesso(self, registry):
        """Use case com zero workers RUNNING retorna sucesso."""
        # Para todos workers
        for worker in registry.list_all():
            worker.stop()

        use_case = OrchestrateWorkersUseCase(registry=registry)

        result = await self._execute_orchestration(use_case)

        assert result.is_success
        assert result.workers_ticked == 0

    async def _execute_orchestration(self, use_case) -> WorkerOrchestrationResult:
        """Helper para executar orquestração síncrona."""
        return await use_case.execute()


# =============================================================================
# Testes: Commands
# =============================================================================

class TestCommands:
    """Testes para Commands."""

    def test_start_worker_command_criado(self):
        """Cria StartWorkerCommand."""
        command = StartWorkerCommand(worker_id=WorkerId("test"))

        assert command.worker_id.value == "test"

    def test_stop_worker_command_criado(self):
        """Cria StopWorkerCommand."""
        command = StopWorkerCommand(
            worker_id=WorkerId("test"),
            reason="test_reason"
        )

        assert command.worker_id.value == "test"
        assert command.reason == "test_reason"
