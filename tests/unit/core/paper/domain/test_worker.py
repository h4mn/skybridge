# -*- coding: utf-8 -*-
"""
Testes unitários para Domain Layer - Worker System.

Testa entidades e value objects do sistema de workers:
- WorkerId (Value Object)
- WorkerStatus (Enum)
- Worker (Entity)
- WorkerStarted, WorkerStopped, WorkerTickComplete (Domain Events)
- WorkerRegistry (Aggregate Root)

TDD: RED → GREEN → REFACTOR
"""

import pytest
from dataclasses import FrozenInstanceError
from decimal import Decimal
from datetime import datetime, timedelta
from typing import NamedTuple

from src.core.paper.domain.worker import (
    WorkerId,
    WorkerName,
    WorkerStatus,
    Worker,
    WorkerStarted,
    WorkerStopped,
    WorkerTickComplete,
    WorkerRegistry,
    WorkerAlreadyRegisteredError,
    WorkerNotFoundError,
)


# =============================================================================
# Testes: Value Objects
# =============================================================================

class TestWorkerId:
    """Testes para Value Object WorkerId."""

    def test_worker_id_criado_com_string(self):
        """Cria WorkerId com string."""
        worker_id = WorkerId("position-worker-1")

        assert worker_id.value == "position-worker-1"

    def test_worker_id_unico(self):
        """WorkerId相同 quando valor相同."""
        id1 = WorkerId("same")
        id2 = WorkerId("same")

        assert id1 == id2
        assert hash(id1) == hash(id2)

    def test_worker_id_imutavel(self):
        """WorkerId deve ser imutável."""
        worker_id = WorkerId("test")

        with pytest.raises(FrozenInstanceError):
            worker_id.value = "other"


class TestWorkerName:
    """Testes para Value Object WorkerName."""

    def test_worker_name_criado(self):
        """Cria WorkerName."""
        name = WorkerName("PositionWorker")

        assert name.value == "PositionWorker"

    def test_worker_name_valida_vazio(self):
        """WorkerName não pode ser vazio."""
        with pytest.raises(ValueError):
            WorkerName("")

    def test_worker_name_imutavel(self):
        """WorkerName deve ser imutável."""
        name = WorkerName("test")

        with pytest.raises(FrozenInstanceError):
            name.value = "other"


# =============================================================================
# Testes: Enum WorkerStatus
# =============================================================================

class TestWorkerStatus:
    """Testes para Enum WorkerStatus."""

    def test_status_inicial(self):
        """Worker inicia com status STOPPED."""
        assert WorkerStatus.STOPPED == "stopped"

    def test_status_transicao_valida(self):
        """Transição STOPPED → RUNNING válida."""
        assert WorkerStatus.STOPPED.can_transition_to(WorkerStatus.RUNNING)

    def test_status_transicao_invalida(self):
        """Transição RUNNING → RUNNING inválida (já está running)."""
        # TODO: Implementar validação de transição
        pass


# =============================================================================
# Testes: Entity Worker
# =============================================================================

class TestWorker:
    """Testes para entidade Worker."""

    def test_worker_criado(self):
        """Cria Worker com id e name."""
        worker_id = WorkerId("position-worker")
        worker_name = WorkerName("PositionWorker")

        worker = Worker(
            id=worker_id,
            name=worker_name,
            status=WorkerStatus.STOPPED,
        )

        assert worker.id == worker_id
        assert worker.name == worker_name
        assert worker.status == WorkerStatus.STOPPED
        assert worker.tick_count == 0

    def test_worker_start_muda_status(self):
        """start() muda status para RUNNING."""
        worker = Worker(
            id=WorkerId("test"),
            name=WorkerName("Test"),
            status=WorkerStatus.STOPPED,
        )

        event = worker.start()

        assert worker.status == WorkerStatus.RUNNING
        assert isinstance(event, WorkerStarted)
        assert event.worker_id.value == "test"

    def test_worker_stop_muda_status(self):
        """stop() muda status para STOPPED."""
        worker = Worker(
            id=WorkerId("test"),
            name=WorkerName("Test"),
            status=WorkerStatus.RUNNING,
        )

        event = worker.stop()

        assert worker.status == WorkerStatus.STOPPED
        assert isinstance(event, WorkerStopped)

    def test_worker_tick_incrementa_contador(self):
        """tick() incrementa contador e gera evento."""
        worker = Worker(
            id=WorkerId("test"),
            name=WorkerName("Test"),
            status=WorkerStatus.RUNNING,
        )

        event = worker.tick()

        assert worker.tick_count == 1
        assert isinstance(event, WorkerTickComplete)
        assert event.worker_id.value == "test"
        assert event.tick_number == 1

    def test_worker_tick_sem_estado_running_levanta_erro(self):
        """tick() sem status RUNNING levanta erro."""
        worker = Worker(
            id=WorkerId("test"),
            name=WorkerName("Test"),
            status=WorkerStatus.STOPPED,
        )

        with pytest.raises(RuntimeError):
            worker.tick()

    def test_worker_equality(self):
        """Workers são iguais quando ID相同."""
        id_same = WorkerId("same")

        worker1 = Worker(
            id=id_same,
            name=WorkerName("Name1"),
            status=WorkerStatus.STOPPED,
        )

        worker2 = Worker(
            id=id_same,
            name=WorkerName("Name2"),  # Nome diferente
            status=WorkerStatus.RUNNING,  # Status diferente
        )

        assert worker1 == worker2


