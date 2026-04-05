"""
Testes unitários para ExecutorDeOrdem.

Testa orquestração de execução:
- Validar ordem (via ValidadorDeOrdem)
- Obter preço atual (via DataFeedPort)
- Executar ordem (via BrokerPort)
- Emitir OrdemExecutada
- Atualizar posição
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.paper.domain.events import (
    EventBus,
    OrdemExecutada,
    OrdemCriada,
    Lado,
)
from src.core.paper.domain.services.executor_ordem import ExecutorDeOrdem
from src.core.paper.ports.broker_port import BrokerPort
from src.core.paper.ports.data_feed_port import DataFeedPort, Cotacao


class MockBrokerPort(BrokerPort):
    """Mock de BrokerPort para testes."""

    def __init__(self):
        self.ordens_enviadas = []

    async def conectar(self):
        pass

    async def desconectar(self):
        pass

    async def enviar_ordem(self, ticker, lado, quantidade, preco_limite=None):
        ordem_id = f"broker-{len(self.ordens_enviadas)}"
        self.ordens_enviadas.append(
            {
                "ticker": ticker,
                "lado": lado,
                "quantidade": quantidade,
                "preco_limite": preco_limite,
                "id": ordem_id,
            }
        )
        return ordem_id

    async def cancelar_ordem(self, ordem_id):
        return True

    async def consultar_ordem(self, ordem_id):
        return {"status": "executada", "quantidade": 100}

    async def obter_saldo(self):
        return Decimal("10000")


class MockDataFeedPort(DataFeedPort):
    """Mock de DataFeedPort para testes."""

    def __init__(self, cotacoes=None):
        self.cotacoes = cotacoes or {}

    async def conectar(self):
        pass

    async def desconectar(self):
        pass

    async def obter_cotacao(self, ticker):
        if ticker not in self.cotacoes:
            raise ValueError(f"Ticker {ticker} não encontrado")
        return self.cotacoes[ticker]

    async def obter_historico(self, ticker, periodo_dias=30):
        return []

    async def stream_cotacoes(self, tickers):
        yield

    async def validar_ticker(self, ticker):
        return ticker in self.cotacoes


class TestExecutorDeOrdem:
    """Testes para ExecutorDeOrdem."""

    @pytest.fixture
    def executor(self):
        """Cria executor com mocks."""
        broker = MockBrokerPort()
        datafeed = MockDataFeedPort(
            cotacoes={
                "PETR4.SA": Cotacao(
                    ticker="PETR4.SA",
                    preco=Decimal("30.00"),
                    volume=1000,
                    timestamp="2026-03-31",
                )
            }
        )
        event_bus = EventBus()

        # Mock para validador (retorna OrdemCriada)
        async def mock_validator(*args, **kwargs):
            evento = OrdemCriada(
                ordem_id="test-001",
                ticker="PETR4.SA",
                lado=Lado.COMPRA,
                quantidade=100,
                preco_limit=Decimal("30.00"),
            )
            return evento

        validator = AsyncMock(side_effect=mock_validator)

        return ExecutorDeOrdem(
            broker=broker,
            datafeed=datafeed,
            event_bus=event_bus,
            validator=validator,
        )

    @pytest.mark.asyncio
    async def test_executar_ordem_compra_sucesso(self, executor):
        """Executar ordem de compra com sucesso."""
        received_events = []

        def handler(event):
            received_events.append(event)

        executor._event_bus.subscribe(OrdemExecutada, handler)

        resultado = await executor.executar_ordem(
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade=100,
            preco_limit=Decimal("30.00"),
        )

        # Verifica que ordem foi enviada ao broker
        assert len(executor._broker.ordens_enviadas) == 1
        ordem_enviada = executor._broker.ordens_enviadas[0]
        assert ordem_enviada["ticker"] == "PETR4.SA"
        assert ordem_enviada["lado"] == "compra"
        assert ordem_enviada["quantidade"] == 100

        # Verifica que OrdemExecutada foi emitida
        assert len(received_events) == 1
        assert isinstance(received_events[0], OrdemExecutada)
        assert received_events[0].ticker == "PETR4.SA"

    @pytest.mark.asyncio
    async def test_executar_ordem_usa_preco_atual_sem_limit(self, executor):
        """Sem preço limit, usa cotação atual."""
        resultado = await executor.executar_ordem(
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade=100,
            # sem preco_limit
        )

        # Deve usar preço da cotação (30.00)
        ordem_enviada = executor._broker.ordens_enviadas[0]
        assert ordem_enviada["preco_limite"] == Decimal("30.00")

    @pytest.mark.asyncio
    async def test_executar_ordem_venda_sucesso(self, executor):
        """Executar ordem de venda com sucesso."""
        resultado = await executor.executar_ordem(
            ticker="PETR4.SA",
            lado=Lado.VENDA,
            quantidade=50,
        )

        assert len(executor._broker.ordens_enviadas) == 1
        ordem_enviada = executor._broker.ordens_enviadas[0]
        assert ordem_enviada["lado"] == "venda"
        assert ordem_enviada["quantidade"] == 50
