# -*- coding: utf-8 -*-
"""
Testes do SQLitePaperState (CQS — Commands e Queries separados).

TDD RED: Estes testes DEVEM falhar enquanto SQLitePaperState não existir.

Spec: openspec/changes/sqlite-paper-persistence/specs/sqlite-paper-state/spec.md
"""

import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest

from src.core.paper.adapters.persistence.sqlite_paper_state import SQLitePaperState
from src.core.paper.ports.paper_state_port import PaperStateData


@pytest.fixture
def state(tmp_path):
    """Cria SQLitePaperState em diretório temporário."""
    db_path = tmp_path / "test_paper_state.db"
    return SQLitePaperState(str(db_path))


# ── Requirement: Instanciação cria database com WAL ──


class TestInit:
    def test_database_criado_com_wal(self, tmp_path):
        """Scenario: Database novo criado com todas as tabelas e WAL ativo."""
        db_path = tmp_path / "new.db"
        SQLitePaperState(str(db_path))

        conn = sqlite3.connect(str(db_path))
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
        conn.close()

    def test_tabelas_criadas(self, state, tmp_path):
        """Scenario: Todas as tabelas existem após init."""
        conn = sqlite3.connect(str(tmp_path / "test_paper_state.db"))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected = {
            "state_meta", "cashbook_entries", "positions", "orders",
            "strategy_positions", "closed_pnl", "signals", "ticks_raw",
            "ohlcv", "portfolios", "schema_version",
        }
        assert expected.issubset(tables)

    def test_queries_em_db_vazio_retornam_defaults(self, state):
        """Scenario: Queries em database novo retornam defaults."""
        assert state.get_position("BTC-USD", "guardiao") is None
        assert state.list_orders("BTC-USD") == []
        assert state.get_cashbook() == {}
        assert state.get_closed_pnl("BTC-USD") == []


# ── Requirement: CQS — Queries granulares ──


class TestQueries:
    def test_get_position_por_ticker_e_estrategia(self, state):
        """Scenario: get_position retorna dict ou None."""
        state.update_position("BTC-USD", "guardiao", {
            "side": "long", "quantity": 1, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })
        result = state.get_position("BTC-USD", "guardiao")
        assert result is not None
        assert result["ticker"] == "BTC-USD"
        assert result["strategy_name"] == "guardiao"
        assert result["side"] == "long"
        assert result["quantity"] == 1

    def test_get_position_nao_existente(self, state):
        """Scenario: Ticker/estratégia que não existe retorna None."""
        assert state.get_position("ETH-USD", "guardiao") is None

    def test_list_orders_com_filtros(self, state):
        """Scenario: list_orders filtra por ticker e status."""
        state.save_order({
            "created_at": "2026-01-01T00:00:00", "id": "ord-1",
            "ticker": "BTC-USD", "side": "buy", "quantity": 1,
            "price": "50000", "total_value": "50000", "status": "EXECUTADA",
            "order_type": "open", "broker": "binance", "strategy_name": "guardiao",
        })
        state.save_order({
            "created_at": "2026-01-02T00:00:00", "id": "ord-2",
            "ticker": "BTC-USD", "side": "buy", "quantity": 2,
            "price": "51000", "total_value": "102000", "status": "PENDING",
            "order_type": "open", "broker": "binance", "strategy_name": "guardiao",
        })

        all_orders = state.list_orders("BTC-USD")
        assert len(all_orders) == 2

        executed = state.list_orders("BTC-USD", status="EXECUTADA")
        assert len(executed) == 1
        assert executed[0]["id"] == "ord-1"

    def test_get_cashbook(self, state):
        """Scenario: get_cashbook retorna dict de currencies."""
        state._conn.execute(
            "INSERT INTO cashbook_entries (currency, amount, conversion_rate) "
            "VALUES (?, ?, ?)", ("BRL", "100000", "1")
        )
        state._conn.execute(
            "INSERT INTO cashbook_entries (currency, amount, conversion_rate) "
            "VALUES (?, ?, ?)", ("USD", "2500", "5.20")
        )
        state._conn.commit()

        cashbook = state.get_cashbook()
        assert cashbook["BRL"]["amount"] == "100000"
        assert cashbook["USD"]["amount"] == "2500"

    def test_get_closed_pnl_por_ticker(self, state):
        """Scenario: get_closed_pnl filtra por ticker."""
        state.save_pnl({
            "closed_at": "2026-01-01T10:00:00", "ticker": "BTC-USD",
            "strategy_name": "guardiao", "broker": "binance",
            "entry_price": "50000", "exit_price": "50500",
            "quantity": 1, "side": "long", "pnl_value": "500",
            "pnl_value_display": 500.0, "pnl_pct": 1.0, "reason": "tp_hit",
        })
        state.save_pnl({
            "closed_at": "2026-01-01T11:00:00", "ticker": "ETH-USD",
            "strategy_name": "guardiao", "broker": "binance",
            "entry_price": "3000", "exit_price": "3100",
            "quantity": 1, "side": "long", "pnl_value": "100",
            "pnl_value_display": 100.0, "pnl_pct": 3.33, "reason": "tp_hit",
        })

        pnl_btc = state.get_closed_pnl("BTC-USD")
        assert len(pnl_btc) == 1
        assert pnl_btc[0]["pnl_value"] == "500"


