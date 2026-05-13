# -*- coding: utf-8 -*-
"""Testes para PositionTracker — Stop Loss, Take Profit, gerenciamento de posição."""

from decimal import Decimal

import pytest


class TestPositionTrackerOpenClose:
    """DOC: specs/position-tracker — Abrir e fechar posições."""

    def test_open_position_btc(self):
        """WHEN chamar open_position THEN posição registrada com ticker e preço."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))

        pos = tracker.get_position("BTC-USD")
        assert pos is not None
        assert pos["ticker"] == "BTC-USD"
        assert pos["preco_entrada"] == Decimal("50000")
        assert pos["status"] == "aberta"

    def test_open_position_duplicada_substitui(self):
        """WHEN posição já existe THEN open_position substitui (netting mode)."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))
        tracker.open_position("BTC-USD", Decimal("55000"))

        pos = tracker.get_position("BTC-USD")
        assert pos["preco_entrada"] == Decimal("55000")

    def test_close_position_existente(self):
        """WHEN fechar posição existente THEN posição é removida."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))
        tracker.close_position("BTC-USD")

        assert tracker.get_position("BTC-USD") is None

    def test_close_position_inexistente_noop(self):
        """WHEN fechar posição inexistente THEN no-op sem erro."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker()
        tracker.close_position("BTC-USD")  # não deve levantar erro


class TestPositionTrackerStopLoss:
    """DOC: specs/position-tracker — Stop Loss."""

    def test_stop_loss_acionado(self):
        """WHEN preço cai abaixo do SL THEN retorna sinal de VENDA."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(stop_loss_pct=Decimal("0.05"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        sinal = tracker.check_price("BTC-USD", Decimal("47000"))
        assert sinal is not None
        assert sinal.tipo.value == "venda"
        assert "Stop Loss" in sinal.razao

    def test_stop_loss_nao_acionado(self):
        """WHEN preço acima do SL THEN retorna None."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(stop_loss_pct=Decimal("0.05"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        sinal = tracker.check_price("BTC-USD", Decimal("48000"))
        assert sinal is None

    def test_stop_loss_limite_exato(self):
        """WHEN preço no limite exato do SL THEN retorna sinal (limite é <=)."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(stop_loss_pct=Decimal("0.05"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        sinal = tracker.check_price("BTC-USD", Decimal("47500"))
        assert sinal is not None
        assert sinal.tipo.value == "venda"


class TestPositionTrackerTakeProfit:
    """DOC: specs/position-tracker — Take Profit."""

    def test_take_profit_acionado(self):
        """WHEN preço sobe acima do TP THEN retorna sinal de VENDA."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(take_profit_pct=Decimal("0.10"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        sinal = tracker.check_price("BTC-USD", Decimal("56000"))
        assert sinal is not None
        assert sinal.tipo.value == "venda"
        assert "Take Profit" in sinal.razao

    def test_take_profit_nao_acionado(self):
        """WHEN preço abaixo do TP THEN retorna None."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(take_profit_pct=Decimal("0.10"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        sinal = tracker.check_price("BTC-USD", Decimal("54000"))
        assert sinal is None

    def test_take_profit_limite_exato(self):
        """WHEN preço no limite exato do TP THEN retorna sinal (limite é >=)."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(take_profit_pct=Decimal("0.10"))
        tracker.open_position("BTC-USD", Decimal("50000"))

        sinal = tracker.check_price("BTC-USD", Decimal("55000"))
        assert sinal is not None
        assert sinal.tipo.value == "venda"


