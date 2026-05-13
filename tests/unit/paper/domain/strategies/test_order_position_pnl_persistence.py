# -*- coding: utf-8 -*-
"""
Testes: ordens, posições e PnL persistidos via WriteQueue no SQLite.

TDD RED→GREEN: prova que dados vão pro SQLite e nenhum .json é criado.
Spec: openspec/changes/sqlite-paper-persistence/specs/sqlite-write-queue/spec.md
"""

import asyncio
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.paper.adapters.persistence.sqlite_paper_state import SQLitePaperState
from src.core.paper.adapters.persistence.sqlite_write_queue import (
    WriteQueue,
    SaveOrder,
    SavePnl,
    SaveStrategyPosition,
    CloseStrategyPosition,
)
from src.core.paper.domain.strategies.signal import SinalEstrategia, TipoSinal
from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador
from src.core.paper.domain.strategies.position_tracker import PositionTracker


def _mock_strategy(name="guardiao-conservador"):
    """Helper: cria MagicMock de strategy que simula GuardiaoConservador."""
    real = GuardiaoConservador()
    strategy = MagicMock()
    strategy.name = name
    strategy._last_indicators = real._last_indicators
    strategy._tp_for_adx = real._tp_for_adx
    return strategy


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


class TestOrderPersistence:
    """Ordens são persistidas na tabela orders."""

    @pytest.mark.asyncio
    async def test_ordem_compra_persistida(self, tmp_path):
        """WHEN COMPRA executada THEN ordem aparece na tabela orders."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="DI crossover",
        )
        strategy = _mock_strategy()
        strategy.evaluate.return_value = sinal

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

        cursor = state._conn.execute("SELECT * FROM orders")
        rows = [dict(r) for r in cursor.fetchall()]
        assert len(rows) == 1
        assert rows[0]["side"] == "BUY"
        assert rows[0]["ticker"] == "BTC-USD"
        assert rows[0]["price"] == "50000"
        assert rows[0]["status"] == "EXECUTADA"
        assert rows[0]["strategy_name"] == "guardiao-conservador"
        await queue.close()

    @pytest.mark.asyncio
    async def test_ordem_venda_persistida(self, tmp_path):
        """WHEN VENDA executada THEN ordem SELL aparece na tabela orders."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.VENDA,
            preco=Decimal("52000"), razao="TP hit",
        )
        strategy = _mock_strategy()
        strategy.evaluate.return_value = sinal

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("52000"), timestamp="2026-01-01T10:00:00"
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

        cursor = state._conn.execute("SELECT * FROM orders")
        rows = [dict(r) for r in cursor.fetchall()]
        assert len(rows) == 1
        assert rows[0]["side"] == "SELL"
        await queue.close()

    @pytest.mark.asyncio
    async def test_ordem_sl_persistida(self, tmp_path):
        """WHEN SL acionado THEN ordem SELL é persistida."""
        strategy = _mock_strategy()
        strategy.evaluate.return_value = None

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("47000"), timestamp="2026-01-01T10:00:00"
        )
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker(stop_loss_pct=Decimal("0.05"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        worker, state, queue = _make_worker_with_queue(
            tmp_path, strategy=strategy, datafeed=datafeed,
            executor=executor, tracker=tracker,
        )
        await worker._do_tick()
        await queue.flush()

        cursor = state._conn.execute("SELECT * FROM orders")
        rows = [dict(r) for r in cursor.fetchall()]
        assert len(rows) == 1
        assert rows[0]["side"] == "SELL"
        await queue.close()


class TestStrategyPositionPersistence:
    """Posições do PositionTracker persistidas na tabela strategy_positions."""

    @pytest.mark.asyncio
    async def test_posicao_aberta_persistida(self, tmp_path):
        """WHEN COMPRA executada THEN posição aparece em strategy_positions."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="DI crossover",
            take_profit_pct=Decimal("0.004"),
        )
        strategy = _mock_strategy()
        strategy.evaluate.return_value = sinal

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

        pos = state.get_strategy_position("BTC-USD", "guardiao-conservador")
        assert pos is not None
        assert pos["entry_price"] == "50000"
        assert pos["status"] == "open"
        assert pos["take_profit_pct"] == "0.004"
        await queue.close()

    @pytest.mark.asyncio
    async def test_posicao_fechada_via_sl(self, tmp_path):
        """WHEN SL acionado THEN posição marcada como closed no SQLite."""
        sinal_compra = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="DI crossover",
        )
        strategy = _mock_strategy()
        call_n = [0]
        def _evaluate(*a):
            call_n[0] += 1
            return sinal_compra if call_n[0] == 1 else None
        strategy.evaluate.side_effect = _evaluate

        datafeed = AsyncMock()
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker(stop_loss_pct=Decimal("0.05"))

        worker, state, queue = _make_worker_with_queue(
            tmp_path, strategy=strategy, datafeed=datafeed,
            executor=executor, tracker=tracker,
        )

        # Tick 1: COMPRA
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("50000"), timestamp="2026-01-01T10:00:00"
        )
        await worker._do_tick()
        await queue.flush()

        # Verifica posição aberta no SQLite
        pos = state.get_strategy_position("BTC-USD", "guardiao-conservador")
        assert pos is not None
        assert pos["status"] == "open"

        # Tick 2: SL — preço cai abaixo do stop loss
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("47000"), timestamp="2026-01-01T10:01:00"
        )
        await worker._do_tick()
        await queue.flush()

        # get_strategy_position filtra por status='open'
        pos = state.get_strategy_position("BTC-USD", "guardiao-conservador")
        assert pos is None  # posição fechada, não deve aparecer

        # Mas deve existir com status='closed'
        cursor = state._conn.execute(
            "SELECT * FROM strategy_positions WHERE ticker='BTC-USD' AND status='closed'"
        )
        rows = [dict(r) for r in cursor.fetchall()]
        assert len(rows) == 1
        assert rows[0]["closed_at"] is not None
        await queue.close()

    @pytest.mark.asyncio
    async def test_posicao_fechada_via_sinal_venda(self, tmp_path):
        """WHEN VENDA por sinal THEN posição marcada como closed."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.VENDA,
            preco=Decimal("52000"), razao="TP hit",
        )
        strategy = _mock_strategy()
        strategy.evaluate.return_value = sinal

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("52000"), timestamp="2026-01-01T10:00:00"
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

        pos = state.get_strategy_position("BTC-USD", "guardiao-conservador")
        assert pos is None  # fechada
        await queue.close()


class TestPnlPersistence:
    """PnL fechado persistido na tabela closed_pnl."""

    @pytest.mark.asyncio
    async def test_pnl_fechado_via_sl_persistido(self, tmp_path):
        """WHEN SL acionado THEN PnL negativo persistido."""
        sinal_compra = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="DI crossover",
        )
        strategy = _mock_strategy()
        call_n = [0]
        def _evaluate(*a):
            call_n[0] += 1
            return sinal_compra if call_n[0] == 1 else None
        strategy.evaluate.side_effect = _evaluate

        datafeed = AsyncMock()
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker(stop_loss_pct=Decimal("0.05"))

        worker, state, queue = _make_worker_with_queue(
            tmp_path, strategy=strategy, datafeed=datafeed,
            executor=executor, tracker=tracker,
        )

        # Tick 1: COMPRA
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("50000"), timestamp="2026-01-01T10:00:00"
        )
        await worker._do_tick()
        await queue.flush()

        # Tick 2: SL
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("47000"), timestamp="2026-01-01T10:01:00"
        )
        await worker._do_tick()
        await queue.flush()

        pnl_rows = state.get_all_closed_pnl()
        assert len(pnl_rows) == 1
        assert pnl_rows[0]["ticker"] == "BTC-USD"
        assert pnl_rows[0]["pnl_pct"] < 0
        assert "Stop Loss" in pnl_rows[0]["reason"]
        await queue.close()

    @pytest.mark.asyncio
    async def test_pnl_fechado_via_venda_persistido(self, tmp_path):
        """WHEN VENDA por sinal THEN PnL persistido."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.VENDA,
            preco=Decimal("52000"), razao="Take Profit",
        )
        strategy = _mock_strategy()
        strategy.evaluate.return_value = sinal

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("52000"), timestamp="2026-01-01T10:00:00"
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

        pnl_rows = state.get_all_closed_pnl()
        assert len(pnl_rows) == 1
        assert pnl_rows[0]["entry_price"] == "50000"
        assert pnl_rows[0]["exit_price"] == "52000"
        assert pnl_rows[0]["pnl_pct"] > 0
        await queue.close()


class TestRestorationFromSQLite:
    """Restauração de estado a partir do SQLite."""

    @pytest.mark.asyncio
    async def test_restaurar_posicoes_do_sqlite(self, tmp_path):
        """WHEN SQLite tem posições abertas THEN PositionTracker restaura."""
        db_path = tmp_path / "test.db"
        state = SQLitePaperState(str(db_path))

        # Simula posição aberta no banco
        state._upsert_strategy_position("BTC-USD", "guardiao-conservador", {
            "entry_price": "50000",
            "take_profit_pct": "0.004",
            "stop_loss_pct": "0.002",
            "status": "open",
        })
        state._conn.commit()

        # Restaura via list_open_strategy_positions
        saved = state.list_open_strategy_positions("guardiao-conservador")
        assert len(saved) == 1

        tracker = PositionTracker()
        for pos in saved:
            tracker.restore_positions([{
                "ticker": pos["ticker"],
                "preco_entrada": Decimal(pos["entry_price"]),
                "take_profit_pct": Decimal(pos["take_profit_pct"]) if pos.get("take_profit_pct") else None,
            }])

        restored = tracker.get_position("BTC-USD")
        assert restored is not None
        assert restored["preco_entrada"] == Decimal("50000")
        assert restored["take_profit_pct"] == Decimal("0.004")
        state.close()

    @pytest.mark.asyncio
    async def test_restaurar_closed_pnl_do_sqlite(self, tmp_path):
        """WHEN SQLite tem PnL fechado THEN closed_pnl restaura."""
        db_path = tmp_path / "test.db"
        state = SQLitePaperState(str(db_path))

        # Simula PnL no banco
        state._insert_pnl({
            "closed_at": "2026-01-01T10:00:00",
            "ticker": "BTC-USD",
            "strategy_name": "guardiao-conservador",
            "broker": "paper",
            "entry_price": "50000",
            "exit_price": "52000",
            "quantity": 100,
            "side": "long",
            "pnl_value": "200000",
            "pnl_value_display": 200000.0,
            "pnl_pct": 4.0,
            "reason": "Take Profit",
        })
        state._conn.commit()

        pnl_rows = state.get_all_closed_pnl()
        closed_pnl = [float(r["pnl_value_display"]) for r in pnl_rows]

        assert len(closed_pnl) == 1
        assert closed_pnl[0] == 200000.0
        state.close()


class TestNoJsonCreated:
    """Garante que nenhum arquivo .json é criado durante o runtime."""

    @pytest.mark.asyncio
    async def test_nenhum_json_criado_no_runtime(self, tmp_path):
        """WHEN worker roda com SQLite THEN nenhum arquivo .json é criado."""
        sinal = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="teste",
        )
        strategy = _mock_strategy("guardiao")
        strategy.evaluate.return_value = sinal

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

        # Verifica que nenhum .json existe em tmp_path
        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 0, f"JSON files found: {json_files}"

        # Verifica que o SQLite existe e tem dados
        db_files = list(tmp_path.glob("*.db"))
        assert len(db_files) == 1

        cursor = state._conn.execute("SELECT * FROM orders")
        assert len(cursor.fetchall()) == 1

        cursor = state._conn.execute("SELECT * FROM strategy_positions")
        assert len(cursor.fetchall()) == 1
        await queue.close()

    @pytest.mark.asyncio
    async def test_ciclo_completo_sem_json(self, tmp_path):
        """WHEN ciclo completo COMPRA→VENDA THEN tudo em SQLite, nenhum JSON."""
        strategy = _mock_strategy("guardiao")
        call_n = [0]

        sinal_compra = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"), razao="DI crossover",
        )
        sinal_venda = SinalEstrategia(
            ticker="BTC-USD", tipo=TipoSinal.VENDA,
            preco=Decimal("52000"), razao="TP hit",
        )

        def _evaluate(*a):
            call_n[0] += 1
            return sinal_compra if call_n[0] == 1 else sinal_venda

        strategy.evaluate.side_effect = _evaluate

        datafeed = AsyncMock()
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("50000"), timestamp="2026-01-01T10:00:00"
        )
        datafeed.obter_historico.return_value = []

        executor = AsyncMock()
        tracker = PositionTracker()

        worker, state, queue = _make_worker_with_queue(
            tmp_path, strategy=strategy, datafeed=datafeed,
            executor=executor, tracker=tracker,
        )

        # Tick 1: COMPRA
        await worker._do_tick()
        await queue.flush()

        # Tick 2: VENDA
        datafeed.obter_cotacao.return_value = MagicMock(
            preco=Decimal("52000"), timestamp="2026-01-01T10:01:00"
        )
        await worker._do_tick()
        await queue.flush()

        # Verificações
        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 0

        cursor = state._conn.execute("SELECT * FROM orders")
        orders = cursor.fetchall()
        assert len(orders) == 2  # 1 BUY + 1 SELL

        cursor = state._conn.execute("SELECT * FROM closed_pnl")
        pnl_rows = cursor.fetchall()
        assert len(pnl_rows) == 1

        cursor = state._conn.execute(
            "SELECT * FROM strategy_positions WHERE status='open'"
        )
        assert len(cursor.fetchall()) == 0  # posição fechada
        await queue.close()
