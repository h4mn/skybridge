# -*- coding: utf-8 -*-
"""
Teste para SQLiteJobQueue.

PRD018 Fase 2 - Plano B: SQLite como fila de jobs.

Valida:
- Operações básicas (enqueue, dequeue, complete, fail)
- Concorrência (múltiplos workers)
- Deduplicação de webhooks
- Recuperação de falha
- Cleanup e VACUUM
"""
from __future__ import annotations

import asyncio
import gc
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from core.webhooks.domain import JobStatus, WebhookEvent, WebhookJob, WebhookSource
from infra.webhooks.adapters.sqlite_job_queue import SQLiteJobQueue


@pytest.fixture
def temp_db_path():
    """Cria banco de dados temporário para testes."""
    db_path = Path(tempfile.mktemp(suffix=".db"))
    yield db_path
    # Fechar todas as conexões explicitamente
    gc.collect()
    # Cleanup
    for ext in ["", "-wal", "-shm"]:
        test_path = db_path.with_suffix(f".db{ext}" if ext else ".db")
        if test_path.exists():
            try:
                test_path.unlink()
            except PermissionError:
                # Windows às vezes mantém locks, ignorar silenciosamente
                pass


@pytest.fixture
def sample_event():
    """Cria evento de webhook de exemplo."""
    return WebhookEvent(
        source=WebhookSource.GITHUB,
        event_type="issues.opened",
        event_id="test-delivery-123",
        payload={
            "action": "opened",
            "issue": {
                "number": 42,
                "title": "Test Issue",
                "body": "Test body",
            },
            "repository": {
                "owner": {"login": "test-owner"},
                "name": "test-repo",
            },
        },
        received_at=datetime.utcnow(),
        signature="test-signature",
    )


@pytest.fixture
def sample_job(sample_event):
    """Cria job de exemplo."""
    return WebhookJob(
        job_id="test-job-001",
        correlation_id="test-corr-001",
        created_at=datetime.utcnow(),
        status=JobStatus.PENDING,
        event=sample_event,
        metadata={"test": True},
    )


@pytest.mark.asyncio
async def test_enqueue_dequeue_complete(temp_db_path, sample_job):
    """Testa fluxo completo: enqueue → dequeue → complete."""
    queue = SQLiteJobQueue(db_path=str(temp_db_path))

    # Enqueue
    job_id = await queue.enqueue(sample_job)
    assert job_id == "test-job-001"

    # Verificar tamanho
    assert queue.size() == 1

    # Dequeue
    dequeued_job = await queue.dequeue(timeout_seconds=1.0)
    assert dequeued_job is not None
    assert dequeued_job.job_id == "test-job-001"
    assert dequeued_job.event.payload["issue"]["number"] == 42

    # Complete
    await queue.complete(
        dequeued_job.job_id,
        result={"status": "success", "changes": ["file1.py"]},
    )

    # Verificar métricas
    metrics = await queue.get_metrics()
    assert metrics["queue_size"] == 0
    assert metrics["total_enqueued"] == 1
    assert metrics["total_completed"] == 1
    assert metrics["success_rate"] == 1.0


@pytest.mark.asyncio
async def test_concurrent_dequeue_no_duplicates(temp_db_path, sample_event):
    """Testa que 3 workers concorrentes não processam o mesmo job."""
    queue = SQLiteJobQueue(db_path=str(temp_db_path))

    # Enfileirar 5 jobs
    for i in range(5):
        job = WebhookJob(
            job_id=f"concurrent-job-{i:03d}",
            correlation_id=f"concurrent-corr-{i}",
            created_at=datetime.utcnow(),
            status=JobStatus.PENDING,
            event=sample_event,
            metadata={"index": i},
        )
        await queue.enqueue(job)

    # Função worker
    async def worker(worker_id: int):
        jobs_processed = []
        for _ in range(3):
            job = await queue.dequeue(timeout_seconds=1.0)
            if job:
                jobs_processed.append(job.job_id)
                await queue.complete(job.job_id)
        return jobs_processed

    # Executar 3 workers simultâneos
    results = await asyncio.gather(
        worker(1),
        worker(2),
        worker(3),
    )

    # Verificar duplicações
    all_jobs = []
    for worker_jobs in results:
        all_jobs.extend(worker_jobs)

    unique_jobs = set(all_jobs)
    duplicates = len(all_jobs) - len(unique_jobs)

    assert len(all_jobs) == 5, "Todos os jobs devem ser processados"
    assert len(unique_jobs) == 5, "Todos os jobs devem ser únicos"
    assert duplicates == 0, f"Não deve haver duplicados, encontrou {duplicates}"


@pytest.mark.asyncio
async def test_delivery_deduplication(temp_db_path):
    """Testa deduplicação de webhooks por delivery_id."""
    queue = SQLiteJobQueue(db_path=str(temp_db_path))

    delivery_id = "test-delivery-123"

    # Primeira vez não existe
    exists = await queue.exists_by_delivery(delivery_id)
    assert exists is False

    # Marcar como processado
    await queue.mark_delivery_processed(delivery_id, "job-001")

    # Agora deve existir
    exists = await queue.exists_by_delivery(delivery_id)
    assert exists is True


