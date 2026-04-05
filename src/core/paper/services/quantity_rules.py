"""
QuantityRules Service para regras de quantidade por ticker.

Este service conhece as regras de quantidade (lote, precisão, tick mínimo)
para diferentes tipos de ativos e exchanges.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class QuantitySpec:
    """
    Especificação de quantidade para um contexto de ticker.

    Attributes:
        min_quantity: Quantidade mínima permitida.
        max_quantity: Quantidade máxima permitida.
        precision: Número de casas decimais.
        min_tick: Menor unidade negociável.
        lot_size: Tamanho do lote padrão (1 para fracionário/crypto).
    """

    min_quantity: Decimal
    max_quantity: Decimal
    precision: int
    min_tick: Decimal
    lot_size: int


class QuantityRules:
    """
    Service que conhece regras de quantidade por ticker/exchange.

    Este service centraliza o conhecimento sobre:
    - Lotes padrão de ações na B3 (100 unidades)
    - Lotes fracionários da B3 (1 unidade, sufixo F)
    - Precisão de cripto (8 casas para BTC, 18 para ETH)
    - Precisão de forex (5 casas)

    Example:
        >>> spec = QuantityRules.for_ticker("PETR4.SA")
        >>> spec.lot_size
        100
        >>> spec = QuantityRules.for_ticker("BTC-USD")
        >>> spec.precision
        8
    """

    # === Specs por Exchange/Tipo ===

    # B3 Lote Padrão (100 unidades)
    B3_LOTE_PADRAO = QuantitySpec(
        min_quantity=Decimal("100"),
        max_quantity=Decimal("100000000"),
        precision=0,
        min_tick=Decimal("1"),
        lot_size=100,
    )

    # B3 Fracionário (1 unidade)
    B3_FRACIONARIO = QuantitySpec(
        min_quantity=Decimal("1"),
        max_quantity=Decimal("99999"),
        precision=0,
        min_tick=Decimal("1"),
        lot_size=1,
    )

    # Bitcoin (8 casas)
    CRYPTO_BTC = QuantitySpec(
        min_quantity=Decimal("0.00000001"),
        max_quantity=Decimal("21000000"),
        precision=8,
        min_tick=Decimal("0.00000001"),
        lot_size=1,
    )

    # Ethereum (18 casas)
    CRYPTO_ETH = QuantitySpec(
        min_quantity=Decimal("0.000000000000000001"),
        max_quantity=Decimal("100000000"),
        precision=18,
        min_tick=Decimal("0.000000000000000001"),
        lot_size=1,
    )

    # Crypto genérico (8 casas)
    CRYPTO_GENERIC = QuantitySpec(
        min_quantity=Decimal("0.00000001"),
        max_quantity=Decimal("1000000000"),
        precision=8,
        min_tick=Decimal("0.00000001"),
        lot_size=1,
    )

    # Forex (5 casas, lote 1000)
    FOREX = QuantitySpec(
        min_quantity=Decimal("1000"),
        max_quantity=Decimal("100000000"),
        precision=5,
        min_tick=Decimal("0.00001"),
        lot_size=1000,
    )

    # Default conservador (2 casas, lote 1)
    DEFAULT = QuantitySpec(
        min_quantity=Decimal("0.01"),
        max_quantity=Decimal("100000000"),
        precision=2,
        min_tick=Decimal("0.01"),
        lot_size=1,
    )

    @classmethod
    def for_ticker(
        cls, ticker: str, exchange: Optional[str] = None
    ) -> QuantitySpec:
        """
        Retorna especificação de quantidade para o ticker.

        Args:
            ticker: Código do ativo (ex: "PETR4.SA", "BTC-USD").
            exchange: Exchange opcional (B3, CRYPTO, FOREX).

        Returns:
            QuantitySpec com regras para o ticker.

        Example:
            >>> spec = QuantityRules.for_ticker("PETR4.SA")
            >>> spec.lot_size
            100
        """
        # Normalizar ticker
        normalized = cls.normalize_ticker(ticker)

        # Detectar exchange se não fornecida
        if exchange is None:
            exchange = cls.get_exchange(normalized)

        exchange = exchange.upper()

        # B3
        if exchange == "B3":
            # Verificar se é fracionário (sufixo F)
            if normalized.endswith("F.SA"):
                return cls.B3_FRACIONARIO
            return cls.B3_LOTE_PADRAO

        # Crypto
        if exchange == "CRYPTO":
            if normalized.startswith("BTC"):
                return cls.CRYPTO_BTC
            if normalized.startswith("ETH"):
                return cls.CRYPTO_ETH
            return cls.CRYPTO_GENERIC

        # Forex
        if exchange == "FOREX":
            return cls.FOREX

        # Default
        return cls.DEFAULT

    @staticmethod
    def normalize_ticker(ticker: str) -> str:
        """
        Normaliza ticker removendo espaços e convertendo para uppercase.

        Args:
            ticker: Ticker a normalizar.

        Returns:
            Ticker normalizado.

        Example:
            >>> QuantityRules.normalize_ticker("  petr4.sa  ")
            'PETR4.SA'
        """
        return ticker.strip().upper()

    @staticmethod
    def get_exchange(ticker: str) -> str:
        """
        Detecta exchange pelo formato do ticker.

        Args:
            ticker: Ticker a analisar.

        Returns:
            Nome da exchange detectada (B3, CRYPTO, FOREX, UNKNOWN).

        Example:
            >>> QuantityRules.get_exchange("PETR4.SA")
            'B3'
            >>> QuantityRules.get_exchange("BTC-USD")
            'CRYPTO'
        """
        normalized = ticker.strip().upper()

        # B3: sufixo .SA
        if normalized.endswith(".SA"):
            return "B3"

        # Crypto: formato XXX-USD ou XXX-BRL ou XXX-USDT
        crypto_patterns = ["-USD", "-BRL", "-USDT", "-EUR"]
        for pattern in crypto_patterns:
            if pattern in normalized:
                return "CRYPTO"

        # Forex: formato XXX/YYY
        if "/" in normalized:
            return "FOREX"

        return "UNKNOWN"
