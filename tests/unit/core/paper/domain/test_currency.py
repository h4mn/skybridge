"""
Testes unitários para Currency enum.

DOC: src/core/paper/domain/currency.py - Currency enum com propriedades is_fiat e is_crypto.

Cenários:
- Moedas fiat (BRL, USD, EUR, GBP) devem ter is_fiat=True
- Moedas crypto (BTC, ETH) devem ter is_crypto=True
- Moedas fiat devem ter is_crypto=False
- Moedas crypto devem ter is_fiat=False
"""
import pytest
from decimal import Decimal

from src.core.paper.domain.currency import Currency


class TestCurrencyEnum:
    """Testes para o enum Currency."""

    def test_currency_enum_contem_moedas_fiat(self):
        """Verifica que moedas fiat estão presentes."""
        assert Currency.BRL.value == "BRL"
        assert Currency.USD.value == "USD"
        assert Currency.EUR.value == "EUR"
        assert Currency.GBP.value == "GBP"

    def test_currency_enum_contem_moedas_crypto(self):
        """Verifica que moedas crypto estão presentes."""
        assert Currency.BTC.value == "BTC"
        assert Currency.ETH.value == "ETH"

    def test_is_fiat_retorna_true_para_moedas_fiat(self):
        """Moedas fiat devem ter is_fiat=True."""
        assert Currency.BRL.is_fiat is True
        assert Currency.USD.is_fiat is True
        assert Currency.EUR.is_fiat is True
        assert Currency.GBP.is_fiat is True

    def test_is_fiat_retorna_false_para_moedas_crypto(self):
        """Moedas crypto devem ter is_fiat=False."""
        assert Currency.BTC.is_fiat is False
        assert Currency.ETH.is_fiat is False

    def test_is_crypto_retorna_true_para_moedas_crypto(self):
        """Moedas crypto devem ter is_crypto=True."""
        assert Currency.BTC.is_crypto is True
        assert Currency.ETH.is_crypto is True

    def test_is_crypto_retorna_false_para_moedas_fiat(self):
        """Moedas fiat devem ter is_crypto=False."""
        assert Currency.BRL.is_crypto is False
        assert Currency.USD.is_crypto is False
        assert Currency.EUR.is_crypto is False
        assert Currency.GBP.is_crypto is False

    def test_total_moedas_suportadas(self):
        """Verifica total de moedas suportadas."""
        moedas = list(Currency)
        assert len(moedas) == 6  # BRL, USD, EUR, GBP, BTC, ETH
