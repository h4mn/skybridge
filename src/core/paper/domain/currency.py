"""
Currency enum para sistema multi-moeda.

Define moedas fiat e crypto suportadas pelo sistema de paper trading.
"""
from enum import Enum


class Currency(Enum):
    """
    Moedas suportadas pelo sistema.

    Moedas Fiat:
        - BRL: Real Brasileiro
        - USD: Dólar Americano
        - EUR: Euro
        - GBP: Libra Esterlina

    Moedas Crypto:
        - BTC: Bitcoin
        - ETH: Ethereum
    """

    BRL = "BRL"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    BTC = "BTC"
    ETH = "ETH"

    @property
    def is_fiat(self) -> bool:
        """Retorna True se for moeda fiat."""
        return self in (Currency.BRL, Currency.USD, Currency.EUR, Currency.GBP)

    @property
    def is_crypto(self) -> bool:
        """Retorna True se for criptomoeda."""
        return self in (Currency.BTC, Currency.ETH)
