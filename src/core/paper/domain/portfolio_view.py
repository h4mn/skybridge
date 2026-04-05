"""
PortfolioView e PositionView - Views de portfolio multi-moeda.

Este módulo define value objects para representar visões consolidadas
do portfolio em múltiplas moedas.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from src.core.paper.domain.currency import Currency
from src.core.paper.domain.money import Money
from src.core.paper.domain.quantity import Quantity, AssetType
from src.core.paper.ports.currency_converter_port import CurrencyConverterPort


@dataclass(frozen=True)
class PositionView:
    """
    Visão de uma posição com valor marcado a mercado.

    Attributes:
        ticker: Código do ativo (ex: "PETR4.SA", "BTC-USD").
        quantity: Quantidade detida.
        market_price: Preço atual de mercado por unidade.
        cost_basis: Custo médio por unidade (opcional).

    Properties calculadas:
        market_value: quantity.value * market_price
        pnl: Lucro/prejuízo ((market_price - cost_basis) * quantity.value)

    Example:
        >>> pos = PositionView(
        ...     ticker="PETR4.SA",
        ...     quantity=Quantity(Decimal("100"), ...),
        ...     market_price=Money(Decimal("35.50"), Currency.BRL),
        ... )
        >>> pos.market_value.amount
        Decimal('3550.00')
    """

    ticker: str
    quantity: Quantity
    market_price: Money
    cost_basis: Optional[Money] = None

    @property
    def market_value(self) -> Money:
        """Valor de mercado: quantity.value * market_price."""
        return self.market_price * self.quantity.value

    @property
    def pnl(self) -> Optional[Money]:
        """Lucro/prejuízo: (market_price - cost_basis) * quantity.value."""
        if self.cost_basis is None:
            return None
        # (35.50 - 30.00) * 100 = 550.00
        diff = self.market_price - self.cost_basis
        return diff * self.quantity.value


@dataclass
class PortfolioView:
    """
    Visão consolidada do portfolio em múltiplas moedas.

    Attributes:
        positions: Lista de posições.
        base_currency: Moeda base para consolidação.
        cash: Saldo em caixa (opcional).

    Example:
        >>> portfolio = PortfolioView(
        ...     positions=[
        ...         PositionView(ticker="BTC-USD", ..., market_price=Money(Decimal("85000"), Currency.USD)),
        ...         PositionView(ticker="PETR4.SA", ..., market_price=Money(Decimal("35.50"), Currency.BRL)),
        ...     ],
        ...     base_currency=Currency.BRL,
        ... )
        >>> totals = portfolio.total_by_currency()
        >>> totals[Currency.USD].amount
        Decimal('42500.00')
    """

    positions: list[PositionView]
    base_currency: Currency
    cash: Optional[Money] = None

    def total_by_currency(self) -> dict[Currency, Money]:
        """
        Soma market_values por moeda.

        Returns:
            Dict mapeando Currency para total em Money.
        """
        totals: dict[Currency, Money] = {}

        # Adiciona cash se presente
        if self.cash is not None:
            totals[self.cash.currency] = self.cash

        # Soma posições por moeda
        for position in self.positions:
            currency = position.market_price.currency
            mv = position.market_value

            if currency in totals:
                totals[currency] = totals[currency] + mv
            else:
                totals[currency] = mv

        return totals

    async def total_converted(
        self, converter: CurrencyConverterPort, target: Currency
    ) -> Money:
        """
        Converte todas posições para moeda alvo e soma.

        Args:
            converter: Adapter para conversão de moedas.
            target: Moeda alvo para consolidação.

        Returns:
            Money com total convertido para moeda alvo.
        """
        total = Money(Decimal("0"), target)

        for position in self.positions:
            mv = position.market_value
            converted = await converter.convert(mv, target)
            total = total + converted

        # Adiciona cash convertido
        if self.cash is not None:
            converted_cash = await converter.convert(self.cash, target)
            total = total + converted_cash

        return total
