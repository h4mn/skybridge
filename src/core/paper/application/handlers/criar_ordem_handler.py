# -*- coding: utf-8 -*-
"""Handler para processar CriarOrdemCommand."""
from dataclasses import dataclass

from ..commands.criar_ordem import CriarOrdemCommand
from ...ports.broker_port import BrokerPort


@dataclass
class OrdemResult:
    """Resultado da execução de uma ordem."""
    id: str
    ticker: str
    lado: str
    quantidade: int
    preco_execucao: float
    valor_total: float
    status: str
    timestamp: str


class CriarOrdemHandler:
    """Handler para processar comandos de criação de ordem.

    Encapsula a lógica de validação e execução de ordens,
    delegando a execução real para o BrokerPort.
    """

    def __init__(self, broker: BrokerPort):
        self._broker = broker

    async def handle(self, command: CriarOrdemCommand) -> OrdemResult:
        """Processa o command de criação de ordem.

        Args:
            command: Command com dados da ordem

        Returns:
            OrdemResult com dados da ordem executada

        Raises:
            SaldoInsuficienteError: Se saldo insuficiente para compra
            ValueError: Se posição insuficiente para venda
        """
        # Executa a ordem via broker
        ordem_id = await self._broker.enviar_ordem(
            ticker=command.ticker,
            lado=command.lado,
            quantidade=command.quantidade,
            preco_limite=command.preco_limite,
        )

        # Consulta ordem executada para retornar resultado completo
        ordem = await self._broker.consultar_ordem(ordem_id)

        return OrdemResult(
            id=ordem["id"],
            ticker=ordem["ticker"],
            lado=ordem["lado"],
            quantidade=ordem["quantidade"],
            preco_execucao=ordem["preco_execucao"],
            valor_total=ordem["valor_total"],
            status=ordem["status"],
            timestamp=ordem["timestamp"],
        )
