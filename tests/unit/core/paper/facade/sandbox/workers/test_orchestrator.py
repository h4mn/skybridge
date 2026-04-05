# -*- coding: utf-8 -*-
"""Testes unitários para PaperOrchestrator."""

import asyncio

import pytest

from src.core.paper.facade.sandbox.orchestrator import PaperOrchestrator
from src.core.paper.facade.sandbox.workers.base import BaseWorker


class MockWorker(BaseWorker):
    """Worker de teste para orchestrator."""

    def __init__(self, name: str = "mock"):
        super().__init__(name)
        self.start_called = False
        self.stop_called = False
        self.tick_count = 0

    async def start(self) -> None:
        await super().start()
        self.start_called = True

    async def stop(self) -> None:
        await super().stop()
        self.stop_called = True

    async def _do_tick(self) -> None:
        self.tick_count += 1


class FailingWorker(BaseWorker):
    """Worker que falha no tick."""

    def __init__(self, name: str = "failing"):
        super().__init__(name)
        self.tick_count = 0

    async def _do_tick(self) -> None:
        self.tick_count += 1
        raise RuntimeError("Erro simulado no tick")


class TestPaperOrchestrator:
    """Testes do PaperOrchestrator."""

    def test_register_adiciona_worker(self):
        """Register deve adicionar worker ao dicionário."""
        orchestrator = PaperOrchestrator()
        worker = MockWorker()

        orchestrator.register(worker)

        assert orchestrator.worker_count == 1

    def test_register_rejeita_nome_duplicado(self):
        """Register deve rejeitar worker com nome duplicado."""
        orchestrator = PaperOrchestrator()
        orchestrator.register(MockWorker(name="duplo"))

        with pytest.raises(ValueError, match="já registrado"):
            orchestrator.register(MockWorker(name="duplo"))

    def test_unregister_remove_worker(self):
        """Unregister deve remover worker pelo nome."""
        orchestrator = PaperOrchestrator()
        worker = MockWorker(name="remover")
        orchestrator.register(worker)

        removed = orchestrator.unregister("remover")

        assert removed is worker
        assert orchestrator.worker_count == 0

    def test_unregister_retorna_none_se_nao_encontrado(self):
        """Unregister deve retornar None se worker não existe."""
        orchestrator = PaperOrchestrator()

        removed = orchestrator.unregister("inexistente")

        assert removed is None

    @pytest.mark.asyncio
    async def test_run_inicia_workers(self):
        """Run deve chamar start() de todos os workers."""
        orchestrator = PaperOrchestrator(interval_seconds=0.01)
        worker1 = MockWorker(name="w1")
        worker2 = MockWorker(name="w2")
        orchestrator.register(worker1)
        orchestrator.register(worker2)

        # Executa por 1 tick e para
        async def stop_after_tick():
            await asyncio.sleep(0.02)
            await orchestrator.shutdown()

        await asyncio.gather(orchestrator.run(), stop_after_tick())

        assert worker1.start_called
        assert worker2.start_called

    @pytest.mark.asyncio
    async def test_run_executa_ticks_periodicamente(self):
        """Run deve executar tick dos workers a cada intervalo."""
        orchestrator = PaperOrchestrator(interval_seconds=0.01)
        worker = MockWorker()
        orchestrator.register(worker)

        async def stop_after_ticks():
            await asyncio.sleep(0.05)  # ~5 ticks
            await orchestrator.shutdown()

        await asyncio.gather(orchestrator.run(), stop_after_ticks())

        assert worker.tick_count >= 3  # Pelo menos 3 ticks

    @pytest.mark.asyncio
    async def test_run_trata_erro_em_worker(self):
        """Run não deve parar se worker lança erro."""
        orchestrator = PaperOrchestrator(interval_seconds=0.01)
        failing = FailingWorker()
        orchestrator.register(failing)

        async def stop_after_ticks():
            await asyncio.sleep(0.05)
            await orchestrator.shutdown()

        await asyncio.gather(orchestrator.run(), stop_after_ticks())

        # Worker deve ter tentado tick mesmo com erro
        assert failing.tick_count >= 1  # Pelo menos 1 tick com erro

    @pytest.mark.asyncio
    async def test_shutdown_para_workers(self):
        """Shutdown deve chamar stop() de todos os workers."""
        orchestrator = PaperOrchestrator()
        worker1 = MockWorker(name="w1")
        worker2 = MockWorker(name="w2")
        orchestrator.register(worker1)
        orchestrator.register(worker2)

        # Inicia workers manualmente
        await orchestrator._start_all_workers()

        # Marca como running para permitir shutdown
        orchestrator._running = True
        await orchestrator.shutdown()

        assert worker1.stop_called
        assert worker2.stop_called
        assert not orchestrator.is_running

    @pytest.mark.asyncio
    async def test_on_tick_complete_callback_executado(self):
        """Callback on_tick_complete deve ser executado após cada ciclo."""
        callback_count = 0

        def on_complete():
            nonlocal callback_count
            callback_count += 1

        orchestrator = PaperOrchestrator(
            interval_seconds=0.01,
            on_tick_complete=on_complete,
        )
        worker = MockWorker()
        orchestrator.register(worker)

        async def stop_after_ticks():
            await asyncio.sleep(0.05)
            await orchestrator.shutdown()

        await asyncio.gather(orchestrator.run(), stop_after_ticks())

        assert callback_count >= 3

    @pytest.mark.asyncio
    async def test_run_sem_workers_nao_falha(self):
        """Run deve funcionar mesmo sem workers."""
        orchestrator = PaperOrchestrator(interval_seconds=0.01)

        async def stop_immediately():
            await asyncio.sleep(0.02)
            await orchestrator.shutdown()

        # Não deve lançar exceção
        await asyncio.gather(orchestrator.run(), stop_immediately())

        assert not orchestrator.is_running
