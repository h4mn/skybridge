# -*- coding: utf-8 -*-
"""
Test E2E para FileBasedJobQueue.

Valida o fluxo completo da fila:
1. Enfileirar job
2. Desenfileirar job
3. Completar job
4. Verificar métricas

Este teste simula o uso real entre webhook server e worker.
"""
from __future__ import annotations

import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import pytest

from core.webhooks.domain import WebhookEvent, WebhookJob, WebhookSource, JobStatus
from infra.webhooks.adapters.file_based_job_queue import FileBasedJobQueue


@pytest.fixture
def temp_queue_dir():
    """Cria diretório temporário para testes."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


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


@pytest.mark.asyncio
async def test_enqueue_persists_job(temp_queue_dir, sample_event):
    """Testa que enqueue persiste job em arquivo."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    job = WebhookJob.create(sample_event)
    job_id = await queue.enqueue(job)

    # Verificar que arquivo foi criado
    job_file = temp_queue_dir / "jobs" / f"{job_id}.json"
    assert job_file.exists(), "Arquivo do job deve existir em jobs/"

    # Verificar que job_id está na fila
    queue_data = queue._load_queue()
    assert job_id in queue_data, "job_id deve estar na fila"


@pytest.mark.asyncio
async def test_dequeue_moves_to_processing(temp_queue_dir, sample_event):
    """Testa que dequeue move job para processing/."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    job = WebhookJob.create(sample_event)
    job_id = await queue.enqueue(job)

    # Dequeue
    dequeued_job = await queue.dequeue()

    assert dequeued_job is not None
    assert dequeued_job.job_id == job_id

    # Verificar que arquivo foi movido para processing/
    processing_file = temp_queue_dir / "processing" / f"{job_id}.json"
    assert processing_file.exists(), "Arquivo deve estar em processing/"

    # Verificar que fila está vazia
    assert queue.size() == 0, "Fila deve estar vazia após dequeue"


@pytest.mark.asyncio
async def test_complete_moves_to_completed(temp_queue_dir, sample_event):
    """Testa que complete move job para completed/."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    job = WebhookJob.create(sample_event)
    job_id = await queue.enqueue(job)

    await queue.dequeue()
    await queue.complete(job_id, result={"status": "success"})

    # Verificar que arquivo foi movido para completed/
    completed_file = temp_queue_dir / "completed" / f"{job_id}.json"
    assert completed_file.exists(), "Arquivo deve estar em completed/"

    # Verificar resultado foi salvo
    import json
    job_data = json.loads(completed_file.read_text())
    assert job_data["status"] == "completed"
    assert job_data["result"]["status"] == "success"
    assert "completed_at" in job_data


@pytest.mark.asyncio
async def test_fail_moves_to_failed(temp_queue_dir, sample_event):
    """Testa que fail move job para failed/."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    job = WebhookJob.create(sample_event)
    job_id = await queue.enqueue(job)

    await queue.dequeue()
    await queue.fail(job_id, error="Test error")

    # Verificar que arquivo foi movido para failed/
    failed_file = temp_queue_dir / "failed" / f"{job_id}.json"
    assert failed_file.exists(), "Arquivo deve estar em failed/"

    # Verificar erro foi salvo
    import json
    job_data = json.loads(failed_file.read_text())
    assert job_data["status"] == "failed"
    assert job_data["error"] == "Test error"
    assert "failed_at" in job_data


@pytest.mark.asyncio
async def test_metrics_calculations(temp_queue_dir, sample_event):
    """Testa cálculo de métricas."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    # Enfileirar alguns jobs
    for i in range(5):
        event = sample_event
        event.event_id = f"test-delivery-{i}"
        job = WebhookJob.create(event)
        await queue.enqueue(job)

    # Desenfileirar e completar 3 jobs
    for _ in range(3):
        job = await queue.dequeue()
        await queue.complete(job.job_id)

    # Obter métricas
    metrics = queue.get_metrics()

    # Verificar métricas básicas
    assert metrics["enqueue_count"] == 5
    assert metrics["dequeue_count"] == 3
    assert metrics["complete_count"] == 3
    assert metrics["queue_size"] == 2  # 2 restantes

    # Verificar latências (deve ter valores)
    assert metrics["enqueue_latency_avg_ms"] > 0
    assert metrics["dequeue_latency_avg_ms"] > 0

    # Verificar disk usage
    assert metrics["disk_usage_mb"] > 0


@pytest.mark.asyncio
async def test_multiple_processes_share_queue(temp_queue_dir, sample_event):
    """
    Testa que múltiplos processos (simulados) compartilham a fila.

    Este é o teste CRÍTICO para validar o Problema #1.
    """
    # Processo 1: Webhook Server (enfileira)
    server_queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    job = WebhookJob.create(sample_event)
    job_id = await server_queue.enqueue(job)

    # Processo 2: Worker (desenfileira - NOVA INSTÂNCIA)
    worker_queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    # Worker deve ver o job enfileirado pelo server
    assert worker_queue.size() == 1, "Worker deve ver job enfileirado pelo server"

    dequeued_job = await worker_queue.dequeue()
    assert dequeued_job is not None
    assert dequeued_job.job_id == job_id, "Worker deve desenfileirar mesmo job"

    # Server deve ver fila vazia
    assert server_queue.size() == 0, "Server deve ver fila vazia após worker dequeue"


