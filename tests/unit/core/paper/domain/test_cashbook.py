# -*- coding: utf-8 -*-
"""
Testes unitários para CashBook e CashEntry.

Cobre todos os requisitos da spec:
- CashEntry: value_in_base_currency, formatação
- CashBook: add, subtract, get, total, serialização
- InsufficientFundsError: mensagem de erro
"""
import pytest
from decimal import Decimal

from src.core.paper.domain.currency import Currency
from src.core.paper.domain.cashbook import (
    CashEntry,
    CashBook,
    InsufficientFundsError,
)


class TestCashEntry:
    """Testes para CashEntry."""

    def test_criar_cash_entry(self):
        """Criar entrada com valores válidos."""
        entry = CashEntry(Currency.USD, Decimal("1000"), Decimal("5.7"))

        assert entry.currency == Currency.USD
        assert entry.amount == Decimal("1000")
        assert entry.conversion_rate == Decimal("5.7")

    def test_value_in_base_currency(self):
        """Calcular valor em moeda base."""
        entry = CashEntry(Currency.USD, Decimal("1000"), Decimal("5.7"))

        assert entry.value_in_base_currency == Decimal("5700")

    def test_value_in_base_currency_zero_rate(self):
        """Taxa zero retorna valor zero (moeda não cotada)."""
        entry = CashEntry(Currency.EUR, Decimal("1000"), Decimal("0"))

        assert entry.value_in_base_currency == Decimal("0")

    def test_frozen_dataclass(self):
        """CashEntry é imutável."""
        entry = CashEntry(Currency.BRL, Decimal("100"), Decimal("1"))

        with pytest.raises(AttributeError):
            entry.amount = Decimal("200")

    def test_str_format(self):
        """Formatação de exibição."""
        entry = CashEntry(Currency.USD, Decimal("1000"), Decimal("5.7"))

        result = str(entry)

        assert "$" in result
        assert "1000" in result


class TestCashBook:
    """Testes para CashBook."""

    def test_criar_cashbook_vazio(self):
        """Criar cashbook sem entradas."""
        cashbook = CashBook(base_currency=Currency.BRL)

        assert cashbook.base_currency == Currency.BRL
        assert cashbook.total_in_base_currency == Decimal("0")

    def test_from_single_currency(self):
        """Factory cria cashbook com moeda única."""
        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("100000"))

        assert cashbook.base_currency == Currency.BRL
        assert cashbook.total_in_base_currency == Decimal("100000")

        brl_entry = cashbook.get(Currency.BRL)
        assert brl_entry.amount == Decimal("100000")
        assert brl_entry.conversion_rate == Decimal("1")

    def test_add_nova_moeda(self):
        """Adicionar entrada em moeda nova."""
        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("50000"))
        cashbook.add(Currency.USD, Decimal("1000"), Decimal("5.7"))

        usd_entry = cashbook.get(Currency.USD)
        assert usd_entry.amount == Decimal("1000")
        assert usd_entry.conversion_rate == Decimal("5.7")

    def test_add_moeda_existente(self):
        """Adicionar a moeda existente soma ao saldo."""
        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("50000"))
        cashbook.add(Currency.USD, Decimal("1000"), Decimal("5.7"))
        cashbook.add(Currency.USD, Decimal("500"), Decimal("5.8"))

        usd_entry = cashbook.get(Currency.USD)
        assert usd_entry.amount == Decimal("1500")
        assert usd_entry.conversion_rate == Decimal("5.8")  # Taxa atualizada

    def test_subtract_com_saldo(self):
        """Subtrair com saldo suficiente."""
        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("1000"))
        cashbook.subtract(Currency.BRL, Decimal("300"))

        assert cashbook.get(Currency.BRL).amount == Decimal("700")

    def test_subtract_saldo_insuficiente(self):
        """Subtrair com saldo insuficiente lança erro."""
        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("100"))

        with pytest.raises(InsufficientFundsError) as exc_info:
            cashbook.subtract(Currency.BRL, Decimal("200"))

        assert exc_info.value.currency == Currency.BRL
        assert exc_info.value.requested == Decimal("200")
        assert exc_info.value.available == Decimal("100")

    def test_subtract_moeda_inexistente(self):
        """Subtrair de moeda inexistente lança erro."""
        cashbook = CashBook(base_currency=Currency.BRL)

        with pytest.raises(InsufficientFundsError):
            cashbook.subtract(Currency.USD, Decimal("100"))

    def test_subtract_zerando_remove_entrada(self):
        """Subtrair todo o saldo remove a entrada."""
        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("100"))
        cashbook.subtract(Currency.BRL, Decimal("100"))

        # Moeda base sempre deve existir, mas com amount 0
        assert Currency.BRL not in cashbook._entries

    def test_total_in_base_currency_multiplas_moedas(self):
        """Total soma todas as moedas convertidas."""
        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("50000"))
        cashbook.add(Currency.USD, Decimal("1000"), Decimal("5.7"))

        # 50000 BRL + 1000 USD * 5.7 = 50000 + 5700 = 55700
        assert cashbook.total_in_base_currency == Decimal("55700")

    def test_get_moeda_inexistente(self):
        """Get de moeda inexistente retorna entrada vazia."""
        cashbook = CashBook(base_currency=Currency.BRL)

        entry = cashbook.get(Currency.EUR)

        assert entry.amount == Decimal("0")
        assert entry.conversion_rate == Decimal("0")

    def test_has_sufficient_funds_true(self):
        """Verificar saldo suficiente retorna True."""
        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("1000"))

        assert cashbook.has_sufficient_funds(Currency.BRL, Decimal("500")) is True

    def test_has_sufficient_funds_false(self):
        """Verificar saldo insuficiente retorna False."""
        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("100"))

        assert cashbook.has_sufficient_funds(Currency.BRL, Decimal("200")) is False

    def test_set_rate(self):
        """Atualizar taxa de conversão."""
        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("50000"))
        cashbook.add(Currency.USD, Decimal("1000"), Decimal("5.5"))
        cashbook.set_rate(Currency.USD, Decimal("5.8"))

        assert cashbook.get(Currency.USD).conversion_rate == Decimal("5.8")

    def test_convert_mesma_moeda(self):
        """Converter para mesma moeda retorna valor original."""
        result = CashBook.convert(
            Decimal("100"),
            Currency.BRL,
            Currency.BRL,
            Decimal("5.7"),
        )

        assert result == Decimal("100")

    def test_convert_moedas_diferentes(self):
        """Converter entre moedas usa taxa."""
        result = CashBook.convert(
            Decimal("100"),
            Currency.USD,
            Currency.BRL,
            Decimal("5.7"),
        )

        assert result == Decimal("570")


