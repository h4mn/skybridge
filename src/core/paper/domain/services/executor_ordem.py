"""
Executor de Ordem - Serviço de Domínio.

Orquestra a execução completa de ordens.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, Callable, Any
from enum import Enum

from ..events import (
    EventBus,
    OrdemExecutada,
    OrdemCriada,
    Lado,
)
from ...ports.broker_port import BrokerPort
from ...ports.data_feed_port import DataFeedPort
from .validador_ordem import ValidadorDeOrdem, ValidacaoError


class ExecutorResult(Enum):
    """Resultado da execução."""

    EXECUTADA = "executada"
    VALIDACAO_FALHOU = "validacao_falhou"
    ERRO_BROKER = "erro_broker"


@dataclass(frozen=True)
class ExecutionSummary:
    """
    Resumo da execução de uma ordem.

    Attributes:
        resultado: Resultado da execução
        ordem_id: ID da ordem no broker
        preco_execucao: Preço de execução
        mensagem: Mensagem de erro (se houver)
    """

    resultado: ExecutorResult
    ordem_id: str | None = None
    preco_execucao: Decimal | None = None
    mensagem: str | None = None


# Protocol para validador injetável
class ValidatorProtocol(Protocol):
    """Protocol para validador de ordens."""

    async def validar_e_criar_ordem(
        self,
        ticker: str,
        lado: Lado,
        quantidade: int,
        preco_limit: Decimal | None = None,
    ) -> OrdemCriada:
        """Valida e cria evento de ordem."""
        ...


class ExecutorDeOrdem:
    """
    Serviço de domínio que orquestra a execução completa de ordens.

    Fluxo:
    1. Validar ordem (via ValidadorDeOrdem)
    2. Obter preço atual (via DataFeedPort)
    3. Executar ordem (via BrokerPort)
    4. Emitir OrdemExecutada (via EventBus)

    Uso:
        executor = ExecutorDeOrdem(...)
        summary = await executor.executar_ordem(
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade=100
        )
    """

    def __init__(
        self,
        broker: BrokerPort,
        datafeed: DataFeedPort,
        event_bus: EventBus,
        validator: ValidatorProtocol,
    ):
        """
        Inicializa executor com dependências.

        Args:
            broker: Para executar ordens
            datafeed: Para obter cotações
            event_bus: Para emitir eventos
            validator: Para validar ordens
        """
        self._broker = broker
        self._datafeed = datafeed
        self._event_bus = event_bus
        self._validator = validator

    async def executar_ordem(
        self,
        ticker: str,
        lado: Lado,
        quantidade: int,
        preco_limit: Decimal | None = None,
    ) -> ExecutionSummary:
        """
        Executa uma ordem completa.

        Args:
            ticker: Código do ativo
            lado: COMPRA ou VENDA
            quantidade: Quantidade de ativos
            preco_limit: Preço limite (opcional)

        Returns:
            ExecutionSummary com resultado da execução

        Raises:
            ValidacaoError: Se validação falhar
        """
        # 1. Validar ordem
        try:
            evento_criada = await self._validator.validar_e_criar_ordem(
                ticker=ticker,
                lado=lado,
                quantidade=quantidade,
                preco_limit=preco_limit,
            )
        except ValidacaoError as e:
            # Validação falhou
            return ExecutionSummary(
                resultado=ExecutorResult.VALIDACAO_FALHOU,
                mensagem=str(e),
            )

        # 2. Obter preço atual (se não tiver preço limit)
        if preco_limit is None:
            cotacao = await self._datafeed.obter_cotacao(ticker)
            preco_execucao = cotacao.preco
        else:
            preco_execucao = preco_limit

        # 3. Executar ordem no broker
        try:
            lado_str = lado.value  # "compra" ou "venda"
            broker_ordem_id = await self._broker.enviar_ordem(
                ticker=ticker,
                lado=lado_str,
                quantidade=quantidade,
                preco_limite=preco_execucao,
            )
        except Exception as e:
            # Erro no broker
            return ExecutionSummary(
                resultado=ExecutorResult.ERRO_BROKER,
                mensagem=f"Erro ao executar: {e}",
            )

        # 4. Emitir OrdemExecutada
        evento_executada = OrdemExecutada(
            ordem_id=broker_ordem_id,
            ticker=ticker,
            lado=lado,
            quantidade_executada=quantidade,
            preco_execucao=preco_execucao,
        )
        self._event_bus.publish(evento_executada)

        # TODO: Atualizar posição
        # Isso seria feito via um listener de OrdemExecutada
        # que atualiza o repositório de posições

        return ExecutionSummary(
            resultado=ExecutorResult.EXECUTADA,
            ordem_id=broker_ordem_id,
            preco_execucao=preco_execucao,
        )


__all__ = [
    "ExecutorDeOrdem",
    "ExecutionSummary",
    "ExecutorResult",
]
