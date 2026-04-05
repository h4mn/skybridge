# -*- coding: utf-8 -*-
"""
Testes unitários para MercadoSimulado.

Testa simulador de mercado com preços realistas:
- PrecoSimulado (Value Object)
- MercadoSimulado (Entity)
- GeradorDePrecos (Service)
- Volatilidade (Enum)

Simula movimentos de mercado baseados em:
- Volatilidade configurável
- Random walk com tendência
- Preços iniciais realistas (baseados em Binance)

TDD: RED → GREEN → REFACTOR
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from typing import NamedTuple
import random

from src.core.paper.domain.mercado_simulado import (
    PrecoSimulado,
    Ticker,
    Volatilidade,
    MercadoSimulado,
    GeradorDePrecos,
    MovimentoMercado,
)


# =============================================================================
# Testes: Value Objects
# =============================================================================

class TestTicker:
    """Testes para Value Object Ticker."""

    def test_ticker_criado(self):
        """Cria Ticker."""
        ticker = Ticker("BTC-USD")

        assert ticker.value == "BTC-USD"

    def test_ticker_imutavel(self):
        """Ticker deve ser imutável."""
        ticker = Ticker("BTC-USD")

        with pytest.raises(Exception):  # FrozenInstanceError
            ticker.value = "ETH-USD"


class TestPrecoSimulado:
    """Testes para Value Object PrecoSimulado."""

    def test_preco_simulado_criado(self):
        """Cria PrecoSimulado."""
        preco = PrecoSimulado(
            ticker=Ticker("BTC-USD"),
            valor=Decimal("85000.00"),
            timestamp=datetime.now(),
        )

        assert preco.ticker.value == "BTC-USD"
        assert preco.valor == Decimal("85000.00")

    def test_preco_simulado_serializavel(self):
        """PrecoSimulado deve ser serializável."""
        preco = PrecoSimulado(
            ticker=Ticker("BTC-USD"),
            valor=Decimal("85000.00"),
            timestamp=datetime(2026, 3, 31, 12, 0, 0),
        )

        data = preco.to_dict()

        assert data["ticker"] == "BTC-USD"
        assert data["valor"] == "85000.00"
        assert "timestamp" in data


# =============================================================================
# Testes: Enum Volatilidade
# =============================================================================

class TestVolatilidade:
    """Testes para Enum Volatilidade."""

    def test_volatilidade_baixa(self):
        """Volatilidade BAIXA tem menor variação."""
        assert Volatilidade.BAIXA.variacao_maxima == Decimal("0.01")  # 1%

    def test_volatilidade_media(self):
        """Volatilidade MEDIA tem variação moderada."""
        assert Volatilidade.MEDIA.variacao_maxima == Decimal("0.03")  # 3%

    def test_volatilidade_alta(self):
        """Volatilidade ALTA tem maior variação."""
        assert Volatilidade.ALTA.variacao_maxima == Decimal("0.08")  # 8%

    def test_volatilidade_extrema(self):
        """Volatilidade EXTREMA tem variação muito alta."""
        assert Volatilidade.EXTREMA.variacao_maxima == Decimal("0.20")  # 20%


# =============================================================================
# Testes: Entity MercadoSimulado
# =============================================================================

class TestMercadoSimulado:
    """Testes para entidade MercadoSimulado."""

    def test_mercado_criado_com_preco_inicial(self):
        """Cria MercadoSimulado com preço inicial."""
        mercado = MercadoSimulado(
            ticker=Ticker("BTC-USD"),
            preco_inicial=Decimal("85000.00"),
            volatilidade=Volatilidade.MEDIA,
        )

        assert mercado.ticker.value == "BTC-USD"
        assert mercado.preco_atual == Decimal("85000.00")
        assert mercado.volatilidade == Volatilidade.MEDIA

    def test_mercado_gerar_novo_preco(self):
        """Gerar novo preço com variação dentro da volatilidade."""
        mercado = MercadoSimulado(
            ticker=Ticker("BTC-USD"),
            preco_inicial=Decimal("85000.00"),
            volatilidade=Volatilidade.MEDIA,  # 3% max
        )

        novo_preco = mercado.gerar_proximo_preco()

        # Variação deve estar dentro de ±3%
        variacao = abs((novo_preco.valor - Decimal("85000.00")) / Decimal("85000.00"))
        assert variacao <= Decimal("0.03")

    def test_mercado_preco_minimo_nao_negativo(self):
        """Preço gerado nunca deve ser negativo ou zero."""
        mercado = MercadoSimulado(
            ticker=Ticker("BTC-USD"),
            preco_inicial=Decimal("100.00"),
            volatilidade=Volatilidade.EXTREMA,  # 20% - max variação
        )

        # Mesmo com volatilidade extrema, preço deve ser positivo
        for _ in range(100):
            novo_preco = mercado.gerar_proximo_preco()
            assert novo_preco.valor > 0

    def test_mercado_historico_de_precos(self):
        """Histórico mantém últimos N preços gerados."""
        mercado = MercadoSimulado(
            ticker=Ticker("BTC-USD"),
            preco_inicial=Decimal("85000.00"),
            volatilidade=Volatilidade.MEDIA,
        )

        # Gerar alguns preços
        mercado.gerar_proximo_preco()
        mercado.gerar_proximo_preco()
        mercado.gerar_proximo_preco()

        historico = mercado.historico

        # Histórico contém apenas preços gerados (3)
        assert len(historico) == 3


# =============================================================================
# Testes: Service GeradorDePrecos
# =============================================================================

class TestGeradorDePrecos:
    """Testes para serviço GeradorDePrecos."""

    @pytest.fixture
    def gerador(self):
        """Cria gerador de preços."""
        return GeradorDePrecos()

    def test_gerar_preco_para_ticker(self, gerador):
        """Gerar preço para ticker específico."""
        preco = gerador.gerar_para_ticker(
            ticker=Ticker("BTC-USD"),
            preco_base=Decimal("85000.00"),
            volatilidade=Volatilidade.MEDIA,
        )

        assert preco.ticker.value == "BTC-USD"
        assert preco.valor > 0

    def test_gerar_preco_deterministico_com_seed(self, gerador):
        """Gerar preço com seed deve ser determinístico."""
        random.seed(42)

        preco1 = gerador.gerar_para_ticker(
            ticker=Ticker("BTC-USD"),
            preco_base=Decimal("85000.00"),
            volatilidade=Volatilidade.MEDIA,
        )

        random.seed(42)

        preco2 = gerador.gerar_para_ticker(
            ticker=Ticker("BTC-USD"),
            preco_base=Decimal("85000.00"),
            volatilidade=Volatilidade.MEDIA,
        )

        # Com mesma seed, preços devem ser idênticos
        assert preco1.valor == preco2.valor

    def test_gerar_lote_precos_multiplos_tickers(self, gerador):
        """Gerar lote de preços para múltiplos tickers."""
        tickers = [
            Ticker("BTC-USD"),
            Ticker("ETH-USD"),
            Ticker("PETR4.SA"),
        ]

        lotes = gerador.gerar_lote(
            tickers=tickers,
            precos_base={
                Ticker("BTC-USD"): Decimal("85000.00"),
                Ticker("ETH-USD"): Decimal("3000.00"),
                Ticker("PETR4.SA"): Decimal("35.00"),
            },
            volatilidade=Volatilidade.MEDIA,
        )

        assert len(lotes) == 3
        assert all(p.valor > 0 for p in lotes)


# =============================================================================
# Testes: MovimentoMercado
# =============================================================================

class TestMovimentoMercado:
    """Testes para Enum MovimentoMercado."""

    def test_movimento_alta(self):
        """Movimento ALTA aumenta preço."""
        movimento = MovimentoMercado.ALTA
        preco = Decimal("100.00")

        novo = movimento.aplicar(preco, Decimal("0.05"))  # 5%

        assert novo > preco

    def test_movimento_baixa(self):
        """Movimento BAIXA diminui preço."""
        movimento = MovimentoMercado.BAIXA
        preco = Decimal("100.00")

        novo = movimento.aplicar(preco, Decimal("0.05"))  # 5%

        assert novo < preco

    def test_movimento_lateral(self):
        """Movimento LATERAL mantém preço similar."""
        movimento = MovimentoMercado.LATERAL
        preco = Decimal("100.00")

        novo = movimento.aplicar(preco, Decimal("0.02"))  # 2%

        # Deve estar bem próximo ao original (±2%)
        variacao = abs((novo - preco) / preco)
        assert variacao <= Decimal("0.02")
