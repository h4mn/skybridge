"""
Testes unitários para Quantity Value Object.

DOC: src/core/paper/domain/quantity.py - Quantity VO com precisão contextual.

Cenários:
- Criação com value, precision, min_tick e asset_type
- Validação no __post_init__ (value alinhado com precision e min_tick)
- Ajuste para tick mais próximo (adjust_to_tick)
- Verificação de validade para ticker específico (is_valid_for)
"""
import pytest
from decimal import Decimal

from src.core.paper.domain.quantity import Quantity, AssetType, AssetTypeMismatchError


class TestAssetTypeEnum:
    """Testes para o enum AssetType."""

    def test_asset_type_contem_tipos_esperados(self):
        """AssetType deve conter tipos STOCK, STOCK_FRACTION, CRYPTO, FOREX."""
        assert AssetType.STOCK.value == "stock"
        assert AssetType.STOCK_FRACTION.value == "stock_fraction"
        assert AssetType.CRYPTO.value == "crypto"
        assert AssetType.FOREX.value == "forex"


class TestQuantityValueObject:
    """Testes para o Value Object Quantity."""

    # === Criação ===

    def test_cria_quantity_com_value_precision_min_tick(self):
        """Quantity deve ser criado com value, precision, min_tick."""
        qty = Quantity(
            value=Decimal("100"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        assert qty.value == Decimal("100")
        assert qty.precision == 0
        assert qty.min_tick == Decimal("1")
        assert qty.asset_type == AssetType.STOCK

    def test_quantity_e_imutavel(self):
        """Quantity deve ser frozen/immutable."""
        qty = Quantity(
            value=Decimal("100"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        with pytest.raises(AttributeError):
            qty.value = Decimal("200")

    # === Validação no __post_init__ ===

    def test_valida_erro_se_precision_negativo(self):
        """Precision negativo deve lançar erro."""
        with pytest.raises(ValueError):
            Quantity(
                value=Decimal("100"),
                precision=-1,
                min_tick=Decimal("1"),
                asset_type=AssetType.STOCK,
            )

    def test_valida_erro_se_min_tick_zero_ou_negativo(self):
        """min_tick zero ou negativo deve lançar erro."""
        with pytest.raises(ValueError):
            Quantity(
                value=Decimal("100"),
                precision=0,
                min_tick=Decimal("0"),
                asset_type=AssetType.STOCK,
            )
        with pytest.raises(ValueError):
            Quantity(
                value=Decimal("100"),
                precision=0,
                min_tick=Decimal("-1"),
                asset_type=AssetType.STOCK,
            )

    def test_valida_erro_se_value_negativo_para_stock(self):
        """Value negativo para STOCK deve lançar erro (sem short)."""
        with pytest.raises(ValueError):
            Quantity(
                value=Decimal("-10"),
                precision=0,
                min_tick=Decimal("1"),
                asset_type=AssetType.STOCK,
            )

    def test_valida_ok_para_value_zero(self):
        """Value zero deve ser permitido."""
        qty = Quantity(
            value=Decimal("0"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        assert qty.value == Decimal("0")

    # === adjust_to_tick ===

    def test_adjust_to_tick_arredonda_para_baixo(self):
        """adjust_to_tick deve arredondar para tick mais próximo (para baixo se < 0.5)."""
        qty = Quantity(
            value=Decimal("100.3"),  # < 0.5 arredonda para baixo
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        adjusted = qty.adjust_to_tick()
        assert adjusted.value == Decimal("100")

    def test_adjust_to_tick_arredonda_para_cima(self):
        """adjust_to_tick deve arredondar para tick mais próximo (para cima)."""
        qty = Quantity(
            value=Decimal("100.5"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        adjusted = qty.adjust_to_tick()
        assert adjusted.value == Decimal("101")

    def test_adjust_to_tick_crypto_8_casas(self):
        """adjust_to_tick para crypto com 8 casas decimais."""
        qty = Quantity(
            value=Decimal("0.123456789"),
            precision=8,
            min_tick=Decimal("0.00000001"),
            asset_type=AssetType.CRYPTO,
        )
        adjusted = qty.adjust_to_tick()
        assert adjusted.value == Decimal("0.12345679")

    def test_adjust_to_tick_ja_valido_retorna_igual(self):
        """Valor já alinhado com tick deve retornar igual."""
        qty = Quantity(
            value=Decimal("100"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        adjusted = qty.adjust_to_tick()
        assert adjusted.value == qty.value

    # === is_valid_for ===

    def test_is_valid_for_stock_b3_lote_padrao(self):
        """Stock B3 lote padrão deve ser múltiplo de 100."""
        qty_lote = Quantity(
            value=Decimal("100"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        qty_fora_lote = Quantity(
            value=Decimal("50"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        assert qty_lote.is_valid_for("PETR4.SA") is True
        assert qty_fora_lote.is_valid_for("PETR4.SA") is False

    def test_is_valid_for_stock_fraction_b3(self):
        """Stock fracionário B3 aceita qualquer quantidade inteira."""
        qty = Quantity(
            value=Decimal("1"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK_FRACTION,
        )
        assert qty.is_valid_for("PETR4F.SA") is True

    def test_is_valid_for_crypto(self):
        """Crypto aceita frações com até 8 casas."""
        qty = Quantity(
            value=Decimal("0.12345678"),
            precision=8,
            min_tick=Decimal("0.00000001"),
            asset_type=AssetType.CRYPTO,
        )
        assert qty.is_valid_for("BTC-USD") is True

    def test_is_valid_for_forex(self):
        """Forex aceita frações com até 5 casas."""
        qty = Quantity(
            value=Decimal("1000.12345"),
            precision=5,
            min_tick=Decimal("0.00001"),
            asset_type=AssetType.FOREX,
        )
        assert qty.is_valid_for("EUR/USD") is True

    # === Operações Matemáticas ===

    def test_soma_duas_quantities_mesmo_tipo(self):
        """Soma de duas quantities do mesmo tipo deve funcionar."""
        a = Quantity(
            value=Decimal("100"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        b = Quantity(
            value=Decimal("50"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        resultado = a + b
        assert resultado.value == Decimal("150")

    def test_soma_quantities_tipos_diferentes_erro(self):
        """Soma de quantities de tipos diferentes deve lançar AssetTypeMismatchError."""
        a = Quantity(
            value=Decimal("100"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        b = Quantity(
            value=Decimal("0.5"),
            precision=8,
            min_tick=Decimal("0.00000001"),
            asset_type=AssetType.CRYPTO,
        )
        with pytest.raises(AssetTypeMismatchError):
            _ = a + b

    def test_multiplica_por_escalar(self):
        """Multiplicação por escalar deve funcionar."""
        qty = Quantity(
            value=Decimal("100"),
            precision=0,
            min_tick=Decimal("1"),
            asset_type=AssetType.STOCK,
        )
        resultado = qty * Decimal("2")
        assert resultado.value == Decimal("200")