class TestCashBookSerialization:
    """Testes de serialização/desserialização."""

    def test_to_dict(self):
        """Serializar para dicionário."""
        cashbook = CashBook.from_single_currency(Currency.BRL, Decimal("50000"))
        cashbook.add(Currency.USD, Decimal("1000"), Decimal("5.7"))

        result = cashbook.to_dict()

        assert result["base_currency"] == "BRL"
        assert "BRL" in result["entries"]
        assert "USD" in result["entries"]
        assert result["entries"]["BRL"]["amount"] == "50000"
        assert result["entries"]["USD"]["amount"] == "1000"

    def test_from_dict(self):
        """Desserializar de dicionário."""
        data = {
            "base_currency": "BRL",
            "entries": {
                "BRL": {"amount": "50000", "conversion_rate": "1"},
                "USD": {"amount": "1000", "conversion_rate": "5.7"},
            },
        }

        cashbook = CashBook.from_dict(data)

        assert cashbook.base_currency == Currency.BRL
        assert cashbook.get(Currency.BRL).amount == Decimal("50000")
        assert cashbook.get(Currency.USD).amount == Decimal("1000")

    def test_roundtrip(self):
        """Serializar e desserializar preserva valores."""
        original = CashBook.from_single_currency(Currency.BRL, Decimal("100000"))
        original.add(Currency.USD, Decimal("5000"), Decimal("5.7"))

        data = original.to_dict()
        restored = CashBook.from_dict(data)

        assert restored.base_currency == original.base_currency
        assert restored.total_in_base_currency == original.total_in_base_currency
        assert restored.get(Currency.BRL).amount == original.get(Currency.BRL).amount
        assert restored.get(Currency.USD).amount == original.get(Currency.USD).amount


class TestInsufficientFundsError:
    """Testes para InsufficientFundsError."""

    def test_mensagem_de_erro(self):
        """Mensagem contém informações do erro."""
        error = InsufficientFundsError(
            currency=Currency.USD,
            requested=Decimal("200"),
            available=Decimal("100"),
        )

        message = str(error)

        assert "USD" in message
        assert "200" in message
        assert "100" in message

    def test_atributos(self):
        """Erro expõe atributos."""
        error = InsufficientFundsError(
            currency=Currency.BRL,
            requested=Decimal("500"),
            available=Decimal("300"),
        )

        assert error.currency == Currency.BRL
        assert error.requested == Decimal("500")
        assert error.available == Decimal("300")
