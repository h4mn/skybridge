# -*- coding: utf-8 -*-
"""
Testes da WriteQueue (Single Writer).

TDD RED: Estes testes DEVEM falhar enquanto sqlite_write_queue.py não existir.

Spec: openspec/changes/sqlite-paper-persistence/specs/sqlite-write-queue/spec.md
"""

import asyncio
from decimal import Decimal
from pathlib import Path

import pytest

from src.core.paper.adapters.persistence.sqlite_paper_state import SQLitePaperState
from src.core.paper.adapters.persistence.sqlite_write_queue import (
    SaveOrder,
    SavePnl,
    SaveSignal,
    SaveTick,
    SaveOhlcv,
    UpdatePosition,
    WriteQueue,
)


@pytest.fixture
def state(tmp_path):
    db_path = tmp_path / "test.db"
    return SQLitePaperState(str(db_path))


@pytest.fixture
def queue(state):
    q = WriteQueue(state, flush_interval=0.1, max_batch=50)
    return q


# ── Requirement: Tipos de operação ──


class TestOperationTypes:
    def test_save_order_tipo(self):
        op = SaveOrder({"id": "ord-1", "ticker": "BTC-USD"})
        assert op.table == "orders"

    def test_update_position_tipo(self):
        op = UpdatePosition(ticker="BTC-USD", strategy_name="guardiao", data={})
        assert op.table == "positions"

    def test_save_pnl_tipo(self):
        op = SavePnl({"ticker": "BTC-USD", "pnl_value": "500"})
        assert op.table == "closed_pnl"

    def test_save_signal_tipo(self):
        op = SaveSignal({"ticker": "BTC-USD", "signal_type": "BUY"})
        assert op.table == "signals"

    def test_save_tick_tipo(self):
        op = SaveTick({"symbol": "BTC-USD", "price": "50000"})
        assert op.table == "ticks_raw"

    def test_save_ohlcv_tipo(self):
        op = SaveOhlcv({"symbol": "BTC-USD", "interval": "1m"})
        assert op.table == "ohlcv"


# ── Requirement: Batch flush em transação única ──


class TestBatchFlush:
    @pytest.mark.asyncio
    async def test_10_operacoes_em_1_transacao(self, state, queue):
        """Scenario: Flush drena múltiplas operações em batch."""
        for i in range(3):
            await queue.enqueue(SaveTick({
                "time": f"2026-01-01T10:00:0{i}", "symbol": "BTC-USD",
                "broker": "paper", "price": str(50000 + i), "volume": 100,
            }))
        for i in range(2):
            await queue.enqueue(SaveOrder({
                "created_at": f"2026-01-01T10:00:0{i}", "id": f"ord-{i}",
                "ticker": "BTC-USD", "side": "buy", "quantity": 1,
                "price": "50000", "total_value": "50000", "status": "EXECUTADA",
                "order_type": "open", "broker": "paper", "strategy_name": "guardiao",
            }))
        for i in range(5):
            await queue.enqueue(SavePnl({
                "closed_at": f"2026-01-01T10:{i}:00", "ticker": "BTC-USD",
                "strategy_name": "guardiao", "broker": "paper",
                "entry_price": "50000", "exit_price": "50500",
                "quantity": 1, "side": "long", "pnl_value": str(500 + i),
                "pnl_value_display": float(500 + i), "pnl_pct": 1.0, "reason": "tp",
            }))

        await queue.flush()

        ticks = state._conn.execute("SELECT COUNT(*) FROM ticks_raw").fetchone()[0]
        orders = state._conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        pnl = state._conn.execute("SELECT COUNT(*) FROM closed_pnl").fetchone()[0]
        assert ticks == 3
        assert orders == 2
        assert pnl == 5


# ── Requirement: Flush por batch size ──


class TestFlushTrigger:
    @pytest.mark.asyncio
    async def test_flush_por_batch_size(self, state):
        """Scenario: Flush quando max_batch atingido."""
        q = WriteQueue(state, flush_interval=10.0, max_batch=5)

        for i in range(5):
            await q.enqueue(SaveTick({
                "time": f"2026-01-01T10:00:0{i}", "symbol": "BTC-USD",
                "broker": "paper", "price": str(50000 + i), "volume": 100,
            }))

        # max_batch atingido, flush automático
        await asyncio.sleep(0.1)

        count = state._conn.execute("SELECT COUNT(*) FROM ticks_raw").fetchone()[0]
        assert count == 5
        await q.close()


# ── Requirement: Concurrent enqueue ──


