# -*- coding: utf-8 -*-
"""
CashBook - Agregado para gerenciamento de múltiplas moedas.

Implementa o padrão CashBook inspirado no QuantConnect LEAN,
permitindo operações de paper trading com ativos em moedas diferentes.

Example:
    >>> cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("100000"))
    >>> cashbook.add(Currency.USD, Decimal("1000"), Decimal("5.7"))
    >>> cashbook.total_in_base_currency
    Decimal('105700')
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from src.core.paper.domain.currency import Currency


class InsufficientFundsError(Exception):
    """
    Erro lançado quando não há saldo suficiente em uma moeda.

    Attributes:
        currency: Moeda com saldo insuficiente.
        requested: Valor solicitado.
        available: Valor disponível.
    """

    def __init__(
        self,
        currency: Currency,
        requested: Decimal,
        available: Decimal,
    ):
        self.currency = currency
        self.requested = requested
        self.available = available
        super().__init__(
            f"Saldo insuficiente em {currency.value}: "
            f"solicitado {requested}, disponível {available}"
        )


@dataclass(frozen=True)
class CashEntry:
    """
    Entrada de caixa em uma moeda específica.

    Attributes:
        currency: Moeda da entrada.
        amount: Quantidade disponível.
        conversion_rate: Taxa de conversão para moeda base.

    Example:
        >>> entry = CashEntry(Currency.USD, Decimal("1000"), Decimal("5.7"))
        >>> entry.value_in_base_currency
        Decimal('5700')
    """

    currency: Currency
    amount: Decimal
    conversion_rate: Decimal

    @property
    def value_in_base_currency(self) -> Decimal:
        """
        Calcula o valor em moeda base.

        Returns:
            Valor convertido para moeda base.
            Retorna 0 se conversion_rate for 0 (moeda não cotada).
        """
        if self.conversion_rate == Decimal("0"):
            return Decimal("0")
        return self.amount * self.conversion_rate

    def __str__(self) -> str:
        """Formata entrada para exibição."""
        symbols = {
            Currency.BRL: "R$",
            Currency.USD: "$",
            Currency.EUR: "€",
            Currency.GBP: "£",
            Currency.BTC: "₿",
            Currency.ETH: "Ξ",
        }
        symbol = symbols.get(self.currency, self.currency.value)
        return f"{symbol} {self.amount:.2f} (taxa: {self.conversion_rate:.4f})"


@dataclass
class CashBook:
    """
    Livro de caixa multi-moeda.

    Mantém saldos em múltiplas moedas com conversão para uma moeda base.

    Attributes:
        base_currency: Moeda base para consolidação.
        entries: Dicionário de moedas para entradas de caixa.

    Example:
        >>> cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("100000"))
        >>> cashbook.add(Currency.USD, Decimal("1000"), Decimal("5.7"))
        >>> cashbook.total_in_base_currency
        Decimal('105700')
    """

    base_currency: Currency
    _entries: dict[Currency, CashEntry] = field(default_factory=dict)

    # ═══════════════════════════════════════════════════════════════════════
    # Properties
    # ═══════════════════════════════════════════════════════════════════════

    @property
    def total_in_base_currency(self) -> Decimal:
        """
        Soma todos os valores convertidos para moeda base.

        Returns:
            Total consolidado em moeda base.
        """
        return sum(
            entry.value_in_base_currency for entry in self._entries.values()
        )

    @property
    def entries(self) -> dict[Currency, CashEntry]:
        """Retorna cópia do dicionário de entradas."""
        return self._entries.copy()

    # ═══════════════════════════════════════════════════════════════════════
    # Query Methods
    # ═══════════════════════════════════════════════════════════════════════

    def get(self, currency: Currency) -> CashEntry:
        """
        Retorna entrada de uma moeda.

        Args:
            currency: Moeda desejada.

        Returns:
            CashEntry com amount=0 e rate=0 se moeda não existir.
        """
        if currency in self._entries:
            return self._entries[currency]
        return CashEntry(currency, Decimal("0"), Decimal("0"))

    def has_sufficient_funds(self, currency: Currency, amount: Decimal) -> bool:
        """
        Verifica se há saldo suficiente em uma moeda.

        Args:
            currency: Moeda a verificar.
            amount: Quantidade necessária.

        Returns:
            True se houver saldo suficiente.
        """
        entry = self.get(currency)
        return entry.amount >= amount

    # ═══════════════════════════════════════════════════════════════════════
    # Command Methods
    # ═══════════════════════════════════════════════════════════════════════

    def add(
        self,
        currency: Currency,
        amount: Decimal,
        conversion_rate: Decimal,
    ) -> None:
        """
        Adiciona valor a uma moeda.

        Se a moeda já existir, soma ao amount existente e atualiza a taxa.
        Se não existir, cria nova entrada.

        Args:
            currency: Moeda a adicionar.
            amount: Quantidade a adicionar.
            conversion_rate: Taxa de conversão para moeda base.
        """
        if currency in self._entries:
            existing = self._entries[currency]
            new_amount = existing.amount + amount
            self._entries[currency] = CashEntry(currency, new_amount, conversion_rate)
        else:
            self._entries[currency] = CashEntry(currency, amount, conversion_rate)

    def subtract(self, currency: Currency, amount: Decimal) -> None:
        """
        Subtrai valor de uma moeda.

        Args:
            currency: Moeda a subtrair.
            amount: Quantidade a subtrair.

        Raises:
            InsufficientFundsError: Se não houver saldo suficiente.
        """
        entry = self.get(currency)

        if entry.amount < amount:
            raise InsufficientFundsError(currency, amount, entry.amount)

        new_amount = entry.amount - amount
        if new_amount == Decimal("0"):
            # Remove entrada se ficar zerada
            del self._entries[currency]
        else:
            self._entries[currency] = CashEntry(
                currency, new_amount, entry.conversion_rate
            )

    def set_rate(self, currency: Currency, conversion_rate: Decimal) -> None:
        """
        Atualiza taxa de conversão de uma moeda.

        Args:
            currency: Moeda a atualizar.
            conversion_rate: Nova taxa de conversão.
        """
        if currency in self._entries:
            entry = self._entries[currency]
            self._entries[currency] = CashEntry(
                currency, entry.amount, conversion_rate
            )

    # ═══════════════════════════════════════════════════════════════════════
    # Conversion
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def convert(
        amount: Decimal,
        from_currency: Currency,
        to_currency: Currency,
        rate: Decimal,
    ) -> Decimal:
        """
        Converte valor entre moedas usando taxa fornecida.

        Args:
            amount: Valor a converter.
            from_currency: Moeda de origem.
            to_currency: Moeda de destino.
            rate: Taxa de câmbio.

        Returns:
            Valor convertido (ou original se mesma moeda).
        """
        if from_currency == to_currency:
            return amount
        return amount * rate

    # ═══════════════════════════════════════════════════════════════════════
    # Serialization
    # ═══════════════════════════════════════════════════════════════════════

    def to_dict(self) -> dict:
        """
        Serializa CashBook para dicionário.

        Returns:
            Dicionário com base_currency e entries.
        """
        entries_dict = {}
        for currency, entry in self._entries.items():
            entries_dict[currency.value] = {
                "amount": str(entry.amount),
                "conversion_rate": str(entry.conversion_rate),
            }

        return {
            "base_currency": self.base_currency.value,
            "entries": entries_dict,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CashBook":
        """
        Desserializa CashBook de dicionário.

        Args:
            data: Dicionário com base_currency e entries.

        Returns:
            Instância de CashBook.
        """
        # Fallback para base_currency (compatibilidade com estados legados)
        base_currency_str = data.get("base_currency", "BRL")
        base_currency = Currency(base_currency_str)
        cashbook = cls(base_currency=base_currency)

        entries_data = data.get("entries", {})
        for currency_str, entry_data in entries_data.items():
            currency = Currency(currency_str)
            amount = Decimal(str(entry_data["amount"]))
            rate = Decimal(str(entry_data.get("conversion_rate", "1")))
            cashbook._entries[currency] = CashEntry(currency, amount, rate)

        return cashbook

    # ═══════════════════════════════════════════════════════════════════════
    # Factory Methods
    # ═══════════════════════════════════════════════════════════════════════

    @classmethod
    def from_single_currency(
        cls,
        base_currency: Currency,
        amount: Decimal,
    ) -> "CashBook":
        """
        Cria CashBook com saldo em uma única moeda.

        Args:
            base_currency: Moeda base e única moeda do cashbook.
            amount: Saldo inicial.

        Returns:
            CashBook com uma entrada (taxa = 1.0).

        Example:
            >>> cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("100000"))
            >>> cashbook.total_in_base_currency
            Decimal('100000')
        """
        cashbook = cls(base_currency=base_currency)
        cashbook._entries[base_currency] = CashEntry(
            base_currency, amount, Decimal("1")
        )
        return cashbook

    # ═══════════════════════════════════════════════════════════════════════
    # Representation
    # ═══════════════════════════════════════════════════════════════════════

    def __str__(self) -> str:
        """Formata cashbook para exibição."""
        lines = [f"CashBook (base: {self.base_currency.value})"]
        lines.append("-" * 40)

        for currency, entry in sorted(self._entries.items(), key=lambda x: x[0].value):
            lines.append(f"  {entry}")

        lines.append("-" * 40)
        lines.append(f"  Total: {self.total_in_base_currency:.2f} {self.base_currency.value}")

        return "\n".join(lines)