# ── Requirement: CQS — Commands granulares ──


class TestCommands:
    def test_save_order_grava_soh_tabela_orders(self, state, tmp_path):
        """Scenario: save_order não toca positions."""
        state.save_order({
            "created_at": "2026-01-01T00:00:00", "id": "ord-1",
            "ticker": "BTC-USD", "side": "buy", "quantity": 1,
            "price": "50000", "total_value": "50000", "status": "EXECUTADA",
            "order_type": "open", "broker": "binance", "strategy_name": "guardiao",
        })

        # orders tem 1 row
        cursor = state._conn.execute("SELECT COUNT(*) FROM orders")
        assert cursor.fetchone()[0] == 1

        # positions não foi tocada
        cursor = state._conn.execute("SELECT COUNT(*) FROM positions")
        assert cursor.fetchone()[0] == 0

    def test_update_position_grava_soh_tabela_positions(self, state):
        """Scenario: update_position não toca orders."""
        state.update_position("BTC-USD", "guardiao", {
            "side": "long", "quantity": 1, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })

        cursor = state._conn.execute("SELECT COUNT(*) FROM positions")
        assert cursor.fetchone()[0] == 1

        cursor = state._conn.execute("SELECT COUNT(*) FROM orders")
        assert cursor.fetchone()[0] == 0

    def test_save_pnl_grava_soh_tabela_closed_pnl(self, state):
        """Scenario: save_pnl não toca outras tabelas."""
        state.save_pnl({
            "closed_at": "2026-01-01T10:00:00", "ticker": "BTC-USD",
            "strategy_name": "guardiao", "broker": "binance",
            "entry_price": "50000", "exit_price": "50500",
            "quantity": 1, "side": "long", "pnl_value": "500",
            "pnl_value_display": 500.0, "pnl_pct": 1.0, "reason": "tp_hit",
        })

        cursor = state._conn.execute("SELECT COUNT(*) FROM closed_pnl")
        assert cursor.fetchone()[0] == 1

    def test_save_signal_grava_soh_tabela_signals(self, state):
        """Scenario: save_signal não toca outras tabelas."""
        state.save_signal({
            "created_at": "2026-01-01T10:00:00", "ticker": "BTC-USD",
            "strategy_name": "guardiao", "broker": "binance",
            "signal_type": "BUY", "price": "50000", "reason": "RSI oversold",
            "take_profit_pct": "0.004",
        })

        cursor = state._conn.execute("SELECT COUNT(*) FROM signals")
        assert cursor.fetchone()[0] == 1

    def test_save_tick_grava_soh_tabela_ticks_raw(self, state):
        """Scenario: save_tick não toca outras tabelas."""
        state.save_tick({
            "time": "2026-01-01T10:00:00.123", "symbol": "BTC-USD",
            "broker": "binance", "price": "50000.12", "volume": 100,
            "side": "buy",
        })

        cursor = state._conn.execute("SELECT COUNT(*) FROM ticks_raw")
        assert cursor.fetchone()[0] == 1

    def test_save_ohlcv_grava_soh_tabela_ohlcv(self, state):
        """Scenario: save_ohlcv não toca outras tabelas."""
        state.save_ohlcv({
            "time": "2026-01-01T10:00:00", "symbol": "BTC-USD",
            "broker": "binance", "open": "50000", "high": "50100",
            "low": "49900", "close": "50050", "volume": 1000, "interval": "1m",
        })

        cursor = state._conn.execute("SELECT COUNT(*) FROM ohlcv")
        assert cursor.fetchone()[0] == 1