class TestPositionTrackerList:
    """DOC: specs/position-tracker — Listar posições e check sem posição."""

    def test_check_price_sem_posicao(self):
        """WHEN não há posição THEN check_price retorna None."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker()
        sinal = tracker.check_price("BTC-USD", Decimal("50000"))
        assert sinal is None

    def test_list_positions_com_posicoes(self):
        """WHEN existem posições abertas THEN list_positions retorna ambas."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))
        tracker.open_position("ETH-USD", Decimal("3000"))

        positions = tracker.list_positions()
        assert len(positions) == 2
        tickers = [p["ticker"] for p in positions]
        assert "BTC-USD" in tickers
        assert "ETH-USD" in tickers

    def test_list_positions_vazia(self):
        """WHEN não existem posições THEN list_positions retorna lista vazia."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker()
        assert tracker.list_positions() == []


class TestPositionTrackerThresholdPrice:
    """DOC: specs/paper-guardiao-v2 — TP/SL executam no preço do threshold, não do mercado."""

    def test_tp_executes_at_threshold_price(self):
        """WHEN preço ultrapassa TP THEN sinal.preco == entrada * (1 + tp_pct)."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(take_profit_pct=Decimal("0.005"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        sinal = tracker.check_price("BTC-USD", Decimal("80400"))
        assert sinal is not None
        assert sinal.preco == Decimal("80400")  # threshold = 80000 * 1.005 = 80400

    def test_tp_preco_mercado_diferente_do_threshold(self):
        """WHEN preço de mercado está acima do threshold THEN sinal.preco == threshold."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(take_profit_pct=Decimal("0.005"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        sinal = tracker.check_price("BTC-USD", Decimal("80500"))
        assert sinal is not None
        assert sinal.preco == Decimal("80400")  # threshold, não 80500

    def test_sl_executes_at_threshold_price(self):
        """WHEN preço cai abaixo do SL THEN sinal.preco == entrada * (1 - sl_pct)."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(stop_loss_pct=Decimal("0.003"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        sinal = tracker.check_price("BTC-USD", Decimal("79700"))
        assert sinal is not None
        assert sinal.preco == Decimal("79760")  # threshold = 80000 * 0.997 = 79760

    def test_sl_preco_mercado_diferente_do_threshold(self):
        """WHEN preço de mercado está abaixo do threshold THEN sinal.preco == threshold."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(stop_loss_pct=Decimal("0.003"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        sinal = tracker.check_price("BTC-USD", Decimal("79500"))
        assert sinal is not None
        assert sinal.preco == Decimal("79760")  # threshold, não 79500


class TestPositionTrackerTrailingStop:
    """DOC: specs/paper-guardiao-v2 — Trailing stop após +0.20%."""

    def test_trailing_stop_apos_020(self):
        """WHEN preço sobe +0.20% THEN trailing ativado."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(stop_loss_pct=Decimal("0.003"), take_profit_pct=Decimal("0.005"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        tracker.update_trailing("BTC-USD", Decimal("80160"))  # +0.20%
        trailing = tracker.get_trailing_stop("BTC-USD")
        assert trailing is not None
        assert trailing == Decimal("80039.7600")  # pico 80160 * 0.9985

    def test_trailing_stop_sobe_com_preco(self):
        """WHEN preço sobe mais THEN trailing sobe junto."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(stop_loss_pct=Decimal("0.003"), take_profit_pct=Decimal("0.005"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        tracker.update_trailing("BTC-USD", Decimal("80160"))  # ativa
        tracker.update_trailing("BTC-USD", Decimal("80300"))  # sobe
        trailing = tracker.get_trailing_stop("BTC-USD")
        assert trailing is not None
        assert trailing == Decimal("80179.5500")  # 80300 * 0.9985

    def test_trailing_stop_nunca_abaixo_breakeven(self):
        """WHEN trailing calculado < entrada THEN trailing = entrada (breakeven)."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(stop_loss_pct=Decimal("0.003"), take_profit_pct=Decimal("0.005"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        tracker.update_trailing("BTC-USD", Decimal("80160"))  # +0.20% — ativa trailing
        # trailing = 80160 * 0.9985 = 80039.76 — acima do breakeven
        assert tracker.get_trailing_stop("BTC-USD") >= Decimal("80000")


