"""
Testes unitários para GeradorDeRelatorio.

Testa geração de relatórios:
- Performance por período
- Top ganhadores/perdedores
- Resumo de PnL
- Análise de risco (CalculadorDeRisco)
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import NamedTuple

import pytest

from src.core.paper.domain.currency import Currency
from src.core.paper.domain.money import Money
from src.core.paper.domain.portfolio_view import PortfolioView, PositionView
from src.core.paper.domain.quantity import Quantity, AssetType
from src.core.paper.domain.services.gerador_relatorio import (
    GeradorDeRelatorio,
    RelatorioPerformance,
    RankingItem,
    ResumoPnL,
)
from src.core.paper.domain.services.calculador_risco import CalculadorDeRisco


class AtivoPerformance(NamedTuple):
    """Performance de um ativo para testes."""

    ticker: str
    pnl: Decimal
    qtd_trades: int


class TestGeradorDeRelatorio:
    """Testes para GeradorDeRelatorio."""

    @pytest.fixture
    def gerador(self):
        """Cria gerador de relatórios."""
        calculador = CalculadorDeRisco()
        return GeradorDeRelatorio(calculador_risco=calculador)

    @pytest.fixture
    def portfolio(self):
        """Portfolio com posições e PnL."""
        return PortfolioView(
            positions=[
                PositionView(
                    ticker="PETR4.SA",
                    quantity=Quantity(Decimal("100"), precision=0, min_tick=Decimal("1"), asset_type=AssetType.STOCK),
                    market_price=Money(Decimal("35.00"), Currency.BRL),
                    cost_basis=Money(Decimal("30.00"), Currency.BRL),
                ),
                PositionView(
                    ticker="VALE3.SA",
                    quantity=Quantity(Decimal("200"), precision=0, min_tick=Decimal("1"), asset_type=AssetType.STOCK),
                    market_price=Money(Decimal("65.00"), Currency.BRL),
                    cost_basis=Money(Decimal("70.00"), Currency.BRL),
                ),
            ],
            base_currency=Currency.BRL,
            cash=Money(Decimal("5000"), Currency.BRL),
        )

    def test_gerar_relatorio_performance(self, gerador, portfolio):
        """Gera relatório de performance completo."""
        relatorio = gerador.gerar_performance(portfolio)

        assert relatorio is not None
        assert hasattr(relatorio, "data")
        assert hasattr(relatorio, "patrimonio_total")

    def test_calcular_ranking_ganhadores_perdedores(self, gerador):
        """Calcula ranking de ativos por PnL."""
        ativos = [
            AtivoPerformance("PETR4.SA", Decimal("1000"), 5),
            AtivoPerformance("VALE3.SA", Decimal("-500"), 3),
            AtivoPerformance("BTC-USD", Decimal("5000"), 2),
            AtivoPerformance("ETH-USD", Decimal("-200"), 1),
        ]

        ranking = gerador._calcular_ranking(ativos)

        # Top ganhadores
        assert ranking[0].ticker == "BTC-USD"
        assert ranking[0].pnl == Decimal("5000")

        # Top perdedores (último tem maior PnL negativo)
        assert ranking[-1].ticker in ["ETH-USD", "VALE3.SA"]

    def test_ranking_limita_top_n(self, gerador):
        """Ranking pode ser limitado a top N."""
        ativos = [
            AtivoPerformance(f"ATIVO{i}", Decimal(str(i)), 1)
            for i in range(10)
        ]

        ranking_top5 = gerador._calcular_ranking(ativos, top_n=5)

        assert len(ranking_top5) == 5

    def test_calcular_resumo_pnl(self, gerador, portfolio):
        """Calcula resumo de PnL total."""
        resumo = gerador._calcular_resumo_pnl(portfolio)

        # PETR4: (35-30)*100 = 500
        # VALE3: (65-70)*200 = -1000
        # Total: -500
        assert resumo.pnl_nao_realizado == Decimal("-500")

        assert hasattr(resumo, "pnl_realizado")
        assert hasattr(resumo, "pnl_nao_realizado")

    def test_integrar_com_calculador_risco(self, gerador, portfolio):
        """Relatório inclui métricas de risco."""
        relatorio = gerador.gerar_performance(portfolio)

        # Deve incluir métricas do CalculadorDeRisco
        assert hasattr(relatorio, "metricas_risco")
        assert hasattr(relatorio.metricas_risco, "exposicao_total")
        assert hasattr(relatorio.metricas_risco, "var_95")

    def test_relatorio_retorna_dados_estruturados(self, gerador, portfolio):
        """Relatório retorna dados estruturados (Pydantic-like)."""
        relatorio = gerador.gerar_performance(portfolio)

        # Deve ter método to_dict ou ser serializável
        assert hasattr(relatorio, "to_dict")

        dados = relatorio.to_dict()
        assert isinstance(dados, dict)
        assert "data" in dados
        assert "patrimonio_total" in dados


class TestRelatorioPerformance:
    """Testes para value object RelatorioPerformance."""

    def test_relatorio_performance_imutavel(self):
        """RelatorioPerformance deve ser imutável (frozen)."""
        from dataclasses import FrozenInstanceError

        relatorio = RelatorioPerformance(
            data=date.today(),
            patrimonio_total=Decimal("10000"),
            metricas_risco=None,  # tipo dummy
            ranking=[],
            resumo_pnl=None,  # tipo dummy
        )

        # Tentar modificar deve levantar erro
        with pytest.raises(FrozenInstanceError):
            relatorio.patrimonio_total = Decimal("20000")


class TestRankingItem:
    """Testes para value object RankingItem."""

    def test_ranking_item_ordenacao(self):
        """RankingItem deve ordenar por PnL decrescente."""
        item1 = RankingItem(ticker="A", pnl=Decimal("100"), qtd_trades=1)
        item2 = RankingItem(ticker="B", pnl=Decimal("200"), qtd_trades=2)
        item3 = RankingItem(ticker="C", pnl=Decimal("-50"), qtd_trades=0)

        ranking = [item1, item2, item3]
        ranking.sort()  # Deve ordenar por PnL

        assert ranking[0].ticker == "B"  # Maior PnL
        assert ranking[1].ticker == "A"
        assert ranking[2].ticker == "C"  # Menor PnL
