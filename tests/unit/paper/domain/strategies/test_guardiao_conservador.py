# -*- coding: utf-8 -*-
"""Testes para GuardiaoConservador — SMA crossover strategy."""

from decimal import Decimal

import pytest

from src.core.paper.domain.strategies.signal import DadosMercado, TipoSinal


def _make_dados(historico: list[int]) -> DadosMercado:
    """Helper: cria DadosMercado com histórico de preços inteiros."""
    precos = tuple(Decimal(str(p)) for p in historico)
    return DadosMercado(
        ticker="BTC-USD",
        preco_atual=precos[-1],
        historico_precos=precos,
    )


class TestGuardiaoSMA:
    """DOC: specs/guardiao-conservador — Cálculo de SMA."""

    def test_sma_dados_suficientes(self):
        """WHEN calcular SMA(3) com [10, 20, 30] THEN resultado = 20."""
        from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador

        strategy = GuardiaoConservador()
        result = strategy._calculate_sma(
            (Decimal("10"), Decimal("20"), Decimal("30")), 3
        )
        assert result == Decimal("20")

    def test_sma_dados_insuficientes(self):
        """WHEN calcular SMA(5) com [10, 20] THEN retorna None."""
        from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador

        strategy = GuardiaoConservador()
        result = strategy._calculate_sma(
            (Decimal("10"), Decimal("20")), 5
        )
        assert result is None

    def test_sma_dados_exatos(self):
        """WHEN calcular SMA(5) com exatamente 5 preços THEN retorna média."""
        from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador

        strategy = GuardiaoConservador()
        precos = tuple(Decimal(str(p)) for p in [10, 20, 30, 40, 50])
        result = strategy._calculate_sma(precos, 5)
        assert result == Decimal("30")


class TestGuardiaoCrossover:
    """DOC: specs/guardiao-conservador — Detecção de crossover."""

    def test_crossover_compra(self):
        """WHEN SMA5 cruza acima de SMA15 THEN sinal COMPRA."""
        from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador

        strategy = GuardiaoConservador()
        # 16 preços estáveis em 100, depois 5 que sobem abruptamente
        # Com 21 preços: prev = primeiros 20, atual = todos 21
        # Preciso que prev_SMA5 <= prev_SMA15 e SMA5 > SMA15
        # Estratégia: preços 0..14 = 100, 15 = 80, 16..20 sobem rápido
        # Prev (0..19): SMA15(0..14)=100, SMA5(15..19)=(80,90,100,110,120)/5=100
        #   prev_SMA5=100 <= prev_SMA15=100 ✓ (empate conta como <=)
        # Atual (0..20): SMA15(1..15)=(100*14+80)/15=98.67, SMA5(16..20)=(90,100,110,120,130)/5=110
        #   SMA5=110 > SMA15=98.67 ✓ crossover!
        historico = [100]*15 + [80, 90, 100, 110, 120, 130]
        dados = _make_dados(historico)
        sinal = strategy.evaluate(dados)

        assert sinal is not None
        assert sinal.tipo == TipoSinal.COMPRA
        assert "SMA5 cruzou acima de SMA15" in sinal.razao

    def test_crossover_venda(self):
        """WHEN SMA5 cruza abaixo de SMA15 THEN sinal VENDA."""
        from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador

        strategy = GuardiaoConservador()
        # Mesma lógica invertida: estáveis, depois sobem, depois caem abruptamente
        # Preciso que prev_SMA5 >= prev_SMA15 e SMA5 < SMA15
        # Preços 0..14 = 100, 15 = 120, 16..20 caem: 110,100,90,80,70
        # Prev (0..19): SMA15(0..14)=100, SMA5(15..19)=(120,110,100,90,80)/5=100
        #   prev_SMA5=100 >= prev_SMA15=100 ✓
        # Atual (0..20): SMA15(1..15)=(100*14+120)/15=101.33, SMA5(16..20)=(110,100,90,80,70)/5=90
        #   SMA5=90 < SMA15=101.33 ✓ crossover!
        historico = [100]*15 + [120, 110, 100, 90, 80, 70]
        dados = _make_dados(historico)
        sinal = strategy.evaluate(dados)

        assert sinal is not None
        assert sinal.tipo == TipoSinal.VENDA
        assert "SMA5 cruzou abaixo de SMA15" in sinal.razao

    def test_sem_crossover_tendencia_mantida(self):
        """WHEN SMA5 estava acima e continua acima THEN retorna None."""
        from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador

        strategy = GuardiaoConservador()
        # Tendência de alta consistente — sem cruzamento
        historico = list(range(1, 21))  # 1,2,3,...,20
        dados = _make_dados(historico)
        sinal = strategy.evaluate(dados)

        assert sinal is None

    def test_dados_insuficientes_para_sma(self):
        """WHEN histórico < 15 preços THEN retorna None."""
        from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador

        strategy = GuardiaoConservador()
        dados = _make_dados([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        sinal = strategy.evaluate(dados)

        assert sinal is None


class TestGuardiaoConfig:
    """DOC: specs/guardiao-conservador — Propriedade name e parâmetros."""

    def test_nome_da_estrategia(self):
        """WHEN acessar strategy.name THEN retorna 'guardiao-conservador'."""
        from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador

        strategy = GuardiaoConservador()
        assert strategy.name == "guardiao-conservador"

    def test_periodos_padrao(self):
        """WHEN criar sem argumentos THEN short=5, long=15."""
        from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador

        strategy = GuardiaoConservador()
        assert strategy._short_period == 5
        assert strategy._long_period == 15

    def test_periodos_customizados(self):
        """WHEN criar com períodos customizados THEN usa os fornecidos."""
        from src.core.paper.domain.strategies.guardiao_conservador import GuardiaoConservador

        strategy = GuardiaoConservador(short_period=10, long_period=30)
        assert strategy._short_period == 10
        assert strategy._long_period == 30
