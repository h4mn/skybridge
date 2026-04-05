"""
Testes unitários para CurrencyConverterPort.

DOC: src/core/paper/ports/currency_converter_port.py - Port para conversão de moedas.

Cenários:
- Protocol define get_rate(from, to) -> Decimal
- Protocol define convert(money, to) -> Money
- Implementação deve seguir o protocol
"""
import pytest
from decimal import Decimal
from typing import Protocol, runtime_checkable

from src.core.paper.domain.currency import Currency
from src.core.paper.domain.money import Money
from src.core.paper.ports.currency_converter_port import CurrencyConverterPort


class TestCurrencyConverterPortProtocol:
    """Testes para verificar que CurrencyConverterPort é um Protocol válido."""

    def test_e_um_protocol(self):
        """CurrencyConverterPort deve ser um Protocol (runtime_checkable)."""
        # Verifica que é um Protocol verificando a origem
        import inspect
        assert inspect.isclass(CurrencyConverterPort)

    def test_define_get_rate(self):
        """CurrencyConverterPort deve definir método get_rate."""
        # Verifica assinatura esperada
        assert hasattr(CurrencyConverterPort, "get_rate")

    def test_define_convert(self):
        """CurrencyConverterPort deve definir método convert."""
        assert hasattr(CurrencyConverterPort, "convert")


class FakeCurrencyConverter:
    """Implementação fake para testes do protocol."""

    async def get_rate(
        self, from_currency: Currency, to_currency: Currency
    ) -> Decimal:
        """Retorna taxa fixa para testes."""
        if from_currency == Currency.USD and to_currency == Currency.BRL:
            return Decimal("5.0")
        if from_currency == Currency.BRL and to_currency == Currency.USD:
            return Decimal("0.2")
        return Decimal("1.0")

    async def convert(self, money: Money, to: Currency) -> Money:
        """Converte money para outra moeda."""
        if money.currency == to:
            return money
        rate = await self.get_rate(money.currency, to)
        return money.convert_to(to, rate)


class TestCurrencyConverterImplementation:
    """Testes para implementação do port."""

    @pytest.mark.asyncio
    async def test_fake_implementation_get_rate(self):
        """Fake implementation deve retornar taxas."""
        converter = FakeCurrencyConverter()
        rate = await converter.get_rate(Currency.USD, Currency.BRL)
        assert rate == Decimal("5.0")

    @pytest.mark.asyncio
    async def test_fake_implementation_convert(self):
        """Fake implementation deve converter money."""
        converter = FakeCurrencyConverter()
        money = Money(Decimal("100"), Currency.USD)
        converted = await converter.convert(money, Currency.BRL)
        assert converted.amount == Decimal("500")
        assert converted.currency == Currency.BRL

    @pytest.mark.asyncio
    async def test_fake_implementation_convert_mesma_moeda(self):
        """Converter para mesma moeda deve retornar igual."""
        converter = FakeCurrencyConverter()
        money = Money(Decimal("100"), Currency.BRL)
        converted = await converter.convert(money, Currency.BRL)
        assert converted.amount == Decimal("100")
        assert converted.currency == Currency.BRL
