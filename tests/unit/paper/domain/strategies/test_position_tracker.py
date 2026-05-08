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

    def test_open_position_duplicada_ignora(self):
        """WHEN posição já existe THEN open_position ignora (mantém existente)."""
        from src.core.paper.domain.strategies.position_tracker import PositionTracker

        tracker = PositionTracker()
        tracker.open_position("BTC-USD", Decimal("50000"))
        tracker.open_position("BTC-USD", Decimal("55000"))

        pos = tracker.get_position("BTC-USD")
        assert pos["preco_entrada"] == Decimal("50000")

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
