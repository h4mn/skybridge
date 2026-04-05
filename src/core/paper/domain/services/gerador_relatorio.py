"""
Gerador de Relatório - Serviço de Domínio.

Gera relatórios de performance do portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Protocol, NamedTuple

from ..portfolio_view import PortfolioView
from .calculador_risco import CalculadorDeRisco, MetricasRisco


@dataclass(frozen=True)
class RankingItem:
    """
    Item de ranking de performance.

    Attributes:
        ticker: Código do ativo
        pnl: Lucro/prejuízo total
        qtd_trades: Quantidade de trades
    """

    ticker: str
    pnl: Decimal
    qtd_trades: int

    def __lt__(self, other):
        """Ordena por PnL decrescente (maior primeiro)."""
        return self.pnl > other.pnl


@dataclass(frozen=True)
class ResumoPnL:
    """
    Resumo de PnL do portfolio.

    Attributes:
        pnl_total: PnL total realizado
        pnl_realizado: PnL já realizado
        pnl_nao_realizado: PnL de posições abertas
        qtd_operacoes: Quantidade de operações
    """

    pnl_total: Decimal
    pnl_realizado: Decimal
    pnl_nao_realizado: Decimal
    qtd_operacoes: int


@dataclass(frozen=True)
class RelatorioPerformance:
    """
    Relatório completo de performance do portfolio.

    Attributes:
        data: Data do relatório
        patrimonio_total: Patrimônio total
        metricas_risco: Métricas de risco (CalculadorDeRisco)
        ranking: Ranking de ativos por PnL
        resumo_pnl: Resumo de PnL
    """

    data: date
    patrimonio_total: Decimal
    metricas_risco: MetricasRisco
    ranking: list[RankingItem]
    resumo_pnl: ResumoPnL

    def to_dict(self) -> dict:
        """Converte para dict serializável."""
        return {
            "data": self.data.isoformat(),
            "patrimonio_total": float(self.patrimonio_total),
            "metricas_risco": self.metricas_risco.to_dict(),
            "ranking": [
                {"ticker": r.ticker, "pnl": float(r.pnl), "qtd_trades": r.qtd_trades}
                for r in self.ranking
            ],
            "resumo_pnl": {
                "pnl_total": float(self.resumo_pnl.pnl_total),
                "pnl_realizado": float(self.resumo_pnl.pnl_realizado),
                "pnl_nao_realizado": float(self.resumo_pnl.pnl_nao_realizado),
                "qtd_operacoes": self.resumo_pnl.qtd_operacoes,
            },
        }


# Protocol para calculador de risco injetável
class CalculadorRiscoProtocol(Protocol):
    """Protocol para calculador de risco."""

    def calcular(
        self, portfolio: PortfolioView, pico_historico: Decimal | None = None
    ) -> MetricasRisco:
        """Calcula métricas de risco."""
        ...


class GeradorDeRelatorio:
    """
    Serviço de domínio para gerar relatórios de performance.

    Relatórios disponíveis:
    - Performance por período (diário/semanal/mensal)
    - Ranking de ganhadores/perdedores
    - Resumo de PnL
    - Análise de risco (integrado com CalculadorDeRisco)

    Uso:
        gerador = GeradorDeRelatorio()
        relatorio = gerador.gerar_performance(portfolio)
    """

    def __init__(self, calculador_risco: CalculadorRiscoProtocol | None = None):
        """
        Inicializa gerador com dependências.

        Args:
            calculador_risco: Calculador de risco (opcional)
        """
        self._calculador_risco = calculador_risco or CalculadorDeRisco()

    def gerar_performance(
        self,
        portfolio: PortfolioView,
        data: date | None = None,
    ) -> RelatorioPerformance:
        """
        Gera relatório completo de performance.

        Args:
            portfolio: PortfolioView com posições
            data: Data do relatório (hoje se None)

        Returns:
            RelatorioPerformance com todos os dados
        """
        if data is None:
            data = date.today()

        # 1. Calcular patrimônio total
        patrimonio_total = self._calcular_patrimonio_total(portfolio)

        # 2. Calcular métricas de risco
        metricas_risco = self._calculador_risco.calcular(portfolio)

        # 3. Calcular ranking (PnL por ativo)
        ranking = self._calcular_ranking_por_pnl(portfolio)

        # 4. Calcular resumo de PnL
        resumo_pnl = self._calcular_resumo_pnl(portfolio)

        return RelatorioPerformance(
            data=data,
            patrimonio_total=patrimonio_total,
            metricas_risco=metricas_risco,
            ranking=ranking,
            resumo_pnl=resumo_pnl,
        )

    def _calcular_patrimonio_total(self, portfolio: PortfolioView) -> Decimal:
        """Calcula patrimônio total (posições + cash)."""
        total = Decimal("0")

        # Soma posições
        for posicao in portfolio.positions:
            total += posicao.market_value.amount

        # Adiciona cash
        if portfolio.cash is not None:
            total += portfolio.cash.amount

        return total

    def _calcular_ranking_por_pnl(
        self, portfolio: PortfolioView
    ) -> list[RankingItem]:
        """
        Calcula ranking de ativos por PnL.

        Returns:
            Lista de RankingItem ordenada por PnL decrescente
        """
        ranking = []

        for posicao in portfolio.positions:
            if posicao.pnl is not None:
                ranking.append(
                    RankingItem(
                        ticker=posicao.ticker,
                        pnl=posicao.pnl.amount,
                        qtd_trades=0,  # TODO: obter do histórico
                    )
                )

        # Ordenar por PnL decrescente
        # __lt__ já ordena decrescente, não usar reverse=True
        ranking.sort()
        return ranking

    def _calcular_resumo_pnl(self, portfolio: PortfolioView) -> ResumoPnL:
        """
        Calcula resumo de PnL do portfolio.

        Returns:
            ResumoPnL com totais
        """
        pnl_realizado = Decimal("0")  # TODO: obter do histórico
        pnl_nao_realizado = Decimal("0")

        # Calcular PnL não realizado das posições
        for posicao in portfolio.positions:
            if posicao.pnl is not None:
                pnl_nao_realizado += posicao.pnl.amount

        pnl_total = pnl_realizado + pnl_nao_realizado

        return ResumoPnL(
            pnl_total=pnl_total,
            pnl_realizado=pnl_realizado,
            pnl_nao_realizado=pnl_nao_realizado,
            qtd_operacoes=0,  # TODO: obter do histórico
        )

    def _calcular_ranking(
        self, ativos: list, top_n: int | None = None
    ) -> list[RankingItem]:
        """
        Calcula ranking a partir de lista de ativos.

        Args:
            ativos: Lista de ativos com performance
            top_n: Limitar a top N (opcional)

        Returns:
            Lista de RankingItem ordenada
        """
        ranking = sorted(ativos, key=lambda x: x.pnl, reverse=True)

        if top_n is not None:
            ranking = ranking[:top_n]

        return ranking


__all__ = [
    "GeradorDeRelatorio",
    "RelatorioPerformance",
    "RankingItem",
    "ResumoPnL",
]
