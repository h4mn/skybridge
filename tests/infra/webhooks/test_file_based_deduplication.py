# -*- coding: utf-8 -*-
"""
Test deduplication functionality for FileBasedJobQueue.

Tests that delivery_id is properly saved/loaded and duplicate webhooks are detected.
"""
from __future__ import annotations

import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import pytest

from core.webhooks.domain import WebhookEvent, WebhookJob, WebhookSource
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
    """Cria evento de webhook de exemplo com delivery_id."""
    return WebhookEvent(
        source=WebhookSource.GITHUB,
        event_type="issues.opened",
        event_id="12345",
        payload={"issue": {"number": 225}},
        received_at=datetime.utcnow(),
        delivery_id="test-delivery-123",  # Importante para deduplicação
    )


@pytest.mark.asyncio
async def test_exists_by_delivery_id(temp_queue_dir, sample_event):
    """Deve verificar se delivery_id já foi processado."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    # Inicialmente não existe
    assert await queue.exists_by_delivery("test-delivery-123") is False

    # Enfileira job com delivery_id
    job = WebhookJob.create(sample_event)
    await queue.enqueue(job)

    # Agora existe
    assert await queue.exists_by_delivery("test-delivery-123") is True


@pytest.mark.asyncio
async def test_duplicate_webhook_same_delivery_id(temp_queue_dir):
    """Deve identificar webhooks duplicados pelo delivery_id."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    # Cria dois jobs com o MESMO delivery_id
    event1 = WebhookEvent(
        source=WebhookSource.GITHUB,
        event_type="issues.opened",
        event_id="1",
        payload={"issue": {"number": 1}},
        received_at=datetime.utcnow(),
        delivery_id="same-delivery-abc",  # MESMO delivery_id
    )
    event2 = WebhookEvent(
        source=WebhookSource.GITHUB,
        event_type="issues.opened",
        event_id="2",
        payload={"issue": {"number": 1}},
        received_at=datetime.utcnow(),
        delivery_id="same-delivery-abc",  # MESMO delivery_id
    )
    job1 = WebhookJob.create(event1)
    job2 = WebhookJob.create(event2)

    # Enfileira primeiro
    await queue.enqueue(job1)
    assert await queue.exists_by_delivery("same-delivery-abc") is True

    # Segundo job tem mesmo delivery_id - seria detectado como duplicata
    assert await queue.exists_by_delivery("same-delivery-abc") is True


@pytest.mark.asyncio
async def test_different_webhooks_different_delivery_ids(temp_queue_dir):
    """Deve tratar webhooks diferentes com delivery_ids diferentes."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    event1 = WebhookEvent(
        source=WebhookSource.GITHUB,
        event_type="issues.opened",
        event_id="1",
        payload={"issue": {"number": 1}},
        received_at=datetime.utcnow(),
        delivery_id="delivery-1",  # Delivery_id diferente
    )
    event2 = WebhookEvent(
        source=WebhookSource.GITHUB,
        event_type="issues.opened",
        event_id="2",
        payload={"issue": {"number": 2}},
        received_at=datetime.utcnow(),
        delivery_id="delivery-2",  # Delivery_id diferente
    )
    job1 = WebhookJob.create(event1)
    job2 = WebhookJob.create(event2)

    # Enfileira ambos
    await queue.enqueue(job1)
    await queue.enqueue(job2)

    # Ambos delivery_ids foram registrados
    assert await queue.exists_by_delivery("delivery-1") is True
    assert await queue.exists_by_delivery("delivery-2") is True


@pytest.mark.asyncio
async def test_webhook_without_delivery_id(temp_queue_dir):
    """Deve tratar webhooks sem delivery_id (legado)."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    event = WebhookEvent(
        source=WebhookSource.GITHUB,
        event_type="issues.opened",
        event_id="1",
        payload={"issue": {"number": 1}},
        received_at=datetime.utcnow(),
        delivery_id=None,  # Sem delivery_id
    )
    job = WebhookJob.create(event)

    # Enfileira sem erro
    await queue.enqueue(job)

    # Não existe em delivery_ids
    assert await queue.exists_by_delivery("any-delivery") is False


@pytest.mark.asyncio
async def test_delivery_id_persists_after_dequeue(temp_queue_dir, sample_event):
    """Deve manter delivery_id registrado após dequeue."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    job = WebhookJob.create(sample_event)
    await queue.enqueue(job)

    # Dequeue move para processing/
    await queue.dequeue()

    # Delivery_id ainda deve ser encontrado (em processing/)
    assert await queue.exists_by_delivery("test-delivery-123") is True


@pytest.mark.asyncio
async def test_delivery_id_persists_after_complete(temp_queue_dir, sample_event):
    """Deve manter delivery_id registrado após complete."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    job = WebhookJob.create(sample_event)
    job_id = await queue.enqueue(job)

    await queue.dequeue()
    await queue.complete(job_id)

    # Delivery_id ainda deve ser encontrado (em completed/)
    assert await queue.exists_by_delivery("test-delivery-123") is True


@pytest.mark.asyncio
async def test_delivery_id_persists_after_fail(temp_queue_dir, sample_event):
    """Deve manter delivery_id registrado após fail."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    job = WebhookJob.create(sample_event)
    job_id = await queue.enqueue(job)

    await queue.dequeue()
    await queue.fail(job_id, "Test error")

    # Delivery_id ainda deve ser encontrado (em failed/)
    assert await queue.exists_by_delivery("test-delivery-123") is True


@pytest.mark.asyncio
async def test_delivery_id_saved_in_json(temp_queue_dir, sample_event):
    """Deve salvar delivery_id no arquivo JSON."""
    import json

    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    job = WebhookJob.create(sample_event)
    job_id = await queue.enqueue(job)

    # Ler arquivo JSON
    job_file = temp_queue_dir / "jobs" / f"{job_id}.json"
    job_data = json.loads(job_file.read_text(encoding="utf-8"))

    # Verificar que delivery_id foi salvo
    assert job_data["event"]["delivery_id"] == "test-delivery-123"


@pytest.mark.asyncio
async def test_delivery_id_loaded_from_json(temp_queue_dir, sample_event):
    """Deve carregar delivery_id do arquivo JSON."""
    queue = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    job = WebhookJob.create(sample_event)
    job_id = await queue.enqueue(job)

    # Criar NOVA instância da fila (simula processo diferente)
    queue2 = FileBasedJobQueue(queue_dir=str(temp_queue_dir))

    # Buscar job
    loaded_job = await queue2.get_job(job_id)

    # Verificar que delivery_id foi carregado
    assert loaded_job is not None
    assert loaded_job.event.delivery_id == "test-delivery-123"
