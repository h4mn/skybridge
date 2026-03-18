# coding: utf-8
"""
Métricas de workers.

Coleta e gerencia métricas de performance dos workers.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class WorkerMetrics:
    """Métricas de um worker."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")

    @property
    def average_latency_ms(self) -> float:
        """Retorna latência média em ms."""
        if self.total_calls == 0:
            return 0.0
        return self.total_latency_ms / self.total_calls

    @property
    def success_rate(self) -> float:
        """Retorna taxa de sucesso (0-1)."""
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls

    def record_call(self, latency_ms: float, success: bool) -> None:
        """
        Registra uma chamada.

        Args:
            latency_ms: Latência em ms.
            success: Se foi bem-sucedida.
        """
        self.total_calls += 1
        self.total_latency_ms += latency_ms
        self.max_latency_ms = max(self.max_latency_ms, latency_ms)
        self.min_latency_ms = min(self.min_latency_ms, latency_ms)

        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1


class WorkerMetricsCollector:
    """
    Coletor de métricas de workers.

    Gerencia métricas de múltiplos workers.
    """

    def __init__(self) -> None:
        """Inicializa o coletor."""
        self._metrics: Dict[str, WorkerMetrics] = {}

    def get_metrics(self, worker_name: str) -> WorkerMetrics:
        """
        Retorna métricas de um worker.

        Args:
            worker_name: Nome do worker.

        Returns:
            WorkerMetrics do worker.
        """
        if worker_name not in self._metrics:
            self._metrics[worker_name] = WorkerMetrics()
        return self._metrics[worker_name]

    def record_call(
        self,
        worker_name: str,
        latency_ms: float,
        success: bool,
    ) -> None:
        """
        Registra uma chamada de worker.

        Args:
            worker_name: Nome do worker.
            latency_ms: Latência em ms.
            success: Se foi bem-sucedida.
        """
        metrics = self.get_metrics(worker_name)
        metrics.record_call(latency_ms, success)

    def get_all_metrics(self) -> Dict[str, WorkerMetrics]:
        """Retorna todas as métricas."""
        return self._metrics.copy()


__all__ = ["WorkerMetrics", "WorkerMetricsCollector"]