# ── Requirement: get_position com PK composta ──


class TestPKComposta:
    def test_guardiao_vs_sniper_mesmo_ticker(self, state):
        """Scenario: Duas estratégias no mesmo ticker."""
        state.update_position("BTC-USD", "guardiao", {
            "side": "long", "quantity": 1, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })
        state.update_position("BTC-USD", "sniper", {
            "side": "long", "quantity": 2, "avg_price": "51000",
            "status": "open", "opened_at": "2026-01-01T01:00:00",
            "broker": "binance",
        })

        g = state.get_position("BTC-USD", "guardiao")
        s = state.get_position("BTC-USD", "sniper")
        assert g["avg_price"] == "50000"
        assert s["avg_price"] == "51000"


# ── Requirement: list_orders com filtros (broker, strategy) ──


class TestListOrdersFilters:
    def test_filtro_por_broker(self, state):
        """Scenario: Filtra ordens por broker."""
        state.save_order({
            "created_at": "2026-01-01T00:00:00", "id": "ord-bin",
            "ticker": "BTC-USD", "side": "buy", "quantity": 1,
            "price": "50000", "total_value": "50000", "status": "EXECUTADA",
            "order_type": "open", "broker": "binance", "strategy_name": "guardiao",
        })
        state.save_order({
            "created_at": "2026-01-01T00:00:00", "id": "ord-cb",
            "ticker": "BTC-USD", "side": "buy", "quantity": 1,
            "price": "50100", "total_value": "50100", "status": "EXECUTADA",
            "order_type": "open", "broker": "coinbase", "strategy_name": "guardiao",
        })

        binance_orders = state.list_orders("BTC-USD", broker="binance")
        assert len(binance_orders) == 1
        assert binance_orders[0]["id"] == "ord-bin"


# ── Requirement: Atomicidade por operação ──


class TestAtomicidade:
    def test_falha_em_save_order_nao_afeta_save_pnl(self, state):
        """Scenario: Falha em save_order não afeta save_pnl anterior."""
        # Salva PnL com sucesso
        state.save_pnl({
            "closed_at": "2026-01-01T10:00:00", "ticker": "BTC-USD",
            "strategy_name": "guardiao", "broker": "binance",
            "entry_price": "50000", "exit_price": "50500",
            "quantity": 1, "side": "long", "pnl_value": "500",
            "pnl_value_display": 500.0, "pnl_pct": 1.0, "reason": "tp_hit",
        })

        # Tenta salvar ordem duplicada (vai falhar por PK)
        state.save_order({
            "created_at": "2026-01-01T00:00:00", "id": "ord-1",
            "ticker": "BTC-USD", "side": "buy", "quantity": 1,
            "price": "50000", "total_value": "50000", "status": "EXECUTADA",
            "order_type": "open", "broker": "binance", "strategy_name": "guardiao",
        })

        with pytest.raises(Exception):
            state.save_order({
                "created_at": "2026-01-01T00:00:00", "id": "ord-1",
                "ticker": "BTC-USD", "side": "buy", "quantity": 1,
                "price": "50000", "total_value": "50000", "status": "EXECUTADA",
                "order_type": "open", "broker": "binance", "strategy_name": "guardiao",
            })

        # PnL anterior ainda está lá
        pnl = state.get_closed_pnl("BTC-USD")
        assert len(pnl) == 1


# ── Requirement: Crash recovery via WAL ──


class TestCrashRecovery:
    def test_dados_intactos_apos_kill(self, tmp_path):
        """Scenario: Dados intactos após kill simulado."""
        db_path = tmp_path / "crash_test.db"
        state1 = SQLitePaperState(str(db_path))
        state1.save_order({
            "created_at": "2026-01-01T00:00:00", "id": "ord-1",
            "ticker": "BTC-USD", "side": "buy", "quantity": 1,
            "price": "50000", "total_value": "50000", "status": "EXECUTADA",
            "order_type": "open", "broker": "binance", "strategy_name": "guardiao",
        })
        state1.close()

        # Reabre sem graceful shutdown (simula crash)
        state2 = SQLitePaperState(str(db_path))
        orders = state2.list_orders("BTC-USD")
        assert len(orders) == 1
        assert orders[0]["id"] == "ord-1"
        state2.close()


