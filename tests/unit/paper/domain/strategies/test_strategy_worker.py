# -*- coding: utf-8 -*-
"""Testes para StrategyWorker refatorado — injeção de dependências reais."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.paper.domain.strategies.signal import DadosMercado, SinalEstrategia, TipoSinal
from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador
from src.core.paper.domain.strategies.position_tracker import PositionTracker


def _make_worker(**kwargs):
    """Helper: cria StrategyWorker com dependências mockadas."""
    strategy = kwargs.pop("strategy", GuardiaoConservador())
    datafeed = kwargs.pop("datafeed", AsyncMock())
    executor = kwargs.pop("executor", AsyncMock())
    tracker = kwargs.pop("tracker", PositionTracker())
    tickers = kwargs.pop("tickers", ["BTC-USD"])

    from src.core.paper.facade.sandbox.workers.strategy_worker import StrategyWorker
    return StrategyWorker(
        strategy=strategy,
        datafeed=datafeed,
        executor=executor,
        position_tracker=tracker,
        tickers=tickers,
        **kwargs,
    )


class TestStrategyWorkerTick:
    """DOC: specs/strategy-worker — Ciclo de tick com dependências reais."""

    @pytest.mark.asyncio
    async def test_tick_com_sinal_compra(self):
        """WHEN estratégia retorna COMPRA THEN executor.executar_ordem é chamado."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="teste",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()
        call_kwargs = executor.executar_ordem.call_args
        assert call_kwargs.kwargs.get("ticker") == "BTC-USD" or call_kwargs[1].get("ticker") == "BTC-USD"

    @pytest.mark.asyncio
    async def test_tick_com_sinal_venda(self):
        """WHEN estratégia retorna VENDA THEN executor.executar_ordem é chamado com VENDA."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.VENDA,
            preco=Decimal("50000"), razao="teste",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()

    @pytest.mark.asyncio
    async def test_tick_sem_sinal(self):
        """WHEN estratégia retorna None THEN executor NÃO é chamado."""
        strategy = MagicMock()
        strategy.evaluate.return_value = None
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("50000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_not_called()

    @pytest.mark.asyncio
    async def test_tick_erro_datafeed_nao_crasha(self):
        """WHEN datafeed lança exceção THEN worker não crasha (BaseWorker captura)."""
        strategy = MagicMock()
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.side_effect = Exception("Yahoo Finance timeout")

        executor = AsyncMock()
        tracker = PositionTracker()

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()  # não deve levantar

        executor.executar_ordem.assert_not_called()


class TestStrategyWorkerSLTP:
    """DOC: specs/strategy-worker — Verificação de SL/TP durante tick."""

    @pytest.mark.asyncio
    async def test_stop_loss_during_tick(self):
        """WHEN position_tracker.check_price retorna sinal SL THEN executa venda."""
        strategy = MagicMock()
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("47000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker(stop_loss_pct=Decimal("0.05"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()

    @pytest.mark.asyncio
    async def test_take_profit_during_tick(self):
        """WHEN position_tracker.check_price retorna sinal TP THEN executa venda."""
        strategy = MagicMock()
        strategy.name = "test"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(preco=Decimal("56000"))
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker(take_profit_pct=Decimal("0.10"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        worker = _make_worker(strategy=strategy, datafeed=datafeed, executor=executor, tracker=tracker)
        await worker._do_tick()

        executor.executar_ordem.assert_called_once()


class TestStrategyWorkerBackwardCompat:
    """DOC: specs/strategy-worker — Backward-compatibilidade com construtor antigo."""

    @pytest.mark.asyncio
    async def test_construtor_antigo_funciona(self):
        """WHEN criar com strategy_name e on_suggestion THEN funciona como stub."""
        from src.core.paper.facade.sandbox.workers.strategy_worker import StrategyWorker

        callback = MagicMock()
        worker = StrategyWorker(strategy_name="legacy", on_suggestion=callback)

        assert worker.name == "strategy_legacy"
        assert worker.strategy_name == "legacy"

        await worker._do_tick()  # stub behavior — não deve crashar
