# -*- coding: utf-8 -*-
"""
Testes de deduplicação para FileBasedJobQueue (Bug #36).

Verifica que webhooks com o mesmo delivery_id não são processados múltiplas vezes.
"""
import asyncio
import json
import tempfile
from pathlib import Path
from shutil import rmtree
from datetime import datetime

import pytest

from infra.webhooks.adapters.file_based_job_queue import FileBasedJobQueue
from core.webhooks.domain import WebhookEvent, WebhookJob, WebhookSource


class TestFileBasedJobQueueDeduplication:
    """Testa funcionalidade de deduplicação do FileBasedJobQueue."""

    @pytest.fixture
    def temp_queue_dir(self):
        """Diretório temporário para testes."""
        temp_dir = tempfile.mkdtemp(prefix="test_queue_")
        yield temp_dir
        # Cleanup
        try:
            rmtree(temp_dir)
        except Exception:
            pass

    @pytest.fixture
    def job_queue(self, temp_queue_dir):
        """Instância de FileBasedJobQueue para testes."""
        return FileBasedJobQueue(queue_dir=temp_queue_dir)

    @pytest.fixture
    def sample_job_with_delivery(self):
        """Job de exemplo com delivery_id."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="123",
            payload={
                "action": "opened",
                "issue": {"number": 36, "title": "Test issue"},
                "repository": {"full_name": "h4mn/skybridge"}
            },
            received_at=datetime.utcnow(),
            signature="sig123",
            delivery_id="test-delivery-abc123",  # Importante para deduplicação
        )
        return WebhookJob.create(event)

    @pytest.mark.asyncio
    async def test_delivery_id_is_persisted(self, job_queue, sample_job_with_delivery):
        """Delivery ID deve ser persistido no arquivo JSON."""
        # Enfileira job
        job_id = await job_queue.enqueue(sample_job_with_delivery)

        # Lê o arquivo JSON diretamente
        job_file = Path(job_queue.jobs_dir) / f"{job_id}.json"
        assert job_file.exists()

        job_data = json.loads(job_file.read_text(encoding="utf-8"))
        event_data = job_data.get("event", {})

        # Verifica que delivery_id foi persistido
        assert "delivery_id" in event_data
        assert event_data["delivery_id"] == "test-delivery-abc123"

    @pytest.mark.asyncio
    async def test_exists_by_delivery_finds_job(self, job_queue, sample_job_with_delivery):
        """exists_by_delivery deve encontrar job pelo delivery_id."""
        delivery_id = "test-delivery-abc123"

        # Antes de enfileirar, não existe
        assert not await job_queue.exists_by_delivery(delivery_id)

        # Enfileira job
        await job_queue.enqueue(sample_job_with_delivery)

        # Agora deve existir
        assert await job_queue.exists_by_delivery(delivery_id)

    @pytest.mark.asyncio
    async def test_duplicate_webhook_same_delivery_id(self, job_queue, sample_job_with_delivery):
        """Webhook duplicado com mesmo delivery_id deve ser detectado."""
        delivery_id = "test-delivery-abc123"

        # Primeira vez - não existe
        assert not await job_queue.exists_by_delivery(delivery_id)

        # Enfileira primeiro job
        job_id_1 = await job_queue.enqueue(sample_job_with_delivery)

        # Agora existe
        assert await job_queue.exists_by_delivery(delivery_id)

        # Tenta enfileirar segundo job com mesmo delivery_id
        # (simulando reenvio do webhook pelo GitHub)
        assert await job_queue.exists_by_delivery(delivery_id)

    @pytest.mark.asyncio
    async def test_exists_by_delivery_checks_all_directories(self, job_queue, sample_job_with_delivery):
        """exists_by_delivery deve buscar em todos os diretórios (jobs, processing, completed, failed)."""
        delivery_id = "test-delivery-abc123"

        # Enfileira job
        job_id = await job_queue.enqueue(sample_job_with_delivery)
        assert await job_queue.exists_by_delivery(delivery_id)

        # Move para processing (dequeue)
        job = await job_queue.dequeue()
        assert job is not None
        assert await job_queue.exists_by_delivery(delivery_id)

        # Marca como completed
        await job_queue.complete(job_id)
        assert await job_queue.exists_by_delivery(delivery_id)

    @pytest.mark.asyncio
    async def test_webhook_without_delivery_id(self, job_queue):
        """Webhook sem delivery_id deve funcionar (compatibilidade com legado)."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="123",
            payload={"action": "opened", "issue": {"number": 36}},
            received_at=datetime.utcnow(),
            delivery_id=None,  # Sem delivery_id
        )
        job = WebhookJob.create(event)

        # Enfileira sem erro
        job_id = await job_queue.enqueue(job)
        assert job_id is not None

        # exists_by_delivery deve retornar False para delivery_id None
        assert not await job_queue.exists_by_delivery(None)

    @pytest.mark.asyncio
    async def test_different_webhooks_different_delivery_ids(self, job_queue):
        """Webhooks diferentes com delivery_ids diferentes devem ser tratados separadamente."""
        event1 = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="1",
            payload={"action": "opened", "issue": {"number": 1}},
            received_at=datetime.utcnow(),
            delivery_id="delivery-1",
        )
        job1 = WebhookJob.create(event1)

        event2 = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="2",
            payload={"action": "opened", "issue": {"number": 2}},
            received_at=datetime.utcnow(),
            delivery_id="delivery-2",
        )
        job2 = WebhookJob.create(event2)

        # Enfileira ambos
        job_id_1 = await job_queue.enqueue(job1)
        job_id_2 = await job_queue.enqueue(job2)

        assert job_id_1 != job_id_2

        # Cada delivery_id deve existir
        assert await job_queue.exists_by_delivery("delivery-1")
        assert await job_queue.exists_by_delivery("delivery-2")

        # Mas não deve confundir
        assert not await job_queue.exists_by_delivery("delivery-3")