# ── Requirement: Compatibilidade legado (carregar/salvar) ──


class TestLegacyCompat:
    def test_carregar_retorna_paper_state_data(self, state):
        """Scenario: carregar() monta PaperStateData."""
        result = state.carregar()
        assert isinstance(result, PaperStateData)
        assert result.version == 3

    def test_salvar_carregar_roundtrip(self, state):
        """Scenario: salvar() + carregar() roundtrip."""
        data = PaperStateData(
            base_currency="BRL",
            cashbook={
                "base_currency": "BRL",
                "entries": {
                    "BRL": {"amount": "100000", "conversion_rate": "1"},
                    "USD": {"amount": "2500", "conversion_rate": "5.20"},
                },
            },
            ordens={"ord-1": {"ticker": "BTC-USD", "side": "buy"}},
            posicoes={"BTC-USD": {"quantity": 1, "avg_price": "50000"}},
        )
        state.salvar(data)
        loaded = state.carregar()

        assert loaded.base_currency == "BRL"
        assert "BRL" in loaded.cashbook["entries"]
        assert loaded.cashbook["entries"]["BRL"]["amount"] == "100000"
        assert loaded.cashbook["entries"]["USD"]["amount"] == "2500"
        assert "ord-1" in loaded.ordens
        assert loaded.ordens["ord-1"]["ticker"] == "BTC-USD"
        assert loaded.ordens["ord-1"]["side"] == "buy"
        assert "BTC-USD::default" in loaded.posicoes
        assert loaded.posicoes["BTC-USD::default"]["quantity"] == 1

    def test_resetar(self, state):
        """Scenario: resetar() limpa tudo e retorna PaperStateData."""
        state.update_position("BTC-USD", "guardiao", {
            "side": "long", "quantity": 1, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })

        result = state.resetar()
        assert isinstance(result, PaperStateData)
        assert state.get_position("BTC-USD", "guardiao") is None


# ── Requirement: Conexão única reutilizável ──


class TestConexaoUnica:
    def test_multiplas_queries_sem_reopen(self, state):
        """Scenario: 10 queries usam mesma conexão."""
        conn_id = id(state._conn)
        for _ in range(10):
            state.get_cashbook()
        assert id(state._conn) == conn_id


# ── Requirement: Surrogate key + FK scenarios ──


class TestPositionSurrogateKey:
    def test_update_position_retorna_id(self, state):
        """Scenario: update_position cria posição com surrogate key."""
        state.update_position("BTC-USD", "guardiao", {
            "side": "long", "quantity": 1, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })
        pos = state.get_position("BTC-USD", "guardiao")
        assert pos is not None
        assert pos["id"] == 1

    def test_save_order_com_position_id_fk(self, state):
        """Scenario: Ordem vinculada à posição via FK."""
        state.update_position("BTC-USD", "guardiao", {
            "side": "long", "quantity": 1, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })
        pos = state.get_position("BTC-USD", "guardiao")
        pos_id = pos["id"]

        state.save_order({
            "created_at": "2026-01-01T00:00:00", "id": "ord-1",
            "ticker": "BTC-USD", "side": "buy", "quantity": 1,
            "price": "50000", "total_value": "50000", "status": "EXECUTADA",
            "order_type": "open", "position_id": pos_id,
            "broker": "binance", "strategy_name": "guardiao",
        })

        orders = state.list_orders("BTC-USD")
        assert len(orders) == 1
        assert orders[0]["position_id"] == pos_id

    def test_fk_rejeita_position_id_invalido(self, state):
        """Scenario: FK rejeita order com position_id inexistente."""
        with pytest.raises(sqlite3.IntegrityError):
            state.save_order({
                "created_at": "2026-01-01T00:00:00", "id": "ord-fk",
                "ticker": "BTC-USD", "side": "buy", "quantity": 1,
                "price": "50000", "total_value": "50000", "status": "EXECUTADA",
                "order_type": "open", "position_id": 999,
                "broker": "binance", "strategy_name": "guardiao",
            })


