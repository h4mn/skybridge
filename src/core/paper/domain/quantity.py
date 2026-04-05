"""
Quantity Value Object para sistema de trading.

Representa uma quantidade com precisão contextual, suportando
diferentes tipos de ativos (ações, cripto, forex).
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Union


class AssetType(Enum):
    """
    Tipos de ativo suportados.

    STOCK: Ações em lote padrão (ex: PETR4.SA - lote 100)
    STOCK_FRACTION: Ações fracionárias (ex: PETR4F.SA - lote 1)
    CRYPTO: Criptomoedas (ex: BTC-USD - precisão 8)
    FOREX: Câmbio (ex: EUR/USD - precisão 5)
    """

    STOCK = "stock"
    STOCK_FRACTION = "stock_fraction"
    CRYPTO = "crypto"
    FOREX = "forex"


class AssetTypeMismatchError(Exception):
    """Erro lançado ao tentar operar com asset types diferentes."""

    def __init__(self, from_type: AssetType, to_type: AssetType):
        self.from_type = from_type
        self.to_type = to_type
        super().__init__(
            f"Cannot operate on different asset types: "
            f"{from_type.value} and {to_type.value}"
        )


# Tickers B3 que usam lote padrão de 100
B3_LOTE_PADRAO_TICKERS = {
    # Petrobras
    "PETR3.SA",
    "PETR4.SA",
    # Vale
    "VALE3.SA",
    # Itaú
    "ITUB3.SA",
    "ITUB4.SA",
    # BB
    "BBDC3.SA",
    "BBDC4.SA",
    # Bradesco
    "BBAS3.SA",
    # Ambev
    "ABEV3.SA",
    # JBSS3
    "JBSS3.SA",
    # RECV3
    "RECV3.SA",
}

# Tickes B3 fracionários (sufixo F)
B3_FRACIONARIO_SUFFIX = "F.SA"


@dataclass(frozen=True)
class Quantity:
    """
    Value Object para quantidade com precisão contextual.

    Attributes:
        value: Valor da quantidade.
        precision: Número de casas decimais.
        min_tick: Menor unidade negociável.
        asset_type: Tipo do ativo.

    Example:
        >>> qty = Quantity(Decimal("100"), precision=0, min_tick=Decimal("1"), asset_type=AssetType.STOCK)
        >>> qty.adjust_to_tick().value
        Decimal('100')
    """

    value: Decimal
    precision: int
    min_tick: Decimal
    asset_type: AssetType

    def __post_init__(self):
        """Valida os valores após inicialização."""
        # Validar precision
        if self.precision < 0:
            raise ValueError(f"Precision must be >= 0, got {self.precision}")

        # Validar min_tick
        if self.min_tick <= 0:
            raise ValueError(f"min_tick must be > 0, got {self.min_tick}")

        # Validar value não negativo para STOCK
        if self.asset_type == AssetType.STOCK and self.value < 0:
            raise ValueError(
                f"Quantity cannot be negative for STOCK, got {self.value}"
            )

        if self.asset_type == AssetType.STOCK_FRACTION and self.value < 0:
            raise ValueError(
                f"Quantity cannot be negative for STOCK_FRACTION, got {self.value}"
            )

    def adjust_to_tick(self) -> "Quantity":
        """
        Ajusta valor para o tick mais próximo usando arredondamento half-up.

        Returns:
            Nova Quantity com valor ajustado.
        """
        # Calcular valor ajustado
        quotient = self.value / self.min_tick
        adjusted_quotient = quotient.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        adjusted_value = adjusted_quotient * self.min_tick

        return Quantity(
            value=adjusted_value,
            precision=self.precision,
            min_tick=self.min_tick,
            asset_type=self.asset_type,
        )

    def is_valid_for(self, ticker: str) -> bool:
        """
        Verifica se a quantidade é válida para o ticker específico.

        Args:
            ticker: Código do ativo (ex: "PETR4.SA", "BTC-USD").

        Returns:
            True se a quantidade é válida para o ticker.

        Rules:
            - STOCK B3: deve ser múltiplo de 100 (lote padrão)
            - STOCK_FRACTION B3: qualquer quantidade inteira >= 1
            - CRYPTO: qualquer quantidade > 0 com até 8 casas
            - FOREX: qualquer quantidade com até 5 casas
        """
        ticker_upper = ticker.upper()

        # Stock fracionário B3 (sufixo F)
        if ticker_upper.endswith(B3_FRACIONARIO_SUFFIX):
            return self.value >= 1 and self.value == int(self.value)

        # Stock B3 lote padrão
        if ticker_upper in B3_LOTE_PADRAO_TICKERS:
            return self.value >= 100 and self.value % 100 == 0

        # Crypto
        if self.asset_type == AssetType.CRYPTO:
            return self.value >= 0 and self.value >= self.min_tick

        # Forex
        if self.asset_type == AssetType.FOREX:
            return self.value >= 0

        # Default: valor positivo
        return self.value >= 0

    def __add__(self, other: "Quantity") -> "Quantity":
        """Soma duas quantities do mesmo tipo."""
        if self.asset_type != other.asset_type:
            raise AssetTypeMismatchError(self.asset_type, other.asset_type)
        return Quantity(
            value=self.value + other.value,
            precision=self.precision,
            min_tick=self.min_tick,
            asset_type=self.asset_type,
        )

    def __sub__(self, other: "Quantity") -> "Quantity":
        """Subtrai duas quantities do mesmo tipo."""
        if self.asset_type != other.asset_type:
            raise AssetTypeMismatchError(self.asset_type, other.asset_type)
        return Quantity(
            value=self.value - other.value,
            precision=self.precision,
            min_tick=self.min_tick,
            asset_type=self.asset_type,
        )

    def __mul__(self, scalar: Union[Decimal, int, float]) -> "Quantity":
        """Multiplica por escalar."""
        if isinstance(scalar, (int, float)):
            scalar = Decimal(str(scalar))
        return Quantity(
            value=self.value * scalar,
            precision=self.precision,
            min_tick=self.min_tick,
            asset_type=self.asset_type,
        )

    def __rmul__(self, scalar: Union[Decimal, int, float]) -> "Quantity":
        """Multiplicação comutativa (escalar * quantity)."""
        return self.__mul__(scalar)
