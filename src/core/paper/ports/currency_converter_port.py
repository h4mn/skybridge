"""
CurrencyConverterPort - Port para conversão de moedas.

Este port define a interface para conversão de moedas, seguindo o padrão
Ports & Adapters (Hexagonal Architecture).
"""
from decimal import Decimal
from typing import Protocol, runtime_checkable

from src.core.paper.domain.currency import Currency
from src.core.paper.domain.money import Money


@runtime_checkable
class CurrencyConverterPort(Protocol):
    """
    Protocol para conversão de moedas.

    Implementações devem fornecer taxas de câmbio atualizadas
    e conversão entre moedas.

    Example:
        >>> class YahooCurrencyAdapter(CurrencyConverterPort):
        ...     async def get_rate(self, from_curr, to_curr) -> Decimal:
        ...         # Busca taxa do Yahoo Finance
        ...         pass
    """

    async def get_rate(
        self, from_currency: Currency, to_currency: Currency
    ) -> Decimal:
        """
        Retorna taxa de câmbio atual.

        Args:
            from_currency: Moeda de origem.
            to_currency: Moeda de destino.

        Returns:
            Taxa de câmbio (quanto vale 1 unidade de from em to).

        Raises:
            CurrencyRateNotFoundError: Se não encontrar taxa para o par.

        Example:
            >>> rate = await converter.get_rate(Currency.USD, Currency.BRL)
            >>> rate
            Decimal('5.0')  # 1 USD = 5 BRL
        """
        ...

    async def convert(self, money: Money, to: Currency) -> Money:
        """
        Converte Money para outra moeda.

        Args:
            money: Valor a converter.
            to: Moeda de destino.

        Returns:
            Novo Money na moeda de destino.

        Example:
            >>> usd = Money(Decimal("100"), Currency.USD)
            >>> brl = await converter.convert(usd, Currency.BRL)
            >>> brl.amount
            Decimal('500')
        """
        ...