@pytest.mark.asyncio
async def test_wait_for_dequeue_timeout(temp_queue_dir):
    """Testa que wait_for_dequeue respeita timeout."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    # Tentar dequeue com timeout curto
    job = await queue.wait_for_dequeue(timeout=0.1)

    assert job is None, "Deve retornar None em timeout"


@pytest.mark.asyncio
async def test_get_job_finds_in_any_directory(temp_queue_dir, sample_event):
    """Testa que get_job encontra job em qualquer estado."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    job = WebhookJob.create(sample_event)
    job_id = await queue.enqueue(job)

    # Job deve ser encontrado em jobs/
    found = await queue.get_job(job_id)
    assert found is not None
    assert found.job_id == job_id

    # Dequeue move para processing/
    await queue.dequeue()

    # Job ainda deve ser encontrado
    found = await queue.get_job(job_id)
    assert found is not None
    assert found.job_id == job_id

    # Complete move para completed/
    await queue.complete(job_id)

    # Job ainda deve ser encontrado
    found = await queue.get_job(job_id)
    assert found is not None
    assert found.job_id == job_id


@pytest.mark.asyncio
async def test_metrics_persistence(temp_queue_dir, sample_event):
    """Testa que métricas persistem entre instâncias."""
    # Instância 1: enfileirar jobs
    queue1 = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    # Enfileirar mais de 10 jobs para forçar persistência
    for i in range(11):
        event = sample_event
        event.event_id = f"test-delivery-{i}"
        job = WebhookJob.create(event)
        await queue1.enqueue(job)

    # Forçar salvamento das métricas
    queue1._save_metrics()

    # Instância 2: carregar métricas
    queue2 = FileBasedJobQueue(queue_dir=str(temp_queue_dir))
    metrics = queue2.get_metrics()

    # Métricas devem persistir
    assert metrics["enqueue_count"] == 11
    assert metrics["queue_size"] == 11


@pytest.mark.asyncio
async def test_concurrent_enqueue(temp_queue_dir, sample_event):
    """Testa enfileiramento concorrente."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    # Enfileirar 10 jobs concorrentemente
    tasks = []
    for i in range(10):
        event = sample_event
        event.event_id = f"test-delivery-{i}"
        job = WebhookJob.create(event)
        tasks.append(queue.enqueue(job))

    # Aguardar todos completarem
    job_ids = await asyncio.gather(*tasks)

    # Verificar que todos foram enfileirados
    assert len(job_ids) == 10
    assert queue.size() == 10

    # Verificar que não há duplicatas
    assert len(set(job_ids)) == 10


def test_decision_score_calculator():
    """
    Testa calculadora de decisão de migração.

    Baseado em GUIA_DECISAO_MENSAGERIA.md

    Threshold: Score >= 5 indica migrar para Redis
    """
    # Cenário 1: Projeto pequeno - CONTINUAR STANDALONE
    metrics_small = {
        "jobs_per_hour": 5,
        "enqueue_latency_p95_ms": 40,
        "backlog_age_seconds": 60,
        "disk_usage_mb": 50,
    }
    score_small = calculate_migration_score(metrics_small)
    assert score_small < 3, f"Score pequeno ({score_small}) deve indicar continuar standalone (<3)"

    # Cenário 2: Projeto médio - AVALIAR MIGRAÇÃO (score médio)
    # Este cenário mostra transição (borderline)
    metrics_medium = {
        "jobs_per_hour": 15,
        "enqueue_latency_p95_ms": 80,
        "backlog_age_seconds": 180,
        "disk_usage_mb": 200,
    }
    score_medium = calculate_migration_score(metrics_medium)
    # Score médio indica monitorar ou avaliar (pode ser <5 dependendo dos valores)
    assert score_medium > score_small, "Score médio deve ser maior que pequeno"

    # Cenário 3: Projeto alto volume - MIGRAR AGORA
    metrics_large = {
        "jobs_per_hour": 25,
        "enqueue_latency_p95_ms": 150,
        "backlog_age_seconds": 480,
        "disk_usage_mb": 600,
    }
    score_large = calculate_migration_score(metrics_large)
    assert score_large >= 5, f"Score alto ({score_large}) deve indicar migração imediata (>=5)"

    # Verificar ordem: pequeno < médio < grande
    assert score_small < score_medium < score_large, "Scores devem crescer com carga"


def calculate_migration_score(metrics: dict) -> float:
    """
    Calcula score de decisão de migração (0-7).

    Baseado em GUIA_DECISAO_MENSAGERIA.md

    Score >= 5: Migrar para Redis
    Score < 5: Continuar Standalone
    """
    score = 0.0

    # Fator 1: Throughput (peso: 3)
    throughput = metrics["jobs_per_hour"]
    throughput_score = min(throughput / 20, 3)
    score += throughput_score

    # Fator 2: Latência (peso: 2)
    latency = metrics["enqueue_latency_p95_ms"]
    latency_score = min(latency / 100, 2)
    score += latency_score

    # Fator 3: Backlog Age (peso: 2)
    backlog_age = metrics["backlog_age_seconds"] / 60
    backlog_score = min(backlog_age / 5, 2)
    score += backlog_score

    # Fator 4: Disk Usage (peso: 1)
    disk = metrics["disk_usage_mb"]
    disk_score = min(disk / 500, 1)
    score += disk_score

    return score


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v"])
