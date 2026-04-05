# -*- coding: utf-8 -*-
"""
Domain Layer - MercadoSimulado.

Simula movimento de mercado com preços realistas baseados em dados Binance:

Value Objects:
- Ticker: Código do ativo
- PrecoSimulado: Preço em determinado momento

Enum:
- Volatilidade: Nível de variação de preço
- MovimentoMercado: Direção do movimento (alta/baixa/lateral)

Entity:
- MercadoSimulado: Simula mercado para um ticker

Service:
- GeradorDePrecos: Gera preços para múltiplos tickers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Callable
import random


# ═══════════════════════════════════════════════════════════════════════
# Value Objects
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Ticker:
    """
    Código de um ativo.

    Attributes:
        value: Símbolo do ticker (ex: "BTC-USD", "PETR4.SA")
    """

    value: str

    def __post_init__(self):
        """Valida que value não é vazio."""
        if not self.value or not self.value.strip():
            raise ValueError("Ticker não pode ser vazio")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PrecoSimulado:
    """
    Preço simulado em determinado momento.

    Attributes:
        ticker: Ticker do ativo
        valor: Preço simulado
        timestamp: Momento da geração
    """

    ticker: Ticker
    valor: Decimal
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Converte para dict serializável."""
        return {
            "ticker": self.ticker.value,
            "valor": str(self.valor),
            "timestamp": self.timestamp.isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════

class Volatilidade(str, Enum):
    """
    Nível de volatilidade do mercado.

    Define a variação máxima percentual permitida.
    """

    BAIXA = "baixa"      # 1%  - Ações estáveis, ETFs
    MEDIA = "media"      # 3%  - Ações comuns, crypto em calmaria
    ALTA = "alta"        # 8%  - Crypto volátil, small caps
    EXTREMA = "extrema"  # 20% - Memecoins, penny stocks

    @property
    def variacao_maxima(self) -> Decimal:
        """Variação máxima percentual (decimal)."""
        return {
            Volatilidade.BAIXA: Decimal("0.01"),
            Volatilidade.MEDIA: Decimal("0.03"),
            Volatilidade.ALTA: Decimal("0.08"),
            Volatilidade.EXTREMA: Decimal("0.20"),
        }[self]

    @classmethod
    def from_ticker(cls, ticker: Ticker) -> "Volatilidade":
        """
        Infer volatilidade baseada no ticker.

        Args:
            ticker: Ticker para analisar

        Returns:
            Volatilidade estimada
        """
        value = ticker.value.upper()

        # Crypto tem volatilidade ALTA por padrão
        if any(crypto in value for crypto in ["BTC", "ETH", "SOL", "XRP"]):
            return Volatilidade.ALTA

        # Ações brasileiras têm volatilidade MEDIA
        if ".SA" in value:
            return Volatilidade.MEDIA

        # Padrão: MEDIA
        return Volatilidade.MEDIA


class MovimentoMercado(str, Enum):
    """
    Direção do movimento de mercado.

    Usado para gerar preços com tendência específica.
    """

    ALTA = "alta"        # Tendência de alta
    BAIXA = "baixa"      # Tendência de baixa
    LATERAL = "lateral"  # Sem tendência definida

    def aplicar(self, preco: Decimal, variacao: Decimal) -> Decimal:
        """
        Aplica movimento ao preço.

        Args:
            preco: Preço atual
            variacao: Variação percentual (ex: 0.05 = 5%)

        Returns:
            Novo preço com movimento aplicado
        """
        if self == MovimentoMercado.ALTA:
            # Alta: preço aumenta (0 a +variação)
            fator = Decimal("1") + (Decimal(random.random()) * variacao)
            return preco * fator

        elif self == MovimentoMercado.BAIXA:
            # Baixa: preço diminui (0 a -variação)
            fator = Decimal("1") - (Decimal(random.random()) * variacao)
            return preco * fator

        else:  # LATERAL
            # Lateral: movimento aleatório pequeno (±variação/2)
            direcao = 1 if random.random() > 0.5 else -1
            fator = Decimal("1") + (Decimal(random.random()) * variacao / 2 * direcao)
            return preco * fator


# ═══════════════════════════════════════════════════════════════════════
# Entity
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class MercadoSimulado:
    """
    Simulador de mercado para um ticker.

    Gera preços realistas baseados em:
    - Preço inicial
    - Volatilidade configurável
    - Random walk com tendência

    Attributes:
        ticker: Ticker do ativo
        preco_inicial: Preço base para simulação
        volatilidade: Nível de variação
        _historico: Histórico de preços gerados
    """

    ticker: Ticker
    preco_inicial: Decimal
    volatilidade: Volatilidade
    _historico: list[PrecoSimulado] = field(default_factory=list)
    _preco_atual: Decimal | None = None

    def __post_init__(self):
        """Inicializa preço atual."""
        if self._preco_atual is None:
            self._preco_atual = self.preco_inicial

    @property
    def preco_atual(self) -> Decimal:
        """Preço atual do mercado."""
        return self._preco_atual

    @property
    def historico(self) -> list[PrecoSimulado]:
        """Histórico de preços gerados."""
        return self._historico.copy()

    def gerar_proximo_preco(self, movimento: MovimentoMercado | None = None) -> PrecoSimulado:
        """
        Gera próximo preço simulado.

        Args:
            movimento: Tendência opcional (alta/baixa/lateral)

        Returns:
            PrecoSimulado gerado
        """
        # Usa volatilidade configurada
        variacao_max = self.volatilidade.variacao_maxima

        # Define movimento (aleatório se não especificado)
        if movimento is None:
            movimento = random.choice([MovimentoMercado.ALTA, MovimentoMercado.BAIXA, MovimentoMercado.LATERAL])

        # Aplica movimento ao preço
        novo_valor = movimento.aplicar(self._preco_atual, variacao_max)

        # Garante que preço não é negativo
        novo_valor = max(novo_valor, Decimal("0.01"))

        # Atualiza preço atual
        self._preco_atual = novo_valor

        # Cria PrecoSimulado
        preco = PrecoSimulado(
            ticker=self.ticker,
            valor=novo_valor,
        )

        # Adiciona ao histórico
        self._historico.append(preco)

        return preco

    def resetar(self) -> None:
        """Reseta simulação para preço inicial."""
        self._preco_atual = self.preco_inicial
        self._historico.clear()


# ═══════════════════════════════════════════════════════════════════════
# Service
# ═══════════════════════════════════════════════════════════════════════

class GeradorDePrecos:
    """
    Serviço para gerar preços simulados.

    Responsabilidades:
    - Gerar preços para tickers individuais
    - Gerar lotes de preços para múltiplos tickers
    - Usar preços base realistas (Binance)

    Attributes:
        seed: Semente para aleatoriedade (opcional)
    """

    def __init__(self, seed: int | None = None):
        """
        Inicializa gerador.

        Args:
            seed: Semente para reproducibilidade (opcional)
        """
        if seed is not None:
            random.seed(seed)

    def gerar_para_ticker(
        self,
        ticker: Ticker,
        preco_base: Decimal,
        volatilidade: Volatilidade | None = None,
    ) -> PrecoSimulado:
        """
        Gera preço simulado para um ticker.

        Args:
            ticker: Ticker do ativo
            preco_base: Preço base
            volatilidade: Nível de variação (usa inferência se None)

        Returns:
            PrecoSimulado gerado
        """
        # Infer volatilidade se não especificada
        if volatilidade is None:
            volatilidade = Volatilidade.from_ticker(ticker)

        # Cria mercado simulado temporário
        mercado = MercadoSimulado(
            ticker=ticker,
            preco_inicial=preco_base,
            volatilidade=volatilidade,
        )

        # Gera um preço
        return mercado.gerar_proximo_preco()

    def gerar_lote(
        self,
        tickers: list[Ticker],
        precos_base: dict[Ticker, Decimal],
        volatilidade: Volatilidade | None = None,
    ) -> list[PrecoSimulado]:
        """
        Gera lote de preços para múltiplos tickers.

        Args:
            tickers: Lista de tickers
            precos_base: Dict mapeando Ticker → preco base
            volatilidade: Volatilidade única para todos (ou None por ticker)

        Returns:
            Lista de PrecoSimulado
        """
        lotes = []

        for ticker in tickers:
            # Busca preço base
            if ticker not in precos_base:
                continue

            # Volatilidade específica ou global
            vol = volatilidade if volatilidade is not None else Volatilidade.from_ticker(ticker)

            # Gera preço
            preco = self.gerar_para_ticker(
                ticker=ticker,
                preco_base=precos_base[ticker],
                volatilidade=vol,
            )

            lotes.append(preco)

        return lotes


__all__ = [
    # Value Objects
    "Ticker",
    "PrecoSimulado",
    # Enums
    "Volatilidade",
    "MovimentoMercado",
    # Entity
    "MercadoSimulado",
    # Service
    "GeradorDePrecos",
]