class TestConcurrentEnqueue:
    @pytest.mark.asyncio
    async def test_3_workers_enfileiram_simultaneamente(self, state, queue):
        """Scenario: Workers enfileiram em paralelo sem erro."""
        async def worker(name, count):
            for i in range(count):
                await queue.enqueue(SaveTick({
                    "time": f"2026-01-01T10:00:0{i}", "symbol": name,
                    "broker": "paper", "price": "50000", "volume": 100,
                }))

        await asyncio.gather(
            worker("BTC-USD", 5),
            worker("ETH-USD", 5),
            worker("SOL-USD", 5),
        )
        await queue.flush()

        count = state._conn.execute("SELECT COUNT(DISTINCT symbol) FROM ticks_raw").fetchone()[0]
        assert count == 3
        total = state._conn.execute("SELECT COUNT(*) FROM ticks_raw").fetchone()[0]
        assert total == 15


# ── Requirement: Close drena fila ──


class TestClose:
    @pytest.mark.asyncio
    async def test_close_drena_fila(self, state, queue):
        """Scenario: close() faz flush final."""
        for i in range(5):
            await queue.enqueue(SaveTick({
                "time": f"2026-01-01T10:00:0{i}", "symbol": "BTC-USD",
                "broker": "paper", "price": "50000", "volume": 100,
            }))

        await queue.close()

        count = state._conn.execute("SELECT COUNT(*) FROM ticks_raw").fetchone()[0]
        assert count == 5


# ── Requirement: Crash consistency ──


class TestCrashConsistency:
    @pytest.mark.asyncio
    async def test_dados_do_ultimo_flush_intactos(self, state, queue):
        """Scenario: Dados commitados estão intactos."""
        await queue.enqueue(SaveTick({
            "time": "2026-01-01T10:00:00", "symbol": "BTC-USD",
            "broker": "paper", "price": "50000", "volume": 100,
        }))
        await queue.flush()

        # "crash" — sem close graceful
        count = state._conn.execute("SELECT COUNT(*) FROM ticks_raw").fetchone()[0]
        assert count == 1


# ── Requirement: Flush por tempo ──


class TestFlushPorTempo:
    @pytest.mark.asyncio
    async def test_flush_apos_intervalo(self, state):
        """Scenario: Flush automático após flush_interval."""
        q = WriteQueue(state, flush_interval=0.1, max_batch=999)
        await q.start()

        await q.enqueue(SaveTick({
            "time": "2026-01-01T10:00:00", "symbol": "BTC-USD",
            "broker": "paper", "price": "50000", "volume": 100,
        }))

        # Espera flush_interval + margem
        await asyncio.sleep(0.3)

        count = state._conn.execute("SELECT COUNT(*) FROM ticks_raw").fetchone()[0]
        assert count == 1
        await q.close()


# ── Requirement: Flush agressivo para ticks ──


class TestFlushAgressivoTicks:
    @pytest.mark.asyncio
    async def test_flush_agressivo_com_muitos_ticks(self, state):
        """Scenario: Flush quando depth > 20 e contém SaveTick."""
        q = WriteQueue(state, flush_interval=60.0, max_batch=999)

        for i in range(21):
            await q.enqueue(SaveTick({
                "time": f"2026-01-01T10:00:{i:02d}", "symbol": "BTC-USD",
                "broker": "paper", "price": str(50000 + i), "volume": 100,
            }))

        count = state._conn.execute("SELECT COUNT(*) FROM ticks_raw").fetchone()[0]
        assert count == 21
        await q.close()


# ── Requirement: Tracker/Signal enqueue ──


class TestSpecificEnqueue:
    @pytest.mark.asyncio
    async def test_tracker_enfileira_posicao(self, state, queue):
        """Scenario: PositionTracker atualiza via UpdatePosition."""
        await queue.enqueue(UpdatePosition(
            ticker="BTC-USD", strategy_name="guardiao",
            data={"side": "long", "quantity": 1, "avg_price": "50000",
                  "status": "open", "opened_at": "2026-01-01T00:00:00",
                  "broker": "paper"},
        ))
        await queue.flush()

        pos = state.get_position("BTC-USD", "guardiao")
        assert pos is not None
        assert pos["quantity"] == 1

    @pytest.mark.asyncio
    async def test_worker_enfileira_sinal(self, state, queue):
        """Scenario: StrategyWorker enfileira SaveSignal."""
        await queue.enqueue(SaveSignal({
            "created_at": "2026-01-01T10:00:00", "ticker": "BTC-USD",
            "strategy_name": "guardiao", "broker": "paper",
            "signal_type": "BUY", "price": "50000", "reason": "RSI oversold",
            "take_profit_pct": "0.004",
        }))
        await queue.flush()

        cursor = state._conn.execute("SELECT * FROM signals")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["signal_type"] == "BUY"

    @pytest.mark.asyncio
    async def test_ohlcv_enfileirado(self, state, queue):
        """Scenario: OHLCV candle enfileirado e persistido."""
        await queue.enqueue(SaveOhlcv({
            "time": "2026-01-01T10:00:00", "symbol": "BTC-USD",
            "broker": "paper", "open": "50000", "high": "50100",
            "low": "49900", "close": "50050", "volume": 1000, "interval": "1m",
        }))
        await queue.flush()

        cursor = state._conn.execute("SELECT * FROM ohlcv")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["interval"] == "1m"

    @pytest.mark.asyncio
    async def test_batch_atomico_rollback_em_erro(self, state, queue):
        """Scenario: Batch atômico — erro faz rollback de tudo."""
        await queue.enqueue(SaveTick({
            "time": "2026-01-01T10:00:00", "symbol": "BTC-USD",
            "broker": "paper", "price": "50000", "volume": 100,
        }))
        # Ordem sem campo obrigatório vai falhar
        await queue.enqueue(SaveOrder({"id": "bad-order"}))

        await queue.flush()

        # Tick não deve ter sido persistido (rollback do batch)
        count = state._conn.execute("SELECT COUNT(*) FROM ticks_raw").fetchone()[0]
        assert count == 0


