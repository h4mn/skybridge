"""
Porta do Broker - Paper Trading

Define a interface para execução de ordens em brokers.
Implementações podem ser Paper Broker (simulação) ou brokers reais.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional


class BrokerPort(ABC):
    """
    Interface para execução de ordens em brokers.

    Implementações:
    - PaperBroker: Simula execução de ordens
    - BinanceAdapter: Conecta com Binance
    - XPAdapter: Conecta com XP Investimentos
    """

    @abstractmethod
    async def conectar(self) -> None:
        """Estabelece conexão com o broker."""
        pass

    @abstractmethod
    async def desconectar(self) -> None:
        """Encerra conexão com o broker."""
        pass

    @abstractmethod
    async def enviar_ordem(
        self,
        ticker: str,
        lado: str,  # "COMPRA" ou "VENDA"
        quantidade: int,
        preco_limite: Optional[Decimal] = None,
    ) -> str:
        """
        Envia uma ordem para o broker.

        Args:
            ticker: Código do ativo (ex: "PETR4")
            lado: Direção da operação ("COMPRA" ou "VENDA")
            quantidade: Número de unidades
            preco_limite: Preço limite (None = mercado)

        Returns:
            ID da ordem criada

        Raises:
            BrokerError: Se falhar ao enviar ordem
        """
        pass

    @abstractmethod
    async def cancelar_ordem(self, ordem_id: str) -> bool:
        """
        Cancela uma ordem existente.

        Args:
            ordem_id: ID da ordem a cancelar

        Returns:
            True se cancelada com sucesso

        Raises:
            OrdemNaoEncontradaError: Se ordem não existir
        """
        pass

    @abstractmethod
    async def consultar_ordem(self, ordem_id: str) -> dict:
        """
        Consulta status de uma ordem.

        Args:
            ordem_id: ID da ordem

        Returns:
            Dicionário com status, quantidade executada, preço médio, etc.
        """
        pass

    @abstractmethod
    async def obter_saldo(self) -> Decimal:
        """
        Obtém saldo disponível na conta.

        Returns:
            Saldo disponível para operação
        """
        pass
