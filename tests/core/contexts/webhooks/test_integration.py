# -*- coding: utf-8 -*-
"""
Integration tests for Webhook flow.

Testa o fluxo completo: webhook → job → queue → handler.

DOC: ADR024 - Testes usam isolated_job_queue para isolamento total.
DOC: ADR024 - Nenhum teste toca data/jobs.db de produção.
"""
from datetime import datetime
import asyncio

import pytest

from core.webhooks.domain import (
    WebhookEvent,
    WebhookJob,
    WebhookSource,
    JobStatus,
)
from core.webhooks.application.webhook_processor import (
    WebhookProcessor,
)
from infra.domain_events.in_memory_event_bus import InMemoryEventBus


class TestWebhookIntegration:
    """Testa integração do fluxo de webhook."""

    @pytest.fixture
    def event_bus(self):
        """Event bus para testes."""
        return InMemoryEventBus()

    @pytest.fixture
    def job_queue(self, isolated_job_queue):
        """
        Retorna fila isolada para este teste.

        DOC: ADR024 - Usa isolated_job_queue ao invés de singleton.
        DOC: ADR024 - Garante isolamento total entre testes.
        """
        return isolated_job_queue

    @pytest.fixture
    def processor(self, job_queue, event_bus):
        """Retorna processor."""
        return WebhookProcessor(job_queue, event_bus)

    @pytest.mark.asyncio
    async def test_full_github_issue_flow(self, processor):
        """Testa fluxo completo: webhook → enfileirar → recuperar."""
        payload = {
            "issue": {"number": 42, "title": "Test issue", "body": "Test body"}
        }

        # 1. Processa webhook
        result = await processor.process_github_issue(
            payload=payload,
            event_type="issues.opened",
            signature="sha256=test",
        )

        # 2. Verifica que foi enfileirado
        assert result.is_ok
        job_id = result.value

        # 3. Recupera job da fila
        job = await processor.job_queue.get_job(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.status == JobStatus.PENDING
        assert job.issue_number == 42

    @pytest.mark.asyncio
    async def test_multiple_jobs_sequential(self, processor):
        """Testa processamento de múltiplos jobs em sequência."""
        for i in range(1, 4):  # 1, 2, 3 em vez de 0, 1, 2 (0 é falsy)
            payload = {"issue": {"number": i, "title": f"Issue {i}"}}

            result = await processor.process_github_issue(
                payload=payload,
                event_type="issues.opened",
                signature=f"sha256=signature{i}",
            )

            assert result.is_ok

        # Verifica que 3 jobs foram enfileirados
        assert processor.job_queue.size() == 3

    @pytest.mark.asyncio
    async def test_dequeue_processes_in_order(self, processor):
        """Testa que dequeue processa jobs na ordem FIFO."""
        # Enfileira 3 jobs
        for i in range(1, 4):  # 1, 2, 3 (0 é falsy)
            payload = {"issue": {"number": i, "title": f"Issue {i}"}}
            await processor.process_github_issue(
                payload=payload,
                event_type="issues.opened",
                signature=f"sha256=signature{i}",
            )

        # Desenfileira e verifica ordem
        previous_number = 0
        for _ in range(3):
            job = await processor.job_queue.dequeue()
            assert job is not None
            assert job.issue_number == previous_number + 1
            previous_number = job.issue_number

    @pytest.mark.asyncio
    async def test_job_lifecycle(self, processor):
        """Testa ciclo de vida completo do job."""
        payload = {"issue": {"number": 99, "title": "Lifecycle test"}}

        # Create
        result = await processor.process_github_issue(
            payload=payload,
            event_type="issues.opened",
            signature="sha256=test",
        )
        assert result.is_ok
        job_id = result.value

        # Retrieve
        job = await processor.job_queue.get_job(job_id)
        assert job.status == JobStatus.PENDING

        # Mark processing
        job.mark_processing()
        assert job.status == JobStatus.PROCESSING

        # Mark completed
        job.mark_completed()
        assert job.status == JobStatus.COMPLETED

        # Verify cleanup eligibility
        assert job.can_cleanup() is True


class TestJobQueuePersistence:
    """Testa persistência da fila (isolada)."""

    @pytest.fixture
    def event_bus(self):
        """Event bus para testes."""
        return InMemoryEventBus()

    @pytest.mark.asyncio
    async def test_job_persists_across_processors(self, isolated_job_queue, event_bus):
        """
        Job deve persistir entre diferentes processadores.

        DOC: ADR024 - Usa isolated_job_queue para isolamento.
        """
        processor1 = WebhookProcessor(isolated_job_queue, event_bus)
        processor2 = WebhookProcessor(isolated_job_queue, event_bus)

        payload = {"issue": {"number": 77, "title": "Persistence test"}}

        # Enfileira com processor1
        result1 = await processor1.process_github_issue(
            payload=payload,
            event_type="issues.opened",
            signature="sha256=test",
        )
        assert result1.is_ok

        # Recupera com processor2
        job_id = result1.value
        job = await processor2.job_queue.get_job(job_id)
        assert job is not None
        assert job.issue_number == 77
