"""
Validador de Ordem - Serviço de Domínio.

Valida regras de negócio antes de criar ordens.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Protocol

from ..events import EventBus, OrdemCriada, Lado
from ..cashbook import CashEntry
from ...ports.data_feed_port import DataFeedPort
from ...services.quantity_rules import QuantityRules


class MotivoRejeicao(str, Enum):
    """Motivos pelos quais uma ordem pode ser rejeitada."""

    SALDO_INSUFICIENTE = "saldo_insuficiente"
    QUANTIDADE_INSUFICIENTE = "quantidade_insuficiente"
    TICKER_INVALIDO = "ticker_invalido"
    QUANTIDADE_ABAIXO_MINIMO = "quantidade_abaixo_minimo"
    QUANTIDADE_ACIMA_MAXIMO = "quantidade_acima_maximo"
    HORARIO_FORA_MERCADO = "horario_fora_mercado"  # Opcional


@dataclass(frozen=True)
class ValidacaoError(Exception):
    """
    Erro lançado quando uma validação falha.

    Attributes:
        motivo: Motivo da rejeição
        detalhes: Detalhes adicionais (opcional)
    """

    motivo: MotivoRejeicao
    detalhes: str | None = None

    def __str__(self):
        msg = f"Ordem rejeitada: {self.motivo.value}"
        if self.detalhes:
            msg += f" - {self.detalhes}"
        return msg


# Protocols para dependências (para desacoplamento)
class CashbookProtocol(Protocol):
    """Interface para cashbook (verificar saldo)."""

    def get(self, currency) -> CashEntry:
        """Retorna entrada de caixa para a moeda."""
        ...


class PosicoesProtocol(Protocol):
    """Interface para posições (verificar quantidade de ativos)."""

    def get_quantidade(self, ticker: str) -> int:
        """Retorna quantidade de ativos posicionados."""
        ...


class ValidadorDeOrdem:
    """
    Serviço de domínio para validar ordens antes de criar.

    Validações:
    1. Saldo suficiente para compra
    2. Quantidade de ativos para venda
    3. Ticker válido (via DataFeedPort)
    4. Limites de ordem (QuantityRules)
    5. Horário de mercado (opcional, não implementado)

    Uso:
        validador = ValidadorDeOrdem(...)
        evento = await validador.validar_e_criar_ordem(
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade=100,
            preco_limit=Decimal("25.50")
        )
    """

    def __init__(
        self,
        datafeed: DataFeedPort,
        cashbook: CashbookProtocol,
        posicoes: PosicoesProtocol,
        event_bus: EventBus,
        quantity_rules: type[QuantityRules] = QuantityRules,
    ):
        """
        Inicializa validador com dependências.

        Args:
            datafeed: Para validar ticker e obter cotações
            cashbook: Para verificar saldo
            posicoes: Para verificar quantidade de ativos
            event_bus: Para emitir OrdemCriada
            quantity_rules: Para validar limites de quantidade
        """
        self._datafeed = datafeed
        self._cashbook = cashbook
        self._posicoes = posicoes
        self._event_bus = event_bus
        self._quantity_rules = quantity_rules

    async def validar_e_criar_ordem(
        self,
        ticker: str,
        lado: Lado,
        quantidade: int,
        preco_limit: Decimal | None = None,
    ) -> OrdemCriada:
        """
        Valida e cria uma ordem.

        Args:
            ticker: Código do ativo
            lado: COMPRA ou VENDA
            quantidade: Quantidade de ativos
            preco_limit: Preço limite (opcional, para ordens limitadas)

        Returns:
            OrdemCriada emitido para o EventBus

        Raises:
            ValidacaoError: Se alguma validação falhar
        """
        # 1. Validar ticker
        await self._validar_ticker(ticker)

        # 2. Obter especificação de quantidade
        spec = self._quantity_rules.for_ticker(ticker)

        # 3. Validar limites de quantidade
        self._validar_limites_quantidade(quantidade, spec)

        # 4. Validar específico por lado
        if lado == Lado.COMPRA:
            await self._validar_compra(ticker, quantidade, preco_limit)
        else:
            self._validar_venda(ticker, quantidade)

        # 5. Criar e emitir evento
        evento = OrdemCriada(
            ordem_id=self._gerar_ordem_id(),
            ticker=ticker,
            lado=lado,
            quantidade=quantidade,
            preco_limit=preco_limit,
        )
        self._event_bus.publish(evento)

        return evento

    async def _validar_ticker(self, ticker: str) -> None:
        """Valida se ticker existe."""
        valido = await self._datafeed.validar_ticker(ticker)
        if not valido:
            raise ValidacaoError(MotivoRejeicao.TICKER_INVALIDO, f"Ticker {ticker} não encontrado")

    def _validar_limites_quantidade(self, quantidade: int, spec) -> None:
        """Valida se quantidade está dentro dos limites."""
        qty_decimal = Decimal(str(quantidade))

        if qty_decimal < spec.min_quantity:
            raise ValidacaoError(
                MotivoRejeicao.QUANTIDADE_ABAIXO_MINIMO,
                f"Mínimo é {spec.min_quantity}",
            )

        if qty_decimal > spec.max_quantity:
            raise ValidacaoError(
                MotivoRejeicao.QUANTIDADE_ACIMA_MAXIMO,
                f"Máximo é {spec.max_quantity}",
            )

    async def _validar_compra(
        self, ticker: str, quantidade: int, preco_limit: Decimal | None
    ) -> None:
        """Valida saldo suficiente para compra."""
        # Estimar custo da ordem
        if preco_limit is not None:
            custo_estimado = Decimal(str(quantidade)) * preco_limit
        else:
            # Se não tem preço limit, usa cotação atual
            cotacao = await self._datafeed.obter_cotacao(ticker)
            custo_estimado = Decimal(str(quantidade)) * cotacao.preco

        # Verificar saldo (assumindo BRL para simplicidade)
        from ..currency import Currency
        entry = self._cashbook.get(Currency.BRL)
        saldo = entry.amount
        if custo_estimado > saldo:
            raise ValidacaoError(
                MotivoRejeicao.SALDO_INSUFICIENTE,
                f"Custo {custo_estimado}, saldo {saldo}",
            )

    def _validar_venda(self, ticker: str, quantidade: int) -> None:
        """Valida quantidade de ativos para venda."""
        quantidade_posicao = self._posicoes.get_quantidade(ticker)
        if quantidade_posicao < quantidade:
            raise ValidacaoError(
                MotivoRejeicao.QUANTIDADE_INSUFICIENTE,
                f"Posição: {quantidade_posicao}, solicitado: {quantidade}",
            )

    def _gerar_ordem_id(self) -> str:
        """Gera ID único para ordem."""
        import uuid

        return f"ordem-{uuid.uuid4().hex[:8]}"


__all__ = [
    "ValidadorDeOrdem",
    "ValidacaoError",
    "MotivoRejeicao",
]
