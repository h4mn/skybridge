# -*- coding: utf-8 -*-
"""Testes unitários para BaseWorker."""

import pytest

from src.core.paper.facade.sandbox.workers.base import BaseWorker


class MockWorker(BaseWorker):
    """Worker de teste."""

    def __init__(self, name: str = "test_worker"):
        super().__init__(name)
        self.tick_count = 0
        self.tick_error: Exception | None = None

    async def _do_tick(self) -> None:
        self.tick_count += 1
        if self.tick_error:
            raise self.tick_error


class TestBaseWorker:
    """Testes do BaseWorker."""

    @pytest.mark.asyncio
    async def test_start_define_running_true(self):
        """Worker deve marcar is_running=True após start."""
        worker = MockWorker()

        assert not worker.is_running
        await worker.start()
        assert worker.is_running

    @pytest.mark.asyncio
    async def test_stop_define_running_false(self):
        """Worker deve marcar is_running=False após stop."""
        worker = MockWorker()
        await worker.start()

        await worker.stop()

        assert not worker.is_running

    @pytest.mark.asyncio
    async def test_tick_incrementa_contador(self):
        """Tick deve incrementar contador quando running."""
        worker = MockWorker()
        await worker.start()

        await worker.tick()

        assert worker.tick_count == 1

    @pytest.mark.asyncio
    async def test_tick_ignorado_quando_parado(self):
        """Tick não deve executar quando worker parado."""
        worker = MockWorker()

        await worker.tick()

        assert worker.tick_count == 0

    @pytest.mark.asyncio
    async def test_tick_trata_erro_sem_interromper(self):
        """Tick deve capturar erro e não propagar."""
        worker = MockWorker()
        worker.tick_error = RuntimeError("Erro simulado")
        await worker.start()

        # Não deve propagar exceção
        await worker.tick()

        assert worker.tick_count == 1  # Incrementou antes do erro
        assert worker.is_running  # Continua rodando

    @pytest.mark.asyncio
    async def test_name_property_retorna_nome(self):
        """Property name deve retornar nome do worker."""
        worker = MockWorker(name="custom_name")

        assert worker.name == "custom_name"