# ── Requirement: Broker enfileira ordens via WriteQueue ──


class TestBrokerEnqueue:
    """Scenario: Broker executa ordem e enfileira SaveOrder."""

    @pytest.mark.asyncio
    async def test_broker_enqueue_save_order(self, state, queue):
        """Scenario: Broker chama enqueue(SaveOrder) após execução."""
        await queue.enqueue(SaveOrder({
            "created_at": "2026-01-01T10:00:00", "id": "ord-broker-1",
            "ticker": "BTC-USD", "side": "buy", "quantity": 100,
            "price": "50000", "total_value": "5000000", "status": "EXECUTADA",
            "order_type": "open", "broker": "binance",
            "strategy_name": "guardiao-conservador",
        }))
        await queue.flush()

        orders = state.list_orders("BTC-USD", status="EXECUTADA")
        assert len(orders) == 1
        assert orders[0]["broker"] == "binance"
        assert orders[0]["order_type"] == "open"

    @pytest.mark.asyncio
    async def test_broker_enqueue_com_position_id(self, state, queue):
        """Scenario: Ordem de broker vinculada à posição via FK."""
        # Abre posição
        state.update_position("BTC-USD", "guardiao", {
            "side": "long", "quantity": 1, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })
        pos_id = state.get_position("BTC-USD", "guardiao")["id"]

        await queue.enqueue(SaveOrder({
            "created_at": "2026-01-01T10:00:00", "id": "ord-broker-2",
            "ticker": "BTC-USD", "side": "buy", "quantity": 100,
            "price": "50000", "total_value": "5000000", "status": "EXECUTADA",
            "order_type": "open", "position_id": pos_id,
            "broker": "binance", "strategy_name": "guardiao",
        }))
        await queue.flush()

        orders = state.list_orders("BTC-USD")
        assert orders[0]["position_id"] == pos_id

    @pytest.mark.asyncio
    async def test_broker_enqueue_increase_e_full_close(self, state, queue):
        """Scenario: Broker enqueue sequência open → increase → full_close."""
        state.update_position("BTC-USD", "guardiao", {
            "side": "long", "quantity": 1, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })
        pos_id = state.get_position("BTC-USD", "guardiao")["id"]

        types = ["open", "increase", "full_close"]
        for i, otype in enumerate(types):
            await queue.enqueue(SaveOrder({
                "created_at": f"2026-01-0{i+1}T10:00:00",
                "id": f"ord-seq-{i}",
                "ticker": "BTC-USD",
                "side": "buy" if otype != "full_close" else "sell",
                "quantity": 100,
                "price": "50000", "total_value": "5000000",
                "status": "EXECUTADA", "order_type": otype,
                "position_id": pos_id,
                "broker": "binance", "strategy_name": "guardiao",
            }))
        await queue.flush()

        orders = state.list_orders("BTC-USD")
        assert len(orders) == 3
        order_types = [o["order_type"] for o in orders]
        assert order_types == types

    @pytest.mark.asyncio
    async def test_broker_e_tracker_enfileiram_juntos(self, state, queue):
        """Scenario: Broker enqueue ordem + tracker enqueue posição no mesmo batch."""
        # Broker: ordem de compra
        await queue.enqueue(SaveOrder({
            "created_at": "2026-01-01T10:00:00", "id": "ord-bt",
            "ticker": "BTC-USD", "side": "buy", "quantity": 100,
            "price": "50000", "total_value": "5000000", "status": "EXECUTADA",
            "order_type": "open", "broker": "binance",
            "strategy_name": "guardiao",
        }))
        # Tracker: posição aberta
        await queue.enqueue(UpdatePosition(
            ticker="BTC-USD", strategy_name="guardiao",
            data={"side": "long", "quantity": 100, "avg_price": "50000",
                  "status": "open", "opened_at": "2026-01-01T10:00:00",
                  "broker": "binance"},
        ))
        await queue.flush()

        assert len(state.list_orders("BTC-USD")) == 1
        assert state.get_position("BTC-USD", "guardiao") is not None
