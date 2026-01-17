# -*- coding: utf-8 -*-
"""
Unit tests for Webhook Adapters.

Testa InMemoryJobQueue e GitHubSignatureVerifier.
"""
import pytest

from infra.webhooks.adapters.in_memory_queue import (
    InMemoryJobQueue,
)
from infra.webhooks.adapters.github_signature_verifier import (
    GitHubSignatureVerifier,
)
from core.webhooks.domain import (
    WebhookEvent,
    WebhookJob,
    WebhookSource,
    JobStatus,
)
from datetime import datetime


class TestInMemoryJobQueue:
    """Testa adapter InMemoryJobQueue."""

    @pytest.fixture
    def job_queue(self):
        """Retorna instância da fila."""
        return InMemoryJobQueue()

    @pytest.fixture
    def sample_job(self):
        """Retorna job de exemplo."""
        event = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="12345",
            payload={"issue": {"number": 225}},
            received_at=datetime.utcnow(),
        )
        return WebhookJob.create(event)

    @pytest.mark.asyncio
    async def test_enqueue_job(self, job_queue, sample_job):
        """Deve enfileir job com sucesso."""
        job_id = await job_queue.enqueue(sample_job)

        assert job_id == sample_job.job_id
        assert job_queue.size() == 1

    @pytest.mark.asyncio
    async def test_dequeue_job(self, job_queue, sample_job):
        """Deve desenfileir job com sucesso."""
        await job_queue.enqueue(sample_job)

        job = await job_queue.dequeue()

        assert job is not None
        assert job.job_id == sample_job.job_id

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self, job_queue):
        """Deve retornar None quando fila está vazia."""
        job = await job_queue.dequeue()

        assert job is None

    @pytest.mark.asyncio
    async def test_get_job(self, job_queue, sample_job):
        """Deve buscar job por ID."""
        await job_queue.enqueue(sample_job)

        job = await job_queue.get_job(sample_job.job_id)

        assert job is not None
        assert job.job_id == sample_job.job_id

    @pytest.mark.asyncio
    async def test_complete_job(self, job_queue, sample_job):
        """Deve marcar job como completado."""
        await job_queue.enqueue(sample_job)

        await job_queue.complete(sample_job.job_id)

        job = await job_queue.get_job(sample_job.job_id)
        assert job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_fail_job(self, job_queue, sample_job):
        """Deve marcar job como falhou."""
        await job_queue.enqueue(sample_job)

        await job_queue.fail(sample_job.job_id, "Test error")

        job = await job_queue.get_job(sample_job.job_id)
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Test error"

    def test_size_empty_queue(self, job_queue):
        """Deve retornar 0 para fila vazia."""
        assert job_queue.size() == 0

    @pytest.mark.asyncio
    async def test_size_with_jobs(self, job_queue, sample_job):
        """Deve retornar número de jobs na fila."""
        # enqueue é síncrono internamente, mas retorna awaitable
        # Cria dois jobs diferentes para evitar duplicação de job_id
        from core.webhooks.domain import WebhookEvent

        event1 = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="1",
            payload={"issue": {"number": 1}},
            received_at=datetime.utcnow(),
        )
        event2 = WebhookEvent(
            source=WebhookSource.GITHUB,
            event_type="issues.opened",
            event_id="2",
            payload={"issue": {"number": 2}},
            received_at=datetime.utcnow(),
        )
        from core.webhooks.domain import WebhookJob
        job1 = WebhookJob.create(event1)
        job2 = WebhookJob.create(event2)

        await job_queue.enqueue(job1)
        await job_queue.enqueue(job2)

        assert job_queue.size() == 2

    @pytest.mark.asyncio
    async def test_clear_queue(self, job_queue, sample_job):
        """Deve limpar todos os jobs."""
        await job_queue.enqueue(sample_job)
        job_queue.clear()

        assert job_queue.size() == 0


class TestGitHubSignatureVerifier:
    """Testa verificador de assinatura do GitHub."""

    @pytest.fixture
    def verifier(self):
        """Retorna verificador de assinatura."""
        return GitHubSignatureVerifier()

    def test_header_name(self, verifier):
        """Deve ter nome de header correto."""
        assert verifier.header_name == "X-Hub-Signature-256"

    def test_extract_signature_from_headers(self, verifier):
        """Deve extrair assinatura dos headers."""
        headers = {
            "X-Hub-Signature-256": "sha256=abc123...",
            "Content-Type": "application/json",
        }

        signature = verifier.extract_signature(headers)

        assert signature == "sha256=abc123..."

    def test_extract_signature_returns_none_when_missing(self, verifier):
        """Deve retornar None quando header não existe."""
        headers = {"Content-Type": "application/json"}

        signature = verifier.extract_signature(headers)

        assert signature is None

    def test_verify_valid_signature(self, verifier):
        """Deve verificar assinatura válida."""
        secret = "test_secret"
        payload = b'{"test": "data"}'

        # Gera assinatura válida
        import hmac
        import hashlib

        mac = hmac.new(secret.encode(), payload, hashlib.sha256)
        expected_signature = "sha256=" + mac.hexdigest()

        assert verifier.verify(payload, expected_signature, secret) is True

    def test_verify_invalid_signature(self, verifier):
        """Deve rejeitar assinatura inválida."""
        secret = "test_secret"
        payload = b'{"test": "data"}'

        assert verifier.verify(payload, "sha256=wrong", secret) is False

    def test_verify_signature_without_prefix(self, verifier):
        """Deve rejeitar assinatura sem prefixo sha256=."""
        secret = "test_secret"
        payload = b'{"test": "data"}'

        assert verifier.verify(payload, "abc123", secret) is False

    def test_is_valid_format(self, verifier):
        """Deve validar formato de assinatura."""
        assert verifier.is_valid_format("sha256=abc123") is True
        assert verifier.is_valid_format("abc123") is False
