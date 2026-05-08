# -*- coding: utf-8 -*-
"""Testes para StrategyProtocol."""

from decimal import Decimal

import pytest

from src.core.paper.domain.strategies.signal import DadosMercado, SinalEstrategia, TipoSinal


class TestStrategyProtocol:
    """DOC: specs/trading-strategies — StrategyProtocol interface."""

    def test_duck_typing_satisfaz_protocol(self):
        """WHEN classe implementa name e evaluate THEN satisfaz StrategyProtocol."""
        from src.core.paper.domain.strategies.protocol import StrategyProtocol

        class MinhaEstrategia:
            name = "minha-estrategia"

            def evaluate(self, dados):
                return None

        assert isinstance(MinhaEstrategia(), StrategyProtocol)

    def test_evaluate_retorna_none_sem_sinal(self):
        """WHEN evaluate() não detecta oportunidade THEN retorna None."""
        from src.core.paper.domain.strategies.protocol import StrategyProtocol

        class EstrategiaNeutra:
            name = "neutra"

            def evaluate(self, dados):
                return None

        estrategia = EstrategiaNeutra()
        dados = DadosMercado(ticker="BTC-USD", preco_atual=Decimal("50000"), historico_precos=())
        result = estrategia.evaluate(dados)
        assert result is None

    def test_evaluate_retorna_sinal_com_oportunidade(self):
        """WHEN evaluate() detecta oportunidade THEN retorna SinalEstrategia com tipo != NEUTRO."""
        from src.core.paper.domain.strategies.protocol import StrategyProtocol

        class EstrategiaCompra:
            name = "compra-fixa"

            def evaluate(self, dados):
                return SinalEstrategia(
                    ticker=dados.ticker,
                    tipo=TipoSinal.COMPRA,
                    preco=dados.preco_atual,
                    razao="teste",
                )

        estrategia = EstrategiaCompra()
        dados = DadosMercado(ticker="BTC-USD", preco_atual=Decimal("50000"), historico_precos=())
        result = estrategia.evaluate(dados)

        assert result is not None
        assert isinstance(result, SinalEstrategia)
        assert result.tipo != TipoSinal.NEUTRO