@pytest.mark.asyncio
async def test_failure_recovery(temp_db_path, sample_job):
    """Testa recuperação de falha."""
    queue = SQLiteJobQueue(db_path=str(temp_db_path))

    # Enqueue
    await queue.enqueue(sample_job)

    # Dequeue
    dequeued = await queue.dequeue(timeout_seconds=1.0)
    assert dequeued is not None

    # Marcar como falhou
    await queue.fail(dequeued.job_id, "Erro simulado para teste")

    # Verificar métricas
    metrics = await queue.get_metrics()
    assert metrics["total_failed"] == 1


@pytest.mark.asyncio
async def test_cleanup_and_vacuum(temp_db_path, sample_event):
    """Testa cleanup de jobs antigos e VACUUM."""
    queue = SQLiteJobQueue(db_path=str(temp_db_path))

    # Enfileirar 3 jobs
    for i in range(3):
        job = WebhookJob(
            job_id=f"cleanup-job-{i}",
            correlation_id=f"cleanup-corr-{i}",
            created_at=datetime.utcnow(),
            status=JobStatus.PENDING,
            event=sample_event,
            metadata={"index": i},
        )
        await queue.enqueue(job)

    # Completar jobs
    for i in range(3):
        job = await queue.dequeue(timeout_seconds=1.0)
        if job:
            await queue.complete(job.job_id)

    # Cleanup (jobs completados recentes não devem ser removidos)
    deleted = await queue.cleanup_old_jobs(older_than_days=1)
    assert deleted == 0, "Jobs recentes não devem ser removidos"

    # Vacuum
    await queue.vacuum()

    # Verificar que banco ainda existe
    assert temp_db_path.exists()


@pytest.mark.asyncio
async def test_get_job(temp_db_path, sample_job):
    """Testa buscar job por ID."""
    queue = SQLiteJobQueue(db_path=str(temp_db_path))

    # Enqueue
    await queue.enqueue(sample_job)

    # Get job
    found = await queue.get_job("test-job-001")
    assert found is not None
    assert found.job_id == "test-job-001"
    assert found.status == JobStatus.PENDING

    # Job não existente
    not_found = await queue.get_job("non-existent")
    assert not_found is None


@pytest.mark.asyncio
async def test_timeout_dequeue(temp_db_path):
    """Testa dequeue com timeout retorna None quando fila vazia."""
    queue = SQLiteJobQueue(db_path=str(temp_db_path))

    # Dequeue com fila vazia
    job = await queue.dequeue(timeout_seconds=0.5)
    assert job is None


@pytest.mark.asyncio
async def test_size_calculation(temp_db_path, sample_event):
    """Testa cálculo do tamanho da fila."""
    queue = SQLiteJobQueue(db_path=str(temp_db_path))

    # Fila vazia
    assert queue.size() == 0

    # Enfileirar 3 jobs
    for i in range(3):
        job = WebhookJob(
            job_id=f"size-job-{i}",
            correlation_id=f"size-corr-{i}",
            created_at=datetime.utcnow(),
            status=JobStatus.PENDING,
            event=sample_event,
        )
        await queue.enqueue(job)

    assert queue.size() == 3

    # Dequeue um
    await queue.dequeue(timeout_seconds=1.0)

    # Tamanho deve reduzir
    assert queue.size() == 2


@pytest.mark.asyncio
async def test_metrics_aggregation(temp_db_path, sample_event):
    """Testa agregação de métricas."""
    queue = SQLiteJobQueue(db_path=str(temp_db_path))

    # Enfileirar 5 jobs
    for i in range(5):
        job = WebhookJob(
            job_id=f"metrics-job-{i}",
            correlation_id=f"metrics-corr-{i}",
            created_at=datetime.utcnow(),
            status=JobStatus.PENDING,
            event=sample_event,
        )
        await queue.enqueue(job)

    # Completar 3 jobs
    for i in range(3):
        job = await queue.dequeue(timeout_seconds=1.0)
        if job:
            await queue.complete(job.job_id)

    # Falhar 1 job
    job = await queue.dequeue(timeout_seconds=1.0)
    if job:
        await queue.fail(job.job_id, "Test error")

    # Verificar métricas
    metrics = await queue.get_metrics()
    assert metrics["queue_size"] == 1  # 1 restante
    assert metrics["processing"] == 0
    assert metrics["completed"] == 3
    assert metrics["failed"] == 1
    assert metrics["total_enqueued"] == 5
    assert metrics["total_completed"] == 3
    assert metrics["total_failed"] == 1
    assert 0.6 <= metrics["success_rate"] <= 0.7  # 3/5 = 0.6


@pytest.mark.asyncio
async def test_multiple_instances_share_queue(temp_db_path, sample_job):
    """Testa que múltiplas instâncias compartilham a mesma fila."""
    # Instância 1: enfileirar
    queue1 = SQLiteJobQueue(db_path=str(temp_db_path))
    await queue1.enqueue(sample_job)

    # Instância 2: deve ver o job
    queue2 = SQLiteJobQueue(db_path=str(temp_db_path))
    assert queue2.size() == 1

    # Instância 2: desenfileirar
    dequeued = await queue2.dequeue(timeout_seconds=1.0)
    assert dequeued is not None
    assert dequeued.job_id == "test-job-001"

    # Instância 1: deve ver fila vazia
    assert queue1.size() == 0


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v"])
