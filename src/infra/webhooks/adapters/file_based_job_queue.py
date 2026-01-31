# -*- coding: utf-8 -*-
"""
File-Based Job Queue Adapter.

Implementação persistente em arquivos do JobQueuePort (evolutiva).

Esta implementação:
- Resolve o problema de filas separadas entre processos
- Funciona sem dependências externas (zero setup)
- Possui métricas embutidas para decisão de quando migrar para Redis
- Preparada para evoluir para Redis/RabbitMQ (mesma interface)

Limitações:
- Throughput: ~10-20 jobs/hora (suficiente para MVP)
- Latência: ~50ms por operação (I/O em arquivo)
- Escala: Single worker ideal, múltiplos workers com lock file

Para produção com alto volume, migrar para RedisJobQueue.
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.webhooks.domain import WebhookJob
    from core.webhooks.ports.job_queue_port import JobQueuePort

from core.webhooks.ports.job_queue_port import JobQueuePort, QueueError


class FileBasedJobQueue(JobQueuePort):
    """
    Fila de jobs persistida em arquivos JSON.

    Compartilha estado entre processos via sistema de arquivos,
    resolvendo o problema de filas separadas (Problema #1).

    Estrutura de diretórios:
    workspace/skybridge/fila/
    ├── queue.json              # Fila principal (array de job_ids)
    ├── jobs/                   # Jobs aguardando processamento
    │   ├── job_abc123.json
    │   └── job_def456.json
    ├── processing/             # Jobs em processamento
    │   └── job_abc123.json
    ├── completed/              # Jobs completados
    │   └── job_abc123.json
    └── failed/                 # Jobs que falharam
        └── job_def456.json

    Attributes:
        queue_dir: Diretório base da fila
        _lock: Lock asyncio para operações atômicas
        _metrics: Métricas embutidas para tomada de decisão
    """

    def __init__(self, queue_dir: str = "workspace/skybridge/fila") -> None:
        """
        Inicializa fila baseada em arquivos.

        Args:
            queue_dir: Diretório para armazenar fila e jobs
        """
        self.queue_dir = Path(queue_dir)
        self.queue_file = self.queue_dir / "queue.json"
        self.jobs_dir = self.queue_dir / "jobs"
        self.processing_dir = self.queue_dir / "processing"
        self.completed_dir = self.queue_dir / "completed"
        self.failed_dir = self.queue_dir / "failed"
        self.metrics_file = self.queue_dir / "metrics.json"

        # Criar diretórios
        for dir_path in [
            self.queue_dir,
            self.jobs_dir,
            self.processing_dir,
            self.completed_dir,
            self.failed_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Lock para evitar race conditions
        self._lock = asyncio.Lock()

        # Métricas embutidas
        self._metrics = {
            "enqueue_count": 0,
            "dequeue_count": 0,
            "complete_count": 0,
            "fail_count": 0,
            "enqueue_latency_ms": [],  # Últimos 1000
            "dequeue_latency_ms": [],  # Últimos 1000
        }

        # Carregar métricas persistidas
        self._load_metrics()

    async def enqueue(self, job: "WebhookJob") -> str:
        """
        Enfileira job com persistência em arquivo.

        Args:
            job: Job a ser enfileirado

        Returns:
            job_id do job enfileirado

        Raises:
            QueueError: Se falhar ao persistir
        """
        start = time.time()

        async with self._lock:
            try:
                # 1. Salvar dados do job em arquivo
                job_file = self.jobs_dir / f"{job.job_id}.json"
                job_file.write_text(self._job_to_json(job), encoding="utf-8")

                # 2. Adicionar job_id à fila
                queue = self._load_queue()
                queue.append(job.job_id)
                self._save_queue(queue)

                # 3. Atualizar métricas
                self._metrics["enqueue_count"] += 1
                latency_ms = (time.time() - start) * 1000
                self._metrics["enqueue_latency_ms"].append(latency_ms)
                if len(self._metrics["enqueue_latency_ms"]) > 1000:
                    self._metrics["enqueue_latency_ms"] = self._metrics["enqueue_latency_ms"][
                        -1000:
                    ]

                # 4. Persistir métricas periodicamente
                if self._metrics["enqueue_count"] % 10 == 0:
                    self._save_metrics()

                return job.job_id

            except Exception as e:
                raise QueueError(f"Falha ao enfileirar job {job.job_id}: {e}") from e

    async def dequeue(self) -> "WebhookJob | None":
        """
        Remove próximo job da fila com persistência.

        Returns:
            Próximo job ou None se fila vazia
        """
        start = time.time()

        async with self._lock:
            try:
                # 1. Carregar fila
                queue = self._load_queue()

                if not queue:
                    return None

                # 2. Pegar próximo job_id (FIFO)
                job_id = queue.pop(0)
                self._save_queue(queue)

                # 3. Mover arquivo para processing/
                job_file = self.jobs_dir / f"{job_id}.json"

                # Job pode estar em processing/ se worker crashou
                if not job_file.exists():
                    job_file = self.processing_dir / f"{job_id}.json"

                processing_file = self.processing_dir / f"{job_id}.json"
                if job_file.exists():
                    job_file.rename(processing_file)

                # 4. Carregar dados do job
                if not processing_file.exists():
                    return None

                job_data = json.loads(processing_file.read_text(encoding="utf-8"))
                job = self._job_from_dict(job_data)

                # 5. Atualizar métricas
                self._metrics["dequeue_count"] += 1
                latency_ms = (time.time() - start) * 1000
                self._metrics["dequeue_latency_ms"].append(latency_ms)
                if len(self._metrics["dequeue_latency_ms"]) > 1000:
                    self._metrics["dequeue_latency_ms"] = self._metrics["dequeue_latency_ms"][
                        -1000:
                    ]

                # 6. Persistir métricas periodicamente
                if self._metrics["dequeue_count"] % 10 == 0:
                    self._save_metrics()

                return job

            except Exception as e:
                raise QueueError(f"Falha ao desenfileirar: {e}") from e

    async def get_job(self, job_id: str) -> "WebhookJob | None":
        """
        Busca job por ID em qualquer estado.

        Args:
            job_id: ID do job

        Returns:
            Job encontrado ou None
        """
        # Buscar em todos os diretórios
        for dir_path in [self.jobs_dir, self.processing_dir, self.completed_dir, self.failed_dir]:
            job_file = dir_path / f"{job_id}.json"
            if job_file.exists():
                try:
                    job_data = json.loads(job_file.read_text(encoding="utf-8"))
                    return self._job_from_dict(job_data)
                except Exception:
                    continue
        return None

    async def complete(self, job_id: str, result: dict | None = None) -> None:
        """
        Marca job como completo - move para completed/.

        Args:
            job_id: ID do job
            result: Resultado opcional do processamento
        """
        async with self._lock:
            try:
                # Mover arquivo de processing/ para completed/
                processing_file = self.processing_dir / f"{job_id}.json"
                completed_file = self.completed_dir / f"{job_id}.json"

                if processing_file.exists():
                    # Adicionar resultado ao arquivo
                    job_data = json.loads(processing_file.read_text(encoding="utf-8"))
                    if result:
                        job_data["result"] = result
                    job_data["status"] = "completed"
                    job_data["completed_at"] = datetime.utcnow().isoformat()

                    completed_file.write_text(json.dumps(job_data, indent=2), encoding="utf-8")
                    processing_file.unlink()

                self._metrics["complete_count"] += 1
                self._save_metrics()

            except Exception as e:
                raise QueueError(f"Falha ao completar job {job_id}: {e}") from e

    async def wait_for_dequeue(self, timeout: float | None = None) -> "WebhookJob | None":
        """
        Aguarda até que haja um job disponível e o remove.

        Implementa polling da fila para compatibilidade com worker.

        Args:
            timeout: Tempo máximo de espera em segundos

        Returns:
            Próximo job ou None se timeout
        """
        start = time.time()

        while True:
            # Tenta dequeue imediatamente
            job = await self.dequeue()
            if job:
                return job

            # Verifica timeout
            if timeout is not None:
                elapsed = time.time() - start
                if elapsed >= timeout:
                    return None
                remaining = timeout - elapsed
            else:
                remaining = 0.1  # Poll interval sem timeout

            # Aguarda antes de tentar novamente
            await asyncio.sleep(remaining if timeout else 0.1)

    async def fail(self, job_id: str, error: str) -> None:
        """
        Marca job como falhou - move para failed/.

        Args:
            job_id: ID do job
            error: Mensagem de erro
        """
        async with self._lock:
            try:
                processing_file = self.processing_dir / f"{job_id}.json"
                failed_file = self.failed_dir / f"{job_id}.json"

                if processing_file.exists():
                    job_data = json.loads(processing_file.read_text(encoding="utf-8"))
                    job_data["error"] = error
                    job_data["status"] = "failed"
                    job_data["failed_at"] = datetime.utcnow().isoformat()

                    failed_file.write_text(json.dumps(job_data, indent=2), encoding="utf-8")
                    processing_file.unlink()

                self._metrics["fail_count"] += 1
                self._save_metrics()

            except Exception as e:
                raise QueueError(f"Falha ao marcar job {job_id} como falhou: {e}") from e

    def size(self) -> int:
        """
        Retorna tamanho atual da fila (jobs aguardando).

        Returns:
            Número de jobs aguardando processamento
        """
        return len(self._load_queue())

    async def exists_by_delivery(self, delivery_id: str) -> bool:
        """
        Verifica se já existe job com este delivery ID.

        Busca em todos os diretórios (jobs, processing, completed, failed)
        para garantir idempotência de webhooks do GitHub.

        Args:
            delivery_id: ID único da entrega do webhook

        Returns:
            True se job com este delivery_id já existe, False caso contrário
        """
        # Buscar em todos os diretórios
        for dir_path in [self.jobs_dir, self.processing_dir, self.completed_dir, self.failed_dir]:
            if not dir_path.exists():
                continue
            for job_file in dir_path.glob("*.json"):
                try:
                    job_data = json.loads(job_file.read_text(encoding="utf-8"))
                    event_data = job_data.get("event", {})
                    if event_data.get("event_id") == delivery_id:
                        return True
                except Exception:
                    continue
        return False

    def get_metrics(self) -> dict[str, Any]:
        """
        Retorna métricas da fila para tomada de decisão.

        Calcula métricas importantes para decidir quando migrar para Redis:
        - queue_size: Tamanho atual da fila
        - jobs_per_hour: Throughput médio nas últimas 24h
        - enqueue_latency_p95_ms: Latência p95 de enqueue
        - backlog_age_seconds: Idade do job mais antigo
        - disk_usage_mb: Uso de disco em MB

        Returns:
            Dicionário com métricas calculadas
        """
        enqueue_latencies = self._metrics["enqueue_latency_ms"]
        dequeue_latencies = self._metrics["dequeue_latency_ms"]

        return {
            "queue_size": self.size(),
            "enqueue_count": self._metrics["enqueue_count"],
            "dequeue_count": self._metrics["dequeue_count"],
            "complete_count": self._metrics["complete_count"],
            "fail_count": self._metrics["fail_count"],
            "enqueue_latency_avg_ms": self._avg(enqueue_latencies),
            "enqueue_latency_p95_ms": self._percentile(enqueue_latencies, 95),
            "dequeue_latency_avg_ms": self._avg(dequeue_latencies),
            "dequeue_latency_p95_ms": self._percentile(dequeue_latencies, 95),
            "jobs_per_hour": self._calculate_jobs_per_hour(),
            "backlog_age_seconds": self._calculate_backlog_age(),
            "disk_usage_mb": self._calculate_disk_usage(),
        }

    def _load_queue(self) -> list[str]:
        """Carrega fila do arquivo."""
        if not self.queue_file.exists():
            return []
        try:
            return json.loads(self.queue_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_queue(self, queue: list[str]) -> None:
        """Salva fila no arquivo com write atômico."""
        temp_file = self.queue_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(queue), encoding="utf-8")
        temp_file.replace(self.queue_file)

    def _load_metrics(self) -> None:
        """Carrega métricas persistidas."""
        if self.metrics_file.exists():
            try:
                self._metrics = json.loads(self.metrics_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _save_metrics(self) -> None:
        """Salva métricas em arquivo."""
        temp_file = self.metrics_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(self._metrics, indent=2), encoding="utf-8")
        temp_file.replace(self.metrics_file)

    def _job_to_json(self, job: "WebhookJob") -> str:
        """Converte WebhookJob para JSON."""
        job_dict = {
            "job_id": job.job_id,
            "event": {
                "source": job.event.source.value,
                "event_type": job.event.event_type,
                "event_id": job.event.event_id,
                "payload": job.event.payload,
                "received_at": job.event.received_at.isoformat(),
                "signature": job.event.signature,
            },
            "status": job.status.value,
            "worktree_path": job.worktree_path,
            "branch_name": job.branch_name,
            "issue_number": job.issue_number,
            "initial_snapshot": job.initial_snapshot,
            "final_snapshot": job.final_snapshot,
            "metadata": job.metadata,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
        }
        return json.dumps(job_dict, indent=2)

    def _job_from_dict(self, data: dict[str, Any]) -> "WebhookJob":
        """Converte dict para WebhookJob."""
        from core.webhooks.domain import WebhookEvent, WebhookJob, JobStatus, WebhookSource

        event_data = data["event"]
        event = WebhookEvent(
            source=WebhookSource(event_data["source"]),
            event_type=event_data["event_type"],
            event_id=event_data["event_id"],
            payload=event_data["payload"],
            received_at=datetime.fromisoformat(event_data["received_at"]),
            signature=event_data.get("signature"),
        )

        return WebhookJob(
            job_id=data["job_id"],
            event=event,
            status=JobStatus(data["status"]),
            worktree_path=data.get("worktree_path"),
            branch_name=data.get("branch_name"),
            issue_number=data.get("issue_number"),
            initial_snapshot=data.get("initial_snapshot"),
            final_snapshot=data.get("final_snapshot"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error_message=data.get("error_message"),
        )

    def _avg(self, values: list[float]) -> float:
        """Calcula média."""
        return sum(values) / len(values) if values else 0.0

    def _percentile(self, values: list[float], p: int) -> float:
        """Calcula percentil."""
        if not values:
            return 0.0
        values_sorted = sorted(values)
        index = int(len(values_sorted) * p / 100)
        return values_sorted[min(index, len(values_sorted) - 1)]

    def _calculate_jobs_per_hour(self) -> float:
        """Calcula throughput médio (jobs/hora) nas últimas 24h."""
        if not self.completed_dir.exists():
            return 0.0

        now = time.time()
        last_24h = now - 86400

        count = 0
        for job_file in self.completed_dir.glob("*.json"):
            try:
                job_data = json.loads(job_file.read_text(encoding="utf-8"))
                completed_at = job_data.get("completed_at")
                if completed_at:
                    completed_time = datetime.fromisoformat(completed_at).timestamp()
                    if completed_time > last_24h:
                        count += 1
            except Exception:
                continue

        return count / 24  # jobs por hora (média)

    def _calculate_backlog_age(self) -> float:
        """Calcula idade do job mais antigo na fila (segundos)."""
        queue = self._load_queue()
        if not queue:
            return 0.0

        oldest_job_id = queue[0]
        job_file = self.jobs_dir / f"{oldest_job_id}.json"
        if not job_file.exists():
            return 0.0

        try:
            job_data = json.loads(job_file.read_text(encoding="utf-8"))
            created_at = job_data.get("created_at")
            if created_at:
                created_time = datetime.fromisoformat(created_at).timestamp()
                return time.time() - created_time
        except Exception:
            pass

        return 0.0

    def _calculate_disk_usage(self) -> float:
        """Calcula uso de disco em MB."""
        total_size = 0
        for file_path in self.queue_dir.rglob("*.json"):
            try:
                total_size += file_path.stat().st_size
            except Exception:
                continue
        return total_size / (1024 * 1024)

    async def list_jobs(
        self,
        limit: int = 100,
        status_filter: str | None = None,
    ) -> list[dict[str, object]]:
        """
        Lista jobs da fila para o WebUI.

        Args:
            limit: Número máximo de jobs a retornar
            status_filter: Filtrar por status (opcional)

        Returns:
            Lista de dicionários com dados dos jobs no formato esperado pelo frontend
        """
        jobs_list = []
        count = 0

        # Buscar em todos os diretórios (processing, completed, failed)
        for dir_path in [self.processing_dir, self.completed_dir, self.failed_dir, self.jobs_dir]:
            if not dir_path.exists():
                continue

            # Lista arquivos ordenados por data de modificação (mais recentes primeiro)
            job_files = sorted(
                dir_path.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            for job_file in job_files:
                if count >= limit:
                    break

                try:
                    job_data = json.loads(job_file.read_text(encoding="utf-8"))
                    job_status = job_data.get("status", "pending")

                    # Aplica filtro de status se especificado
                    if status_filter and job_status != status_filter.lower():
                        continue

                    # Determina source e event_type
                    event_data = job_data.get("event", {})
                    source = event_data.get("source", "unknown")
                    event_type = event_data.get("event_type", "unknown")

                    jobs_list.append({
                        "job_id": job_data.get("job_id", ""),
                        "source": source,
                        "event_type": event_type,
                        "status": job_status.upper(),
                        "created_at": job_data.get("created_at", ""),
                        "worktree_path": job_data.get("worktree_path"),
                    })
                    count += 1

                except Exception:
                    continue

            if count >= limit:
                break

        return jobs_list

    async def update_metadata(self, job_id: str, metadata: dict[str, object]) -> None:
        """
        Atualiza metadata de um job.

        Busca o job em todos os diretórios e atualiza o arquivo.

        Args:
            job_id: ID do job
            metadata: Novo metadata (será mesclado com o existente)
        """
        # Buscar job em todos os diretórios
        for dir_path in [self.jobs_dir, self.processing_dir, self.completed_dir, self.failed_dir]:
            job_file = dir_path / f"{job_id}.json"
            if job_file.exists():
                try:
                    job_data = json.loads(job_file.read_text(encoding="utf-8"))

                    # Atualiza worktree_path se presente no metadata
                    if "worktree_path" in metadata:
                        job_data["worktree_path"] = str(metadata["worktree_path"])

                    # Atualiza branch_name se presente
                    if "branch_name" in metadata:
                        job_data["branch_name"] = str(metadata["branch_name"])

                    # Mescla com metadata existente
                    if "metadata" not in job_data:
                        job_data["metadata"] = {}
                    job_data["metadata"].update(metadata)

                    # Salva atualizações
                    job_file.write_text(json.dumps(job_data, indent=2), encoding="utf-8")
                    return

                except Exception:
                    continue


# Import para manter compatibilidade
InMemoryJobQueue = FileBasedJobQueue
