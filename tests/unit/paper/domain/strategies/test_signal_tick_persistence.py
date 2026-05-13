# -*- coding: utf-8 -*-
"""
Testes de integração: Signals + Ticks + OHLCV no StrategyWorker.

TDD RED: Testes de persistência via WriteQueue.
Spec: openspec/changes/sqlite-paper-persistence/specs/sqlite-write-queue/spec.md
"""

import asyncio
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.paper.adapters.persistence.sqlite_paper_state import SQLitePaperState
from src.core.paper.adapters.persistence.sqlite_write_queue import (
    SaveSignal,
    SaveTick,
    WriteQueue,
)
from src.core.paper.domain.strategies.signal import SinalEstrategia, TipoSinal
from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador
from src.core.paper.domain.strategies.position_tracker import PositionTracker


def _make_worker_with_queue(tmp_path, **kwargs):
    """Helper: cria StrategyWorker com WriteQueue conectado."""
    db_path = tmp_path / "test.db"
    state = SQLitePaperState(str(db_path))
    queue = WriteQueue(state, flush_interval=60.0, max_batch=999)

    strategy = kwargs.pop("strategy", GuardiaoConservador())
    datafeed = kwargs.pop("datafeed", AsyncMock())
    executor = kwargs.pop("executor", AsyncMock())
    tracker = kwargs.pop("tracker", PositionTracker())
    tickers = kwargs.pop("tickers", ["BTC-USD"])

    from src.core.paper.facade.sandbox.workers.strategy_worker import StrategyWorker
    worker = StrategyWorker(
        strategy=strategy,
        datafeed=datafeed,
        executor=executor,
        position_tracker=tracker,
        tickers=tickers,
        write_queue=queue,
        **kwargs,
    )
    return worker, state, queue


class TestSignalPersistence:
    """Task 6.1-6.2: Sinais COMPRA/VENDA persistidos."""

    @pytest.mark.asyncio
    async def test_sinal_compra_persistido(self, tmp_path):
        """Scenario: Sinal COMPRA persistido com strategy_name e broker."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="DI crossover",
            take_profit_pct=Decimal("0.004"),
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "guardiao-conservador"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("50000"), timestamp="2026-01-01T10:00:00"
        )
        datafeed.obter_historico.return_value = []

        worker, state, queue = _make_worker_with_queue(
            tmp_path, strategy=strategy, datafeed=datafeed,
        )
        await worker._do_tick()
        await queue.flush()

        cursor = state._conn.execute("SELECT * FROM signals")
        rows = [dict(r) for r in cursor.fetchall()]
        assert len(rows) == 1
        assert rows[0]["signal_type"] == "BUY"
        assert rows[0]["ticker"] == "BTC-USD"
        assert rows[0]["strategy_name"] == "guardiao-conservador"
        assert rows[0]["broker"] is not None
        await queue.close()

    @pytest.mark.asyncio
    async def test_sinal_venda_persistido(self, tmp_path):
        """Scenario: Sinal VENDA persistido quando posição fecha."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.VENDA,
            preco=Decimal("51000"), razao="SL hit",
        )
        strategy = MagicMock()
        strategy.evaluate.return_value = sinal
        strategy.name = "guardiao-conservador"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("51000"), timestamp="2026-01-01T10:00:00"
        )
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))

        worker, state, queue = _make_worker_with_queue(
            tmp_path, strategy=strategy, datafeed=datafeed,
            executor=executor, tracker=tracker,
        )
        await worker._do_tick()
        await queue.flush()

        cursor = state._conn.execute("SELECT * FROM signals")
        rows = [dict(r) for r in cursor.fetchall()]
        assert len(rows) == 1
        assert rows[0]["signal_type"] == "SELL"
        await queue.close()


class TestTickPersistence:
    """Task 6.3-6.4: Ticks raw persistidos."""

    @pytest.mark.asyncio
    async def test_tick_raw_persistido_por_tick(self, tmp_path):
        """Scenario: Tick persistido em ticks_raw com preço exato."""
        strategy = MagicMock()
        strategy.evaluate.return_value = None
        strategy.name = "guardiao"

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("50000.12"), timestamp="2026-01-01T10:00:00.500"
        )
        datafeed.obter_historico.return_value = []

        worker, state, queue = _make_worker_with_queue(
            tmp_path, strategy=strategy, datafeed=datafeed,
        )
        await worker._do_tick()
        await queue.flush()

        cursor = state._conn.execute("SELECT * FROM ticks_raw")
        rows = [dict(r) for r in cursor.fetchall()]
        assert len(rows) == 1
        assert rows[0]["price"] == "50000.12"
        assert rows[0]["symbol"] == "BTC-USD"
        await queue.close()


class TestOhlcvAggregation:
    """Task 6.5-6.6: OHLCV agregado em memória e persistido."""

    @pytest.mark.asyncio
    async def test_candle_1m_persistido(self, tmp_path):
        """Scenario: Após N ticks, candle OHLCV é persistido."""
        strategy = MagicMock()
        strategy.evaluate.return_value = None
        strategy.name = "guardiao"

        datafeed = AsyncMock()
        datafeed.obter_historico.return_value = []

        worker, state, queue = _make_worker_with_queue(
            tmp_path, strategy=strategy, datafeed=datafeed,
        )

        # Simula vários ticks no mesmo minuto
        prices = [Decimal("50000"), Decimal("50100"), Decimal("49900"), Decimal("50050")]
        for i, price in enumerate(prices):
            datafeed.obter_cotacao.return_value = MagicMock(
                preco=price, timestamp=f"2026-01-01T10:00:{i:02d}"
            )
            await worker._do_tick()

        # Força flush do candle
        worker.flush_ohlcv()
        await queue.flush()

        cursor = state._conn.execute("SELECT * FROM ohlcv")
        rows = [dict(r) for r in cursor.fetchall()]
        assert len(rows) >= 1
        candle = rows[0]
        assert candle["open"] == "50000"
        assert candle["high"] == "50100"
        assert candle["low"] == "49900"
        assert candle["close"] == "50050"
        assert candle["interval"] == "1m"
        await queue.close()
