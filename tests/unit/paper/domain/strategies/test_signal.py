# -*- coding: utf-8 -*-
"""Testes para Value Objects de sinal: TipoSinal, DadosMercado, SinalEstrategia."""

from decimal import Decimal

import pytest


# ═══════════════════════════════════════════════════════════════════════
# TipoSinal
# ═══════════════════════════════════════════════════════════════════════

class TestTipoSinal:
    """DOC: specs/trading-strategies — TipoSinal enum."""

    def test_tipo_sinal_compra_valor_string(self):
        """WHEN instanciar TipoSinal.COMPRA THEN valor SHALL ser 'compra'."""
        from src.core.paper.domain.strategies.signal import TipoSinal

        assert TipoSinal.COMPRA.value == "compra"

    def test_tipo_sinal_venda_valor_string(self):
        """WHEN instanciar TipoSinal.VENDA THEN valor SHALL ser 'venda'."""
        from src.core.paper.domain.strategies.signal import TipoSinal

        assert TipoSinal.VENDA.value == "venda"

    def test_tipo_sinal_neutro_valor_string(self):
        """WHEN instanciar TipoSinal.NEUTRO THEN valor SHALL ser 'neutro'."""
        from src.core.paper.domain.strategies.signal import TipoSinal

        assert TipoSinal.NEUTRO.value == "neutro"


# ═══════════════════════════════════════════════════════════════════════
# DadosMercado
# ═══════════════════════════════════════════════════════════════════════

class TestDadosMercado:
    """DOC: specs/trading-strategies — DadosMercado value object."""

    def test_criar_dados_mercado(self):
        """WHEN criar DadosMercado THEN objeto SHALL ser frozen (imutável)."""
        from src.core.paper.domain.strategies.signal import DadosMercado

        dados = DadosMercado(
            ticker="BTC-USD",
            preco_atual=Decimal("50000"),
            historico_precos=(Decimal("48000"), Decimal("49000"), Decimal("50000")),
        )

        assert dados.ticker == "BTC-USD"
        assert dados.preco_atual == Decimal("50000")
        assert len(dados.historico_precos) == 3
        with pytest.raises(AttributeError):
            dados.ticker = "ETH-USD"

    def test_dados_mercado_historico_vazio(self):
        """WHEN criar DadosMercado com historico_precos=[] THEN cria sem erro."""
        from src.core.paper.domain.strategies.signal import DadosMercado

        dados = DadosMercado(
            ticker="BTC-USD",
            preco_atual=Decimal("50000"),
            historico_precos=[],
        )

        assert dados.historico_precos == ()


# ═══════════════════════════════════════════════════════════════════════
# SinalEstrategia
# ═══════════════════════════════════════════════════════════════════════

class TestSinalEstrategia:
    """DOC: specs/trading-strategies — SinalEstrategia value object."""

    def test_criar_sinal_compra(self):
        """WHEN criar SinalEstrategia THEN objeto SHALL ser frozen e timestamp preenchido."""
        from src.core.paper.domain.strategies.signal import SinalEstrategia, TipoSinal

        sinal = SinalEstrategia(
            ticker="BTC-USD",
            tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"),
            razao="SMA5 > SMA15",
        )

        assert sinal.ticker == "BTC-USD"
        assert sinal.tipo == TipoSinal.COMPRA
        assert sinal.preco == Decimal("50000")
        assert sinal.razao == "SMA5 > SMA15"
        assert sinal.timestamp is not None

    def test_sinal_to_dict(self):
        """WHEN chamar sinal.to_dict() THEN retorna dict com chaves esperadas."""
        from src.core.paper.domain.strategies.signal import SinalEstrategia, TipoSinal

        sinal = SinalEstrategia(
            ticker="BTC-USD",
            tipo=TipoSinal.COMPRA,
            preco=Decimal("50000"),
            razao="SMA5 > SMA15",
        )

        d = sinal.to_dict()
        assert d["ticker"] == "BTC-USD"
        assert d["tipo"] == "compra"
        assert d["preco"] == "50000"
        assert "timestamp" in d
        assert "razao" in d