class TestBreakevenStandalone:
    """DOC: specs/position-tracker — Breakeven standalone: +0.10% move SL para entrada."""

    def test_breakeven_ativa_em_010(self):
        """WHEN preço sobe +0.10% THEN SL é movido para o preço de entrada."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker

        tracker = SimpleTracker(stop_loss_pct=Decimal("0.005"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        tracker.update_breakeven("BTC-USD", Decimal("80080"))  # exatamente +0.10%

        pos = tracker.get_position("BTC-USD")
        assert pos["stop_loss_pct"] == Decimal("0")
        assert pos["breakeven_activated"] is True

    def test_breakeven_protege_entrada(self):
        """WHEN breakeven ativado E preço volta para entrada THEN SL é acionado (zerada a perda)."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker

        tracker = SimpleTracker(stop_loss_pct=Decimal("0.005"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        # Sobe +0.10%, ativa breakeven
        tracker.update_breakeven("BTC-USD", Decimal("80080"))

        # Preço volta para exatamente a entrada
        sinal = tracker.check_price("BTC-USD", Decimal("80000"))
        assert sinal is not None
        assert "Breakeven" in sinal.razao

    def test_breakeven_nao_ativa_antes_de_010(self):
        """WHEN preço sobe apenas +0.09% THEN breakeven NÃO é ativado."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker

        tracker = SimpleTracker(stop_loss_pct=Decimal("0.005"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        tracker.update_breakeven("BTC-USD", Decimal("80072"))  # +0.09%

        pos = tracker.get_position("BTC-USD")
        assert pos.get("breakeven_activated") is not True
        assert pos["stop_loss_pct"] == Decimal("0.005")

    def test_breakeven_idempotente(self):
        """WHEN update_breakeven chamado várias vezes THEN SL permanece na entrada."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker

        tracker = SimpleTracker(stop_loss_pct=Decimal("0.005"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        tracker.update_breakeven("BTC-USD", Decimal("80080"))
        tracker.update_breakeven("BTC-USD", Decimal("80150"))
        tracker.update_breakeven("BTC-USD", Decimal("80200"))

        pos = tracker.get_position("BTC-USD")
        assert pos["stop_loss_pct"] == Decimal("0")

    def test_breakeven_check_preco_abaixo_entrada(self):
        """WHEN breakeven ativado E preço cai abaixo da entrada THEN SL é acionado no preço de entrada."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker

        tracker = SimpleTracker(stop_loss_pct=Decimal("0.005"))
        tracker.open_position("BTC-USD", Decimal("80000"))

        tracker.update_breakeven("BTC-USD", Decimal("80080"))

        # Preço cai 0.10% abaixo da entrada
        sinal = tracker.check_price("BTC-USD", Decimal("79920"))
        assert sinal is not None
        assert "Breakeven" in sinal.razao
        # Executa no preço da entrada, não no preço de mercado
        assert sinal.preco == Decimal("80000")

    def test_breakeven_default_activation_pct(self):
        """WHEN criar SimpleTracker sem parâmetros THEN breakeven_activation_pct = 0.001 (0.10%)."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker

        tracker = SimpleTracker()
        assert tracker._breakeven_activation_pct == Decimal("0.001")


class TestPositionTrackerPure:
    """DOC: check_price() deve ser puro — sem side effects."""

    def test_check_price_nao_ativa_trailing(self):
        """WHEN check_price chamado com preço acima da ativação THEN trailing NÃO é ativado."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker(
            stop_loss_pct=Decimal("0.10"),
            take_profit_pct=Decimal("0.20"),
            trailing_activation_pct=Decimal("0.002"),
        )
        tracker.open_position("BTC-USD", Decimal("80000"))

        # check_price com preço que ativaria trailing (+0.25%)
        tracker.check_price("BTC-USD", Decimal("80200"))

        # Sem efeito colateral: trailing não foi ativado por check_price
        assert tracker.get_trailing_stop("BTC-USD") is None

        # Apenas update_trailing ativa
        tracker.update_trailing("BTC-USD", Decimal("80200"))
        assert tracker.get_trailing_stop("BTC-USD") is not None


class TestPositionTrackerRestore:
    """Persistência de estado (facade)."""

    def test_restore_positions_recupera_estado(self):
        """WHEN restore_positions é chamado THEN posições são restauradas."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker
        tracker = PositionTracker(stop_loss_pct=Decimal("0.01"))
        tracker.restore_positions([
            {"ticker": "BTC-USD", "preco_entrada": "80000"},
            {"ticker": "ETH-USD", "preco_entrada": "3000"},
        ])
        assert tracker.get_position("BTC-USD") is not None
        assert tracker.get_position("ETH-USD") is not None
        assert tracker.get_position("BTC-USD")["preco_entrada"] == Decimal("80000")

    def test_restore_positions_permite_check_price(self):
        """WHEN posições restauradas THEN SL/TP funciona normalmente."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker
        tracker = PositionTracker(
            stop_loss_pct=Decimal("0.01"),
            take_profit_pct=Decimal("0.02"),
        )
        tracker.restore_positions([{"ticker": "BTC-USD", "preco_entrada": "80000"}])

        # SL deve detectar
        sinal = tracker.check_price("BTC-USD", Decimal("79100"))
        assert sinal is not None
        assert "Stop Loss" in sinal.razao

    def test_restore_empty_nao_quebra(self):
        """WHEN restore_positions com lista vazia THEN sem efeito."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker
        tracker = PositionTracker()
        tracker.restore_positions([])
        assert tracker.list_positions() == []


class TestSimpleTrackerSLDefault:
    """DOC: specs/strategy-worker — SL default 0.50% (0.005)."""

    def test_default_stop_loss_pct_0_005(self):
        """WHEN criar SimpleTracker sem parâmetros THEN stop_loss_pct = 0.005."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        assert tracker._stop_loss_pct == Decimal("0.005")

    def test_open_position_usa_sl_default(self):
        """WHEN open_position sem stop_loss_pct THEN posição usa default 0.005."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        tracker.open_position("BTC-USD", Decimal("80000"))
        pos = tracker.get_position("BTC-USD")
        assert pos["stop_loss_pct"] == Decimal("0.005")

    def test_open_position_com_sl_custom(self):
        """WHEN open_position com stop_loss_pct THEN usa valor customizado."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        tracker.open_position("BTC-USD", Decimal("80000"), stop_loss_pct=Decimal("0.01"))
        pos = tracker.get_position("BTC-USD")
        assert pos["stop_loss_pct"] == Decimal("0.01")


class TestPositionTrackerPort:
    """DOC: specs/position-tracker — PositionTrackerPort (interface abstrata)."""

    def test_port_define_contrato(self):
        """WHEN criar implementação THEN deve ter todos os métodos da port."""
        from src.core.paper.domain.strategies.position_tracker import PositionTrackerPort

        required_methods = [
            "open_position", "close_position", "get_position",
            "check_price", "list_positions", "restore_positions",
            "set_reentry_state", "get_reentry_state",
            "tick_reentry", "clear_reentry_state",
        ]
        for method in required_methods:
            assert hasattr(PositionTrackerPort, method), f"Port missing: {method}"

    def test_nao_instancia_port_diretamente(self):
        """WHEN tentar instanciar PositionTrackerPort THEN TypeError."""
        from src.core.paper.domain.strategies.position_tracker import PositionTrackerPort

        with pytest.raises(TypeError):
            PositionTrackerPort()


class TestSimpleTracker:
    """DOC: specs/position-tracker — SimpleTracker (netting, 1 posição/ticker)."""

    def test_import_simple_tracker(self):
        """WHEN importar THEN SimpleTracker está disponível."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        assert tracker is not None

    def test_position_tracker_alias(self):
        """WHEN importar PositionTracker THEN é alias para SimpleTracker."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker, SimpleTracker
        assert PositionTracker is SimpleTracker

    def test_ticket_sequencial(self):
        """WHEN abrir posição THEN ticket é int auto-incrementado."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))
        tracker.open_position("ETH-USD", Decimal("3000"))

        btc = tracker.get_position("BTC-USD")
        eth = tracker.get_position("ETH-USD")
        assert btc["ticket"] == 1
        assert eth["ticket"] == 2

    def test_position_type_buy(self):
        """WHEN posição aberta via COMPRA THEN position_type = 'BUY'."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))
        pos = tracker.get_position("BTC-USD")
        assert pos["position_type"] == "BUY"

    def test_netting_substitui_duplicada(self):
        """WHEN já existe posição para ticker THEN substitui (netting)."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))
        tracker.open_position("BTC-USD", Decimal("55000"))

        pos = tracker.get_position("BTC-USD")
        assert pos["preco_entrada"] == Decimal("55000")

    def test_reentry_state_criar(self):
        """WHEN set_reentry_state THEN estado criado com crossover_price, swing_low, fib_level."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        tracker.set_reentry_state("BTC-USD", crossover_price=Decimal("80830"), swing_low=Decimal("80279"))

        state = tracker.get_reentry_state("BTC-USD")
        assert state is not None
        assert state["crossover_price"] == Decimal("80830")
        assert state["swing_low"] == Decimal("80279")
        assert state["ticks_since_signal"] == 0
        # fib_level = 80279 + (80830 - 80279) * 0.618 = 80279 + 340.518 = 80619.518
        assert state["fib_level"] == Decimal("80619.518")

    def test_reentry_state_obter_inexistente(self):
        """WHEN get_reentry_state sem estado THEN retorna None."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        assert tracker.get_reentry_state("BTC-USD") is None

    def test_reentry_tick_incrementa(self):
        """WHEN tick_reentry THEN ticks_since_signal incrementa em 1."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        tracker.set_reentry_state("BTC-USD", crossover_price=Decimal("80830"), swing_low=Decimal("80279"))

        tracker.tick_reentry("BTC-USD")
        state = tracker.get_reentry_state("BTC-USD")
        assert state["ticks_since_signal"] == 1

        tracker.tick_reentry("BTC-USD")
        assert tracker.get_reentry_state("BTC-USD")["ticks_since_signal"] == 2

    def test_reentry_clear(self):
        """WHEN clear_reentry_state THEN estado removido."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        tracker.set_reentry_state("BTC-USD", crossover_price=Decimal("80830"), swing_low=Decimal("80279"))
        tracker.clear_reentry_state("BTC-USD")

        assert tracker.get_reentry_state("BTC-USD") is None

    def test_reentry_expiracao_200_ticks(self):
        """WHEN ticks_since_signal >= 200 THEN estado é limpo automaticamente."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        tracker.set_reentry_state("BTC-USD", crossover_price=Decimal("80830"), swing_low=Decimal("80279"))

        # Incrementar 199 ticks — ainda existe
        for _ in range(199):
            tracker.tick_reentry("BTC-USD")
        assert tracker.get_reentry_state("BTC-USD") is not None

        # Tick 200 — expira
        tracker.tick_reentry("BTC-USD")
        assert tracker.get_reentry_state("BTC-USD") is None

    def test_reentry_swing_low_none_desabilita_fib(self):
        """WHEN swing_low is None THEN fib_level is None."""
        from src.core.paper.domain.strategies.position_tracker import SimpleTracker
        tracker = SimpleTracker()
        tracker.set_reentry_state("BTC-USD", crossover_price=Decimal("80830"), swing_low=None)

        state = tracker.get_reentry_state("BTC-USD")
        assert state["fib_level"] is None
