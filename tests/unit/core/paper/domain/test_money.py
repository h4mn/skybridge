"""
Testes unitários para Money Value Object.

DOC: src/core/paper/domain/money.py - Money VO com operações matemáticas e conversão.

Cenários:
- Criação com amount e currency
- Operações matemáticas (add, sub, mul)
- Erro ao operar moedas diferentes (CurrencyMismatchError)
- Conversão de moeda com taxa
- Formatação com símbolos de moeda
"""
import pytest
from decimal import Decimal

from src.core.paper.domain.currency import Currency
from src.core.paper.domain.money import Money, CurrencyMismatchError


class TestMoneyValueObject:
    """Testes para o Value Object Money."""

    # === Criação ===

    def test_cria_money_com_amount_e_currency(self):
        """Money deve ser criado com amount e currency."""
        money = Money(Decimal("100.50"), Currency.BRL)
        assert money.amount == Decimal("100.50")
        assert money.currency == Currency.BRL

    def test_money_e_immutavel(self):
        """Money deve ser frozen/immutable."""
        money = Money(Decimal("100"), Currency.BRL)
        with pytest.raises(AttributeError):
            money.amount = Decimal("200")

    # === Operações Matemáticas ===

    def test_soma_duas_moedas_iguais(self):
        """Soma de duas moedas iguais deve funcionar."""
        a = Money(Decimal("100"), Currency.BRL)
        b = Money(Decimal("50"), Currency.BRL)
        resultado = a + b
        assert resultado.amount == Decimal("150")
        assert resultado.currency == Currency.BRL

    def test_soma_moedas_diferentes_erro(self):
        """Soma de moedas diferentes deve lançar CurrencyMismatchError."""
        a = Money(Decimal("100"), Currency.BRL)
        b = Money(Decimal("50"), Currency.USD)
        with pytest.raises(CurrencyMismatchError) as exc_info:
            _ = a + b
        assert "BRL" in str(exc_info.value)
        assert "USD" in str(exc_info.value)

    def test_subtrai_duas_moedas_iguais(self):
        """Subtração de duas moedas iguais deve funcionar."""
        a = Money(Decimal("100"), Currency.BRL)
        b = Money(Decimal("30"), Currency.BRL)
        resultado = a - b
        assert resultado.amount == Decimal("70")
        assert resultado.currency == Currency.BRL

    def test_subtrai_moedas_diferentes_erro(self):
        """Subtração de moedas diferentes deve lançar CurrencyMismatchError."""
        a = Money(Decimal("100"), Currency.BRL)
        b = Money(Decimal("30"), Currency.USD)
        with pytest.raises(CurrencyMismatchError):
            _ = a - b

    def test_multiplica_por_escalar(self):
        """Multiplicação por escalar deve funcionar."""
        money = Money(Decimal("100"), Currency.BRL)
        resultado = money * Decimal("2.5")
        assert resultado.amount == Decimal("250")
        assert resultado.currency == Currency.BRL

    def test_multiplicacao_comutativa(self):
        """Multiplicação deve ser comutativa (escalar * money)."""
        money = Money(Decimal("100"), Currency.BRL)
        resultado = Decimal("2") * money
        assert resultado.amount == Decimal("200")
        assert resultado.currency == Currency.BRL

    # === Conversão ===

    def test_converte_para_outra_moeda(self):
        """Conversão deve multiplicar pela taxa."""
        money = Money(Decimal("100"), Currency.USD)
        taxa = Decimal("5.0")  # 1 USD = 5 BRL
        resultado = money.convert_to(Currency.BRL, taxa)
        assert resultado.amount == Decimal("500")
        assert resultado.currency == Currency.BRL

    def test_converte_para_mesma_moeda_retorna_self(self):
        """Conversão para mesma moeda deve retornar o mesmo valor."""
        money = Money(Decimal("100"), Currency.BRL)
        resultado = money.convert_to(Currency.BRL, Decimal("5"))
        assert resultado.amount == Decimal("100")
        assert resultado.currency == Currency.BRL

    # === Formatação ===

    def test_formata_brl_com_simbolo(self):
        """Formatação BRL deve usar R$."""
        money = Money(Decimal("1234.56"), Currency.BRL)
        formatted = money.format()
        assert "R$" in formatted
        assert "1.234,56" in formatted or "1234.56" in formatted

    def test_formata_usd_com_simbolo(self):
        """Formatação USD deve usar $."""
        money = Money(Decimal("1234.56"), Currency.USD)
        formatted = money.format()
        assert "$" in formatted
        assert "1,234.56" in formatted or "1234.56" in formatted

    def test_formata_eur_com_simbolo(self):
        """Formatação EUR deve usar €."""
        money = Money(Decimal("1234.56"), Currency.EUR)
        formatted = money.format()
        assert "€" in formatted

    def test_formata_gbp_com_simbolo(self):
        """Formatação GBP deve usar £."""
        money = Money(Decimal("1234.56"), Currency.GBP)
        formatted = money.format()
        assert "£" in formatted

    def test_formata_btc_com_simbolo(self):
        """Formatação BTC deve usar ₿."""
        money = Money(Decimal("0.12345678"), Currency.BTC)
        formatted = money.format()
        assert "₿" in formatted or "BTC" in formatted

    def test_formata_eth_com_simbolo(self):
        """Formatação ETH deve usar Ξ."""
        money = Money(Decimal("1.5"), Currency.ETH)
        formatted = money.format()
        assert "Ξ" in formatted or "ETH" in formatted


class TestCurrencyMismatchError:
    """Testes para CurrencyMismatchError."""

    def test_erro_contem_moedas_envolvidas(self):
        """Erro deve informar quais moedas causaram o problema."""
        error = CurrencyMismatchError(Currency.BRL, Currency.USD)
        assert "BRL" in str(error)
        assert "USD" in str(error)
