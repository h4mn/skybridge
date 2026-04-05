"""
Money Value Object para sistema multi-moeda.

Representa um valor monetário com moeda específica, suportando
operações matemáticas e conversão entre moedas.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Union

from src.core.paper.domain.currency import Currency


class CurrencyMismatchError(Exception):
    """Erro lançado ao tentar operar com moedas diferentes."""

    def __init__(self, from_currency: Currency, to_currency: Currency):
        self.from_currency = from_currency
        self.to_currency = to_currency
        super().__init__(
            f"Cannot operate on different currencies: "
            f"{from_currency.value} and {to_currency.value}"
        )


# Símbolos de moeda para formatação
CURRENCY_SYMBOLS = {
    Currency.BRL: "R$",
    Currency.USD: "$",
    Currency.EUR: "€",
    Currency.GBP: "£",
    Currency.BTC: "₿",
    Currency.ETH: "Ξ",
}

# Separadores decimais por moeda (True = vírgula decimal, ponto milhares)
DECIMAL_FORMAT_EUROPEAN = {
    Currency.BRL: True,  # 1.234,56
    Currency.USD: False,  # 1,234.56
    Currency.EUR: True,  # 1.234,56
    Currency.GBP: False,  # 1,234.56
    Currency.BTC: False,  # 0.12345678
    Currency.ETH: False,  # 1.50000000
}


@dataclass(frozen=True)
class Money:
    """
    Value Object para valor monetário com moeda.

    Attributes:
        amount: Valor monetário como Decimal para precisão.
        currency: Moeda do valor.

    Example:
        >>> valor = Money(Decimal("100.50"), Currency.BRL)
        >>> valor.format()
        'R$ 100,50'
    """

    amount: Decimal
    currency: Currency

    def __add__(self, other: "Money") -> "Money":
        """Soma dois valores na mesma moeda."""
        if self.currency != other.currency:
            raise CurrencyMismatchError(self.currency, other.currency)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        """Subtrai dois valores na mesma moeda."""
        if self.currency != other.currency:
            raise CurrencyMismatchError(self.currency, other.currency)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, scalar: Union[Decimal, int, float]) -> "Money":
        """Multiplica por escalar."""
        if isinstance(scalar, (int, float)):
            scalar = Decimal(str(scalar))
        return Money(self.amount * scalar, self.currency)

    def __rmul__(self, scalar: Union[Decimal, int, float]) -> "Money":
        """Multiplicação comutativa (escalar * money)."""
        return self.__mul__(scalar)

    def convert_to(self, target: Currency, rate: Decimal) -> "Money":
        """
        Converte para outra moeda usando taxa fornecida.

        Args:
            target: Moeda de destino.
            rate: Taxa de câmbio (quanto vale 1 unidade da moeda origem em destino).

        Returns:
            Novo Money na moeda de destino.

        Example:
            >>> usd = Money(Decimal("100"), Currency.USD)
            >>> brl = usd.convert_to(Currency.BRL, Decimal("5.0"))
            >>> brl.amount
            Decimal('500')
        """
        if self.currency == target:
            return self
        return Money(self.amount * rate, target)

    def format(self) -> str:
        """
        Formata valor para exibição com símbolo de moeda.

        Returns:
            String formatada com símbolo e valor.

        Example:
            >>> Money(Decimal("1234.56"), Currency.BRL).format()
            'R$ 1.234,56'
        """
        symbol = CURRENCY_SYMBOLS.get(self.currency, self.currency.value)
        use_european = DECIMAL_FORMAT_EUROPEAN.get(self.currency, False)

        # Formata com 2 casas decimais para fiat, 8 para crypto
        if self.currency.is_crypto:
            formatted_amount = f"{self.amount:.8f}".rstrip("0").rstrip(".")
        else:
            formatted_amount = f"{self.amount:.2f}"

        if use_european:
            # Formato europeu: 1.234,56
            parts = formatted_amount.split(".")
            if len(parts) == 2:
                int_part = parts[0]
                dec_part = parts[1]
                # Adiciona separador de milhares
                int_with_thousands = ""
                for i, digit in enumerate(reversed(int_part)):
                    if i > 0 and i % 3 == 0:
                        int_with_thousands = "." + int_with_thousands
                    int_with_thousands = digit + int_with_thousands
                formatted_amount = f"{int_with_thousands},{dec_part}"
        else:
            # Formato americano: 1,234.56
            parts = formatted_amount.split(".")
            if len(parts) == 2:
                int_part = parts[0]
                dec_part = parts[1]
                # Adiciona separador de milhares
                int_with_thousands = ""
                for i, digit in enumerate(reversed(int_part)):
                    if i > 0 and i % 3 == 0:
                        int_with_thousands = "," + int_with_thousands
                    int_with_thousands = digit + int_with_thousands
                formatted_amount = f"{int_with_thousands}.{dec_part}"

        return f"{symbol} {formatted_amount}"
