# -*- coding: utf-8 -*-
"""
Domain Layer - Worker System.

Implementa o sistema de workers usando DDD:

Value Objects:
- WorkerId: Identificador único do worker
- WorkerName: Nome descritivo do worker

Entity:
- Worker: Representa um worker com estado

Domain Events:
- WorkerStarted: Emitido quando worker inicia
- WorkerStopped: Emitido quando worker para
- WorkerTickComplete: Emitido após cada tick

Aggregate Root:
- WorkerRegistry: Gerencia coleção de workers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol
import uuid


# ═══════════════════════════════════════════════════════════════════════
# Value Objects
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class WorkerId:
    """
    Identificador único de um Worker.

    Attributes:
        value: Valor do ID (string)
    """

    value: str

    def __post_init__(self):
        """Valida que value não é vazio."""
        if not self.value or not self.value.strip():
            raise ValueError("WorkerId não pode ser vazio")

    @classmethod
    def generate(cls) -> "WorkerId":
        """Gera novo WorkerId único."""
        return cls(f"worker-{uuid.uuid4().hex[:12]}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class WorkerName:
    """
    Nome descritivo de um Worker.

    Attributes:
        value: Nome do worker
    """

    value: str

    def __post_init__(self):
        """Valida que value não é vazio."""
        if not self.value or not self.value.strip():
            raise ValueError("WorkerName não pode ser vazio")


# ═══════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════

class WorkerStatus(str, Enum):
    """Estado de um Worker."""

    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"

    def can_transition_to(self, new_status: "WorkerStatus") -> bool:
        """Verifica se transição é válida."""
        # STOPPED → RUNNING: ok
        # RUNNING → STOPPED: ok
        # ERROR → STOPPED: ok
        # RUNNING → RUNNING: não (já está running)
        # STOPPED → STOPPED: ok (não-op)

        invalid = {
            WorkerStatus.RUNNING: {WorkerStatus.RUNNING},
        }

        return new_status not in invalid.get(self, set())


# ═══════════════════════════════════════════════════════════════════════
# Domain Events
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class WorkerStarted:
    """
    Evento de domínio: Worker iniciado.

    Attributes:
        worker_id: ID do worker
        timestamp: Momento do início
    """

    worker_id: WorkerId
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Converte para dict serializável."""
        return {
            "event_type": "worker_started",
            "worker_id": self.worker_id.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass(frozen=True)
class WorkerStopped:
    """
    Evento de domínio: Worker parado.

    Attributes:
        worker_id: ID do worker
        timestamp: Momento da parada
        reason: Razão da parada (opcional)
    """

    worker_id: WorkerId
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str | None = None

    def to_dict(self) -> dict:
        """Converte para dict serializável."""
        return {
            "event_type": "worker_stopped",
            "worker_id": self.worker_id.value,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class WorkerTickComplete:
    """
    Evento de domínio: Tick completado.

    Attributes:
        worker_id: ID do worker
        tick_number: Número do tick
        duration_ms: Duração em milissegundos
        timestamp: Momento de conclusão
    """

    worker_id: WorkerId
    tick_number: int
    duration_ms: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Converte para dict serializável."""
        return {
            "event_type": "worker_tick_complete",
            "worker_id": self.worker_id.value,
            "tick_number": self.tick_number,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════
# Entity
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class Worker:
    """
    Entidade Worker.

    Representa um worker com estado e comportamento.
    Dois workers são iguais se tiverem o mesmo ID.

    Attributes:
        id: Identificador único
        name: Nome descritivo
        status: Estado atual
        tick_count: Número de ticks executados
        created_at: Momento de criação
    """

    id: WorkerId
    name: WorkerName
    status: WorkerStatus
    tick_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def __eq__(self, other) -> bool:
        """Workers são iguais quando têm o mesmo ID."""
        if not isinstance(other, Worker):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash baseado no ID."""
        return hash(self.id.value)

    def start(self) -> WorkerStarted:
        """
        Inicia o worker.

        Returns:
            WorkerStarted event

        Raises:
            ValueError: Se transição inválida
        """
        if not self.status.can_transition_to(WorkerStatus.RUNNING):
            raise ValueError(
                f"Transição inválida: {self.status} → {WorkerStatus.RUNNING}"
            )

        self.status = WorkerStatus.RUNNING
        return WorkerStarted(worker_id=self.id)

    def stop(self, reason: str | None = None) -> WorkerStopped:
        """
        Para o worker.

        Args:
            reason: Razão da parada (opcional)

        Returns:
            WorkerStopped event
        """
        if not self.status.can_transition_to(WorkerStatus.STOPPED):
            raise ValueError(
                f"Transição inválida: {self.status} → {WorkerStatus.STOPPED}"
            )

        self.status = WorkerStatus.STOPPED
        return WorkerStopped(worker_id=self.id, reason=reason)

    def tick(self) -> WorkerTickComplete:
        """
        Executa um tick do worker.

        Returns:
            WorkerTickComplete event

        Raises:
            RuntimeError: Se worker não está RUNNING
        """
        if self.status != WorkerStatus.RUNNING:
            raise RuntimeError(
                f"Worker não está RUNNING: {self.status}"
            )

        self.tick_count += 1
        return WorkerTickComplete(
            worker_id=self.id,
            tick_number=self.tick_count,
            duration_ms=0,  # Será preenchido pelo executor
        )


# ═══════════════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════════════

class WorkerAlreadyRegisteredError(Exception):
    """Erro: Worker com mesmo ID já registrado."""

    def __init__(self, worker_id: WorkerId):
        self.worker_id = worker_id
        super().__init__(f"Worker '{worker_id}' já registrado")


class WorkerNotFoundError(Exception):
    """Erro: Worker não encontrado."""

    def __init__(self, worker_id: WorkerId):
        self.worker_id = worker_id
        super().__init__(f"Worker '{worker_id}' não encontrado")


# ═══════════════════════════════════════════════════════════════════════
# Aggregate Root
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class WorkerRegistry:
    """
    Aggregate Root para gerenciar Workers.

    Responsabilidades:
    - Registrar novos workers
    - Remover workers
    - Consultar workers por ID ou status
    - Manter consistência da coleção

    Attributes:
        _workers: Dict mapeando WorkerId → Worker
    """

    _workers: dict[WorkerId, Worker] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        """Retorna True se não há workers registrados."""
        return len(self._workers) == 0

    @property
    def worker_count(self) -> int:
        """Número de workers registrados."""
        return len(self._workers)

    def register(self, worker: Worker) -> None:
        """
        Registra um novo worker.

        Args:
            worker: Worker a registrar

        Raises:
            WorkerAlreadyRegisteredError: Se ID já existe
        """
        if worker.id in self._workers:
            raise WorkerAlreadyRegisteredError(worker.id)

        self._workers[worker.id] = worker

    def get(self, worker_id: WorkerId) -> Worker:
        """
        Retorna worker por ID.

        Args:
            worker_id: ID do worker

        Returns:
            Worker

        Raises:
            WorkerNotFoundError: Se ID não existe
        """
        if worker_id not in self._workers:
            raise WorkerNotFoundError(worker_id)

        return self._workers[worker_id]

    def remove(self, worker_id: WorkerId) -> Worker:
        """
        Remove worker por ID.

        Args:
            worker_id: ID do worker

        Returns:
            Worker removido

        Raises:
            WorkerNotFoundError: Se ID não existe
        """
        if worker_id not in self._workers:
            raise WorkerNotFoundError(worker_id)

        return self._workers.pop(worker_id)

    def list_all(self) -> list[Worker]:
        """
        Lista todos workers registrados.

        Returns:
            Lista de todos workers
        """
        return list(self._workers.values())

    def list_by_status(self, status: WorkerStatus) -> list[Worker]:
        """
        Lista workers por status.

        Args:
            status: Status para filtrar

        Returns:
            Lista de workers com o status
        """
        return [
            w for w in self._workers.values()
            if w.status == status
        ]

    def clear(self) -> None:
        """Remove todos workers."""
        self._workers.clear()


__all__ = [
    # Value Objects
    "WorkerId",
    "WorkerName",
    # Enum
    "WorkerStatus",
    # Entity
    "Worker",
    # Domain Events
    "WorkerStarted",
    "WorkerStopped",
    "WorkerTickComplete",
    # Aggregate Root
    "WorkerRegistry",
    # Exceptions
    "WorkerAlreadyRegisteredError",
    "WorkerNotFoundError",
]
