# -*- coding: utf-8 -*-
"""
Metrics Event Listener.

Listens to ALL Domain Events and records metrics.
Tracks jobs/hour, latency, success/failure ratios.

PRD018 ARCH-11: MetricsEventListener desacoplado via Domain Events.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.domain_events.event_bus import EventBus
    from core.domain_events.domain_event import DomainEvent

from core.domain_events.job_events import (
    JobStartedEvent,
    JobCompletedEvent,
    JobFailedEvent,
)
from core.domain_events.issue_events import IssueReceivedEvent

logger = logging.getLogger(__name__)


class MetricsEventListener:
    """
    Listener for ALL Domain Events to record metrics.

    Responsibilities:
    - Subscribe to all Domain Events
    - Track metrics: jobs/hour, latency P50/P95/P99, success/failure ratio
    - Provide metrics query interface

    PRD018 ARCH-11: Desacoplado - Componentes não conhecem coleta de métricas.
    """

    def __init__(self, event_bus: "EventBus"):
        """
        Inicializa listener.

        Args:
            event_bus: Event bus para se inscrever nos eventos
        """
        self.event_bus = event_bus
        self._subscription_ids: list[str] = []

        # Metrics storage
        self._job_counts: dict[str, int] = defaultdict(int)  # status -> count
        self._job_latencies: list[float] = []  # duração em segundos
        self._event_counts: dict[str, int] = defaultdict(int)  # event_type -> count
        self._jobs_last_hour: list[datetime] = []  # timestamps dos jobs

    async def start(self) -> None:
        """
        Inicia o listener, inscrevendo-se em TODOS os eventos.

        Deve ser chamado durante a inicialização da aplicação.
        """
        # Subscribe to all job events
        job_events = [JobStartedEvent, JobCompletedEvent, JobFailedEvent]
        for event_cls in job_events:
            sub_id = self.event_bus.subscribe(
                event_cls,
                self._on_any_event,
            )
            self._subscription_ids.append(sub_id)

        # Subscribe to issue events
        issue_events = [IssueReceivedEvent]
        for event_cls in issue_events:
            sub_id = self.event_bus.subscribe(
                event_cls,
                self._on_any_event,
            )
            self._subscription_ids.append(sub_id)

        logger.info(
            f"MetricsEventListener iniciado com {len(self._subscription_ids)} inscrições"
        )

    async def stop(self) -> None:
        """
        Para o listener, cancelando todas as inscrições.

        Deve ser chamado durante o shutdown da aplicação.
        """
        for sub_id in self._subscription_ids:
            try:
                self.event_bus.unsubscribe(sub_id)
            except Exception as e:
                logger.warning(f"Erro ao cancelar inscrição {sub_id}: {e}")

        self._subscription_ids.clear()
        logger.info("MetricsEventListener parado")

    async def _on_any_event(self, event: DomainEvent) -> None:
        """
        Handler para TODOS os eventos.

        Registra métricas baseadas no tipo de evento.

        Args:
            event: Domain Event qualquer
        """
        try:
            event_type = event.event_type
            self._event_counts[event_type] += 1

            # Métricas específicas por tipo de evento
            if isinstance(event, JobStartedEvent):
                # Job iniciado - registra timestamp
                pass  # Já registramos o tempo de início no JobOrchestrator

            elif isinstance(event, JobCompletedEvent):
                # Job completado com sucesso
                self._job_counts["completed"] += 1
                self._job_latencies.append(event.duration_seconds)
                self._jobs_last_hour.append(event.timestamp)

                # Limpa timestamps antigos (mais de 1 hora)
                self._cleanup_old_timestamps()

            elif isinstance(event, JobFailedEvent):
                # Job falhou
                self._job_counts["failed"] += 1
                self._job_latencies.append(event.duration_seconds)
                self._jobs_last_hour.append(event.timestamp)

                # Limpa timestamps antigos (mais de 1 hora)
                self._cleanup_old_timestamps()

            elif isinstance(event, IssueReceivedEvent):
                # Issue recebida
                self._event_counts["issues_received"] += 1

        except Exception as e:
            logger.error(
                f"Erro ao processar evento {event.event_type}: {e}",
                # exc_info removido - SkybridgeLogger não suporta
            )

    def _cleanup_old_timestamps(self) -> None:
        """
        Remove timestamps com mais de 1 hora.

        Mantém apenas jobs recentes para cálculo de jobs/hora.
        """
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self._jobs_last_hour = [
            ts for ts in self._jobs_last_hour if ts > cutoff
        ]

    def get_metrics(self) -> dict[str, object]:
        """
        Retorna todas as métricas coletadas.

        Returns:
            Dicionário com métricas:
            - jobs_per_hour: Jobs executados na última hora
            - total_jobs: Total de jobs processados
            - success_rate: Taxa de sucesso (0-1)
            - latency_p50: Mediana de latência em segundos
            - latency_p95: Percentil 95 de latência em segundos
            - latency_p99: Percentil 99 de latência em segundos
            - event_counts: Contagem de eventos por tipo
        """
        # Calcula jobs por hora
        jobs_per_hour = len(self._jobs_last_hour)

        # Calcula taxa de sucesso
        total_completed = self._job_counts["completed"]
        total_failed = self._job_counts["failed"]
        total_jobs = total_completed + total_failed
        success_rate = total_completed / total_jobs if total_jobs > 0 else 0.0

        # Calcula percentis de latência
        latencies = sorted(self._job_latencies)
        latency_p50 = (
            latencies[len(latencies) // 2] if latencies else 0.0
        )  # Mediana
        latency_p95 = (
            latencies[int(len(latencies) * 0.95)] if latencies else 0.0
        )  # P95
        latency_p99 = (
            latencies[int(len(latencies) * 0.99)] if latencies else 0.0
        )  # P99

        return {
            "jobs_per_hour": jobs_per_hour,
            "total_jobs": total_jobs,
            "success_rate": success_rate,
            "latency_p50": latency_p50,
            "latency_p95": latency_p95,
            "latency_p99": latency_p99,
            "event_counts": dict(self._event_counts),
        }

    def reset_metrics(self) -> None:
        """Reseta todas as métricas."""
        self._job_counts.clear()
        self._job_latencies.clear()
        self._event_counts.clear()
        self._jobs_last_hour.clear()
        logger.info("Métricas resetadas")