class TestOrderTypeScenarios:
    def test_increase_order_vinculada(self, state):
        """Scenario: Ordem increase vinculada à posição existente."""
        state.update_position("BTC-USD", "guardiao", {
            "side": "long", "quantity": 10, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })
        pos_id = state.get_position("BTC-USD", "guardiao")["id"]

        state.save_order({
            "created_at": "2026-01-02T00:00:00", "id": "ord-inc",
            "ticker": "BTC-USD", "side": "buy", "quantity": 5,
            "price": "52000", "total_value": "260000", "status": "EXECUTADA",
            "order_type": "increase", "position_id": pos_id,
            "broker": "binance", "strategy_name": "guardiao",
        })

        # Simula recalculo do preço médio
        # (10*50000 + 5*52000) / 15 = 50666.67
        state.update_position("BTC-USD", "guardiao", {
            "quantity": 15, "avg_price": "50666.67",
        })

        pos = state.get_position("BTC-USD", "guardiao")
        assert pos["quantity"] == 15
        assert pos["avg_price"] == "50666.67"

        orders = state.list_orders("BTC-USD")
        inc_orders = [o for o in orders if o["order_type"] == "increase"]
        assert len(inc_orders) == 1
        assert inc_orders[0]["position_id"] == pos_id

    def test_partial_close_order(self, state):
        """Scenario: Ordem partial_close com quantity parcial."""
        state.update_position("BTC-USD", "guardiao", {
            "side": "long", "quantity": 10, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })
        pos_id = state.get_position("BTC-USD", "guardiao")["id"]

        state.save_order({
            "created_at": "2026-01-03T00:00:00", "id": "ord-pc",
            "ticker": "BTC-USD", "side": "sell", "quantity": 5,
            "price": "51000", "total_value": "255000", "status": "EXECUTADA",
            "order_type": "partial_close", "position_id": pos_id,
            "broker": "binance", "strategy_name": "guardiao",
        })

        orders = state.list_orders("BTC-USD")
        pc_orders = [o for o in orders if o["order_type"] == "partial_close"]
        assert len(pc_orders) == 1
        assert pc_orders[0]["quantity"] == 5

    def test_grid_position_com_nivel(self, state):
        """Scenario: Posição grid com grid_level e parent_position_id."""
        # Posição pai
        state.update_position("BTC-USD", "grid-master", {
            "side": "long", "quantity": 5, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })
        parent_id = state.get_position("BTC-USD", "grid-master")["id"]

        # Sub-posição grid nível 3
        state.update_position("BTC-USD", "grid-3", {
            "side": "long", "quantity": 1, "avg_price": "48000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance", "grid_level": 3,
            "parent_position_id": f"pos-{parent_id}",
        })

        sub = state.get_position("BTC-USD", "grid-3")
        assert sub["grid_level"] == 3
        assert sub["parent_position_id"] == f"pos-{parent_id}"

        # Posições independentes
        master = state.get_position("BTC-USD", "grid-master")
        assert master["grid_level"] is None
        assert master["parent_position_id"] is None

    def test_hierarquia_grid_5_niveis(self, state):
        """Scenario: 5 sub-posições grid vinculadas ao mesmo pai."""
        state.update_position("BTC-USD", "grid-master", {
            "side": "long", "quantity": 5, "avg_price": "50000",
            "status": "open", "opened_at": "2026-01-01T00:00:00",
            "broker": "binance",
        })
        parent_id = state.get_position("BTC-USD", "grid-master")["id"]

        for level in range(1, 6):
            state.update_position("BTC-USD", f"grid-{level}", {
                "side": "long", "quantity": 1,
                "avg_price": str(50000 - level * 500),
                "status": "open", "opened_at": "2026-01-01T00:00:00",
                "broker": "binance", "grid_level": level,
                "parent_position_id": f"pos-{parent_id}",
            })

        # Verifica todas sub-posições
        for level in range(1, 6):
            sub = state.get_position("BTC-USD", f"grid-{level}")
            assert sub["grid_level"] == level
            assert sub["parent_position_id"] == f"pos-{parent_id}"
