"""
Testes unitários para QuantityRules Service.

DOC: src/core/paper/services/quantity_rules.py - Service de regras de quantidade por ticker.

Cenários:
- Retornar spec para ticker B3 lote padrão
- Retornar spec para ticker B3 fracionário
- Retornar spec para cripto (BTC, ETH)
- Retornar spec para forex
- Retornar default para ticker desconhecido
"""
import pytest
from decimal import Decimal

from src.core.paper.services.quantity_rules import QuantityRules, QuantitySpec


class TestQuantitySpec:
    """Testes para QuantitySpec dataclass."""

    def test_cria_quantity_spec_com_todos_campos(self):
        """QuantitySpec deve ser criado com min, max, precision, min_tick, lot_size."""
        spec = QuantitySpec(
            min_quantity=Decimal("1"),
            max_quantity=Decimal("1000000"),
            precision=0,
            min_tick=Decimal("1"),
            lot_size=100,
        )
        assert spec.min_quantity == Decimal("1")
        assert spec.max_quantity == Decimal("1000000")
        assert spec.precision == 0
        assert spec.min_tick == Decimal("1")
        assert spec.lot_size == 100


class TestQuantityRules:
    """Testes para QuantityRules service."""

    # === B3 Lote Padrão ===

    def test_for_ticker_b3_lote_padrao_retorna_spec_correto(self):
        """Ticker B3 lote padrão deve retornar spec com lote 100."""
        spec = QuantityRules.for_ticker("PETR4.SA", exchange="B3")
        assert spec.lot_size == 100
        assert spec.precision == 0
        assert spec.min_tick == Decimal("1")
        assert spec.min_quantity == Decimal("100")

    def test_for_ticker_b3_varios_tickers_lote_padrao(self):
        """Vários tickers B3 devem retornar spec lote padrão."""
        tickers = ["VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA"]
        for ticker in tickers:
            spec = QuantityRules.for_ticker(ticker, exchange="B3")
            assert spec.lot_size == 100

    # === B3 Fracionário ===

    def test_for_ticker_b3_fracionario_retorna_spec_correto(self):
        """Ticker B3 fracionário (F) deve retornar spec com lote 1."""
        spec = QuantityRules.for_ticker("PETR4F.SA", exchange="B3")
        assert spec.lot_size == 1
        assert spec.precision == 0
        assert spec.min_tick == Decimal("1")
        assert spec.min_quantity == Decimal("1")

    def test_for_ticker_b3_fracionario_detecta_sufixo_f(self):
        """Tickers com sufixo F devem ser detectados como fracionários."""
        spec_petr = QuantityRules.for_ticker("PETR4F.SA", exchange="B3")
        spec_vale = QuantityRules.for_ticker("VALE3F.SA", exchange="B3")
        assert spec_petr.lot_size == 1
        assert spec_vale.lot_size == 1

    # === Crypto ===

    def test_for_ticker_btc_usd_retorna_spec_crypto(self):
        """BTC-USD deve retornar spec crypto com 8 casas."""
        spec = QuantityRules.for_ticker("BTC-USD", exchange="CRYPTO")
        assert spec.precision == 8
        assert spec.min_tick == Decimal("0.00000001")
        assert spec.lot_size == 1
        assert spec.min_quantity == Decimal("0.00000001")

    def test_for_ticker_eth_usd_retorna_spec_crypto(self):
        """ETH-USD deve retornar spec crypto com 18 casas."""
        spec = QuantityRules.for_ticker("ETH-USD", exchange="CRYPTO")
        assert spec.precision == 18
        assert spec.min_tick == Decimal("0.000000000000000001")
        assert spec.lot_size == 1

    def test_for_ticker_crypto_brl_tambem_funciona(self):
        """Crypto em BRL também deve funcionar."""
        spec = QuantityRules.for_ticker("BTC-BRL", exchange="CRYPTO")
        assert spec.precision == 8
        assert spec.lot_size == 1

    # === Forex ===

    def test_for_ticker_forex_retorna_spec_correto(self):
        """Forex deve retornar spec com 5 casas e lote 1000."""
        spec = QuantityRules.for_ticker("EUR/USD", exchange="FOREX")
        assert spec.precision == 5
        assert spec.min_tick == Decimal("0.00001")
        assert spec.lot_size == 1000
        assert spec.min_quantity == Decimal("1000")

    def test_for_ticker_forex_varios_pares(self):
        """Vários pares forex devem funcionar."""
        pairs = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/BRL"]
        for pair in pairs:
            spec = QuantityRules.for_ticker(pair, exchange="FOREX")
            assert spec.precision == 5

    # === Default ===

    def test_for_ticker_desconhecido_retorna_default(self):
        """Ticker desconhecido deve retornar spec default conservador."""
        spec = QuantityRules.for_ticker("UNKNOWN", exchange="UNKNOWN")
        assert spec.lot_size == 1
        assert spec.precision == 2
        assert spec.min_tick == Decimal("0.01")

    # === Case Insensitive ===

    def test_for_ticker_case_insensitive(self):
        """Ticker deve ser case insensitive."""
        spec_lower = QuantityRules.for_ticker("petr4.sa", exchange="b3")
        spec_upper = QuantityRules.for_ticker("PETR4.SA", exchange="B3")
        assert spec_lower.lot_size == spec_upper.lot_size

    # === Normalize Ticker ===

    def test_normalize_ticker_remove_espacos(self):
        """normalize_ticker deve remover espaços."""
        normalized = QuantityRules.normalize_ticker("  PETR4.SA  ")
        assert normalized == "PETR4.SA"

    def test_normalize_ticker_uppercase(self):
        """normalize_ticker deve converter para uppercase."""
        normalized = QuantityRules.normalize_ticker("petr4.sa")
        assert normalized == "PETR4.SA"

    # === Get Exchange ===

    def test_get_exchange_detecta_b3(self):
        """get_exchange deve detectar B3 pelo sufixo .SA."""
        exchange = QuantityRules.get_exchange("PETR4.SA")
        assert exchange == "B3"

    def test_get_exchange_detecta_crypto(self):
        """get_exchange deve detectar CRYPTO pelo formato BTC-USD."""
        exchange = QuantityRules.get_exchange("BTC-USD")
        assert exchange == "CRYPTO"

    def test_get_exchange_detecta_forex(self):
        """get_exchange deve detectar FOREX pelo formato EUR/USD."""
        exchange = QuantityRules.get_exchange("EUR/USD")
        assert exchange == "FOREX"
