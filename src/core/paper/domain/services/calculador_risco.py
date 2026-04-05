"""
Calculador de Risco - Serviço de Domínio.

Calcula métricas de risco para o portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from ..portfolio_view import PortfolioView
from ..currency import Currency
from ..money import Money


@dataclass(frozen=True)
class MetricasRisco:
    """
    Métricas de risco calculadas do portfolio.

    Attributes:
        exposicao_total: Valor total exposto em posições
        var_95: Value at Risk (95% confiança) - perda máxima esperada
        drawdown: Queda desde o pico histórico (0 a 1)
        concentracao: Dict mapeando ticker -> % do portfolio (0 a 1)
    """

    exposicao_total: Decimal
    var_95: Decimal
    drawdown: Decimal
    concentracao: dict[str, Decimal]

    def to_dict(self) -> dict:
        """Converte para dict serializável."""
        return {
            "exposicao_total": float(self.exposicao_total),
            "var_95": float(self.var_95),
            "drawdown": float(self.drawdown),
            "concentracao": {k: float(v) for k, v in self.concentracao.items()},
        }


class CalculadorDeRisco:
    """
    Serviço de domínio para calcular métricas de risco.

    Métricas calculadas:
    - VaR (Value at Risk 95%): Perda máxima esperada com 95% confiança
    - Exposição total: Valor total em posições abertas
    - Concentração: % do portfolio por ativo
    - Drawdown: Queda desde o pico histórico

    Implementação simplificada (pode ser expandida):
    - VaR usa método paramétrico simplificado (5% da exposição)
    - Não considera correlação entre ativos
    - Drawdown requer pico histórico externo

    Uso:
        calculador = CalculadorDeRisco()
        metricas = calculador.calcular(portfolio)
        print(f"VaR 95%: {metricas.var_95}")
    """

    # Parâmetros para VaR simplificado
    VAR_PERCENTUAL = Decimal("0.05")  # 5% da exposição como risco

    def calcular(
        self,
        portfolio: PortfolioView,
        pico_historico: Decimal | None = None,
    ) -> MetricasRisco:
        """
        Calcula todas as métricas de risco.

        Args:
            portfolio: PortfolioView com posições
            pico_historico: Pico histórico do portfolio (opcional, para drawdown)

        Returns:
            MetricasRisco com todas as métricas calculadas
        """
        # 1. Calcular exposição total
        exposicao_total = self._calcular_exposicao_total(portfolio)

        # 2. Calcular VaR 95% (simplificado)
        var_95 = self._calcular_var_95(exposicao_total)

        # 3. Calcular concentração por ativo
        concentracao = self._calcular_concentracao(portfolio, exposicao_total)

        # 4. Calcular drawdown
        drawdown = self._calcular_drawdown(portfolio, pico_historico)

        return MetricasRisco(
            exposicao_total=exposicao_total,
            var_95=var_95,
            drawdown=drawdown,
            concentracao=concentracao,
        )

    def _calcular_exposicao_total(self, portfolio: PortfolioView) -> Decimal:
        """
        Calcula exposição total (soma dos market_values).

        Nota: Para multi-moeda, precisaria converter para moeda base.
        Esta implementação simplificada soma tudo.
        """
        total = Decimal("0")

        for posicao in portfolio.positions:
            # market_value já é Money, pegamos o amount
            total += posicao.market_value.amount

        return total

    def _calcular_var_95(self, exposicao_total: Decimal) -> Decimal:
        """
        Calcula VaR 95% (método simplificado).

        NOTA: Esta é uma implementação simplificada.
        VaR real requer:
        - Distribuição de retornos históricos
        - Método paramétrico, histórico ou Monte Carlo
        - Correlação entre ativos

        Simplificação: 5% da exposição como risco máximo
        """
        return exposicao_total * self.VAR_PERCENTUAL

    def _calcular_concentracao(
        self, portfolio: PortfolioView, exposicao_total: Decimal
    ) -> dict[str, Decimal]:
        """
        Calcula concentração de cada ativo (% do portfolio).

        Returns:
            Dict mapeando ticker -> % (0 a 1)
        """
        if exposicao_total == 0:
            return {}

        concentracao = {}

        for posicao in portfolio.positions:
            valor = posicao.market_value.amount
            pct = valor / exposicao_total
            concentracao[posicao.ticker] = pct

        return concentracao

    def _calcular_drawdown(
        self, portfolio: PortfolioView, pico_historico: Decimal | None
    ) -> Decimal:
        """
        Calcula drawdown (queda desde o pico).

        Drawdown = (Pico - Valor Atual) / Pico

        Args:
            portfolio: Portfolio atual
            pico_historico: Pico histórico do portfolio (opcional)

        Returns:
            Drawdown como decimal (0 a 1), ou 0 se não há pico
        """
        if pico_historico is None or pico_historico == 0:
            return Decimal("0")

        valor_atual = self._calcular_exposicao_total(portfolio)

        if valor_atual >= pico_historico:
            return Decimal("0")

        drawdown = (pico_historico - valor_atual) / pico_historico
        return max(drawdown, Decimal("0"))


__all__ = [
    "CalculadorDeRisco",
    "MetricasRisco",
]