# =============================================================================
# Testes: Domain Events
# =============================================================================

class TestWorkerStarted:
    """Testes para Domain Event WorkerStarted."""

    def test_worker_started_created(self):
        """Cria WorkerStarted com timestamp."""
        event = WorkerStarted(
            worker_id=WorkerId("test"),
            timestamp=datetime.now(),
        )

        assert event.worker_id.value == "test"
        assert isinstance(event.timestamp, datetime)

    def test_worker_started_serializavel(self):
        """WorkerStarted deve ser serializável."""
        event = WorkerStarted(
            worker_id=WorkerId("test"),
            timestamp=datetime(2026, 3, 31, 12, 0, 0),
        )

        data = event.to_dict()

        assert data["worker_id"] == "test"
        assert "timestamp" in data


class TestWorkerStopped:
    """Testes para Domain Event WorkerStopped."""

    def test_worker_stoppped_created(self):
        """Cria WorkerStopped."""
        event = WorkerStopped(
            worker_id=WorkerId("test"),
            timestamp=datetime.now(),
            reason="user_requested",
        )

        assert event.worker_id.value == "test"
        assert event.reason == "user_requested"


class TestWorkerTickComplete:
    """Testes para Domain Event WorkerTickComplete."""

    def test_worker_tick_complete_created(self):
        """Cria WorkerTickComplete."""
        event = WorkerTickComplete(
            worker_id=WorkerId("test"),
            tick_number=5,
            duration_ms=150,
            timestamp=datetime.now(),
        )

        assert event.worker_id.value == "test"
        assert event.tick_number == 5
        assert event.duration_ms == 150


# =============================================================================
# Testes: Aggregate Root WorkerRegistry
# =============================================================================

class TestWorkerRegistry:
    """Testes para Aggregate Root WorkerRegistry."""

    def test_registry_vazio_inicialmente(self):
        """Registry inicia vazio."""
        registry = WorkerRegistry()

        assert registry.is_empty
        assert registry.worker_count == 0

    def test_registry_register_adiciona_worker(self):
        """register() adiciona worker."""
        registry = WorkerRegistry()
        worker = Worker(
            id=WorkerId("test"),
            name=WorkerName("Test"),
            status=WorkerStatus.STOPPED,
        )

        registry.register(worker)

        assert registry.worker_count == 1
        assert not registry.is_empty

    def test_registry_register_worker_duplicado_erro(self):
        """register() com ID duplicado levanta erro."""
        registry = WorkerRegistry()
        worker1 = Worker(
            id=WorkerId("same"),
            name=WorkerName("Worker1"),
            status=WorkerStatus.STOPPED,
        )
        worker2 = Worker(
            id=WorkerId("same"),
            name=WorkerName("Worker2"),
            status=WorkerStatus.STOPPED,
        )

        registry.register(worker1)

        with pytest.raises(WorkerAlreadyRegisteredError):
            registry.register(worker2)

    def test_registry_get_retorna_worker(self):
        """get() retorna worker por ID."""
        registry = WorkerRegistry()
        worker = Worker(
            id=WorkerId("test"),
            name=WorkerName("Test"),
            status=WorkerStatus.STOPPED,
        )
        registry.register(worker)

        retrieved = registry.get(WorkerId("test"))

        assert retrieved == worker

    def test_registry_get_inexistente_erro(self):
        """get() com ID inexistente levanta erro."""
        registry = WorkerRegistry()

        with pytest.raises(WorkerNotFoundError):
            registry.get(WorkerId("inexistente"))

    def test_registry_remove_worker(self):
        """remove() remove worker."""
        registry = WorkerRegistry()
        worker = Worker(
            id=WorkerId("test"),
            name=WorkerName("Test"),
            status=WorkerStatus.STOPPED,
        )
        registry.register(worker)

        removed = registry.remove(WorkerId("test"))

        assert removed == worker
        assert registry.is_empty

    def test_registry_list_all(self):
        """list_all() retorna todos workers."""
        registry = WorkerRegistry()
        worker1 = Worker(
            id=WorkerId("w1"),
            name=WorkerName("Worker1"),
            status=WorkerStatus.STOPPED,
        )
        worker2 = Worker(
            id=WorkerId("w2"),
            name=WorkerName("Worker2"),
            status=WorkerStatus.RUNNING,
        )

        registry.register(worker1)
        registry.register(worker2)

        all_workers = registry.list_all()

        assert len(all_workers) == 2
        assert worker1 in all_workers
        assert worker2 in all_workers

    def test_registry_list_by_status(self):
        """list_by_status() filtra por status."""
        registry = WorkerRegistry()
        worker1 = Worker(
            id=WorkerId("w1"),
            name=WorkerName("Worker1"),
            status=WorkerStatus.STOPPED,
        )
        worker2 = Worker(
            id=WorkerId("w2"),
            name=WorkerName("Worker2"),
            status=WorkerStatus.RUNNING,
        )
        worker3 = Worker(
            id=WorkerId("w3"),
            name=WorkerName("Worker3"),
            status=WorkerStatus.RUNNING,
        )

        registry.register(worker1)
        registry.register(worker2)
        registry.register(worker3)

        running = registry.list_by_status(WorkerStatus.RUNNING)

        assert len(running) == 2
        assert worker2 in running
        assert worker3 in running
        assert worker1 not in running
