# -*- coding: utf-8 -*-
"""
Testes de Integração M1 - Serviços de Domínio.

Testa comunicação entre serviços M1:
- EventBus publish/subscribe entre services
- ExecutorDeOrdem orquestra Validador + Broker + DataFeed
- GeradorDeRelatorio integra com CalculadorDeRisco + PortfolioView
- Domain Events fluem entre camadas

TDD: RED → GREEN → REFACTOR
"""

from decimal import Decimal
from datetime import date
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.core.paper.domain.events import (
    EventBus,
    OrdemExecutada,
    OrdemCriada,
    Lado,
)
from src.core.paper.domain.services.validador_ordem import ValidadorDeOrdem, ValidacaoError
from src.core.paper.domain.services.executor_ordem import ExecutorDeOrdem, ExecutorResult
from src.core.paper.domain.services.calculador_risco import CalculadorDeRisco, MetricasRisco
from src.core.paper.domain.services.gerador_relatorio import GeradorDeRelatorio
from src.core.paper.domain.portfolio_view import PortfolioView, PositionView
from src.core.paper.domain.currency import Currency
from src.core.paper.domain.money import Money
from src.core.paper.domain.quantity import Quantity, AssetType
from src.core.paper.domain.cashbook import CashBook
from src.core.paper.ports.data_feed_port import DataFeedPort, Cotacao
from src.core.paper.ports.broker_port import BrokerPort


# =============================================================================
# Mocks para Ports (Infrastructure)
# =============================================================================

class MockDataFeedPort(DataFeedPort):
    """Mock de DataFeedPort para testes de integração."""

    def __init__(self, cotacoes=None):
        self.cotacoes = cotacoes or {}
        self._conectado = False

    async def conectar(self):
        self._conectado = True

    async def desconectar(self):
        self._conectado = False

    async def obter_cotacao(self, ticker):
        if ticker not in self.cotacoes:
            raise ValueError(f"Cotação não encontrada: {ticker}")
        return self.cotacoes[ticker]

    async def obter_historico(self, ticker, periodo_dias=30):
        return []

    async def stream_cotacoes(self, tickers):
        yield

    async def validar_ticker(self, ticker):
        return ticker in self.cotacoes


class MockBrokerPort(BrokerPort):
    """Mock de BrokerPort para testes de integração."""

    def __init__(self):
        self.ordens_enviadas = []
        self._conectado = False

    async def conectar(self):
        self._conectado = True

    async def desconectar(self):
        self._conectado = False

    async def enviar_ordem(self, ticker, lado, quantidade, preco_limite=None):
        ordem_id = f"broker-{len(self.ordens_enviadas)}"
        self.ordens_enviadas.append({
            "ticker": ticker,
            "lado": lado,
            "quantidade": quantidade,
            "preco_limite": preco_limite,
            "id": ordem_id,
        })
        return ordem_id

    async def cancelar_ordem(self, ordem_id):
        return True

    async def consultar_ordem(self, ordem_id):
        return {"status": "executada", "quantidade": 100}

    async def obter_saldo(self):
        return Decimal("10000")


# =============================================================================
# Testes de Integração: EventBus
# =============================================================================

class TestEventBusIntegration:
    """Testa integração via EventBus entre serviços."""

    @pytest.fixture
    def event_bus(self):
        """EventBus isolado para cada teste."""
        return EventBus()

    def test_event_bus_publish_subscribe(self, event_bus):
        """
        DOC: EventBus deve permitir publish/subscribe de eventos.

        Given: EventBus com subscriber registrado
        When: Evento OrdemExecutada é publicado
        Then: Subscriber deve receber o evento
        """
        received_events = []

        def handler(evento):
            received_events.append(evento)

        # Subscribe
        event_bus.subscribe(OrdemExecutada, handler)

        # Publish
        evento = OrdemExecutada(
            ordem_id="test-001",
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade_executada=100,
            preco_execucao=Decimal("30.00"),
        )
        event_bus.publish(evento)

        # Assert: handler recebeu evento
        assert len(received_events) == 1
        assert received_events[0].ordem_id == "test-001"
        assert received_events[0].ticker == "PETR4.SA"

    def test_event_bus_multiple_subscribers(self, event_bus):
        """
        DOC: EventBus deve notificar múltiplos subscribers.

        Given: EventBus com 3 subscribers para OrdemExecutada
        When: Evento é publicado
        Then: Todos 3 subscribers devem receber
        """
        received = {"count1": 0, "count2": 0, "count3": 0}

        def handler1(e): received["count1"] += 1
        def handler2(e): received["count2"] += 1
        def handler3(e): received["count3"] += 1

        event_bus.subscribe(OrdemExecutada, handler1)
        event_bus.subscribe(OrdemExecutada, handler2)
        event_bus.subscribe(OrdemExecutada, handler3)

        # Publish único evento
        evento = OrdemExecutada(
            ordem_id="test-001",
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade_executada=100,
            preco_execucao=Decimal("30.00"),
        )
        event_bus.publish(evento)

        # Assert: todos receberam
        assert received["count1"] == 1
        assert received["count2"] == 1
        assert received["count3"] == 1

    def test_event_bus_unsubscribe(self, event_bus):
        """
        DOC: EventBus deve permitir unsubscribe.

        Given: Subscriber registrado
        When: Unsubscribe é chamado
        Then: Subscriber não deve receber mais eventos
        """
        received = []

        def handler(e): received.append(e)

        event_bus.subscribe(OrdemExecutada, handler)
        event_bus.publish(OrdemExecutada(
            ordem_id="001", ticker="A", lado=Lado.COMPRA,
            quantidade_executada=1, preco_execucao=Decimal("1")
        ))

        # Unsubscribe
        event_bus.unsubscribe(OrdemExecutada, handler)
        event_bus.publish(OrdemExecutada(
            ordem_id="002", ticker="B", lado=Lado.COMPRA,
            quantidade_executada=1, preco_execucao=Decimal("1")
        ))

        # Assert: apenas primeiro evento recebido
        assert len(received) == 1
        assert received[0].ordem_id == "001"


# =============================================================================
# Testes de Integração: ExecutorDeOrdem + Validador + Broker + DataFeed
# =============================================================================

class TestExecutorOrdemIntegration:
    """Testa fluxo completo de execução de ordens."""

    @pytest.fixture
    def cashbook(self):
        """CashBook com saldo para testes."""
        return CashBook.from_single_currency(Currency.BRL, Decimal("10000"))

    @pytest.fixture
    def validador(self, cashbook, datafeed, event_bus):
        """Validador com dependências completas."""
        return ValidadorDeOrdem(
            datafeed=datafeed,
            cashbook=cashbook,
            posicoes=None,  # Não usado na validação básica
            event_bus=event_bus,
        )

    @pytest.fixture
    def datafeed(self):
        """DataFeed com cotações mockadas."""
        return MockDataFeedPort(cotacoes={
            "PETR4.SA": Cotacao(
                ticker="PETR4.SA",
                preco=Decimal("30.00"),
                volume=1000000,
                timestamp="2026-03-31T20:00:00",
            ),
            "VALE3.SA": Cotacao(
                ticker="VALE3.SA",
                preco=Decimal("65.00"),
                volume=2000000,
                timestamp="2026-03-31T20:00:00",
            ),
        })

    @pytest.fixture
    def broker(self):
        """Broker mock."""
        return MockBrokerPort()

    @pytest.fixture
    def event_bus(self):
        """EventBus para testes."""
        return EventBus()

    @pytest.fixture
    def executor(self, validador, datafeed, broker, event_bus):
        """Executor com dependências mockadas."""
        return ExecutorDeOrdem(
            broker=broker,
            datafeed=datafeed,
            event_bus=event_bus,
            validator=validador,
        )

    @pytest.mark.asyncio
    async def test_executor_ordem_fluxo_completo_sucesso(self, executor, broker, event_bus):
        """
        DOC: ExecutorDeOrdem deve orquestrar fluxo completo.

        Given: Executor configurado com validador, broker, datafeed
        When: Executar ordem de compra válida
        Then:
            - Validador deve validar
            - DataFeed deve fornecer preço
            - Broker deve receber ordem
            - EventBus deve publicar OrdemExecutada
        """
        # Setup: capturar eventos publicados
        received_events = []

        def handler(evento):
            received_events.append(evento)

        event_bus.subscribe(OrdemExecutada, handler)

        # WHEN: Executar ordem
        resultado = await executor.executar_ordem(
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade=100,
            preco_limit=Decimal("30.00"),
        )

        # THEN: Fluxo completo executado
        assert resultado.resultado == ExecutorResult.EXECUTADA
        assert resultado.ordem_id == "broker-0"
        assert resultado.preco_execucao == Decimal("30.00")

        # Broker recebeu ordem
        assert len(broker.ordens_enviadas) == 1
        assert broker.ordens_enviadas[0]["ticker"] == "PETR4.SA"
        assert broker.ordens_enviadas[0]["lado"] == "compra"
        assert broker.ordens_enviadas[0]["quantidade"] == 100

        # EventBus publicou evento
        assert len(received_events) == 1
        assert isinstance(received_events[0], OrdemExecutada)
        assert received_events[0].ticker == "PETR4.SA"
        assert received_events[0].quantidade_executada == 100

    @pytest.mark.asyncio
    async def test_executor_ordem_validacao_falha(self, executor, broker, event_bus):
        """
        DOC: ExecutorDeOrdem deve retornar erro quando validação falha.

        Given: Executor com validador que rejeita ordem
        When: Executar ordem com saldo insuficiente
        Then: Não deve enviar ao broker, deve retornar VALIDACAO_FALHOU
        """
        # Setup: esvaziar cashbook (saldo insuficiente)
        executor._validator._cashbook = CashBook.from_single_currency(
            Currency.BRL, Decimal("10")  # Saldo insuficiente
        )

        # WHEN: Tentar executar ordem
        resultado = await executor.executar_ordem(
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade=100,  # Vai custar 3000, só temos 10
            preco_limit=Decimal("30.00"),
        )

        # THEN: Validação falhou, ordem não enviada
        assert resultado.resultado == ExecutorResult.VALIDACAO_FALHOU
        assert resultado.ordem_id is None
        assert "saldo" in resultado.mensagem.lower()

        # Broker NÃO recebeu ordem
        assert len(broker.ordens_enviadas) == 0

    @pytest.mark.asyncio
    async def test_executor_ordem_usa_preco_datafeed_sem_limit(self, executor, datafeed):
        """
        DOC: ExecutorDeOrdem deve usar preço do DataFeed se sem limit.

        Given: Executor com datafeed retornando preço 30.00
        When: Executar ordem SEM preco_limit
        Then: Deve usar preço 30.00 do datafeed
        """
        # WHEN: Sem preço limit
        resultado = await executor.executar_ordem(
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade=100,
            # sem preco_limit
        )

        # THEN: Usou preço do datafeed
        assert resultado.resultado == ExecutorResult.EXECUTADA
        assert resultado.preco_execucao == Decimal("30.00")


# =============================================================================
# Testes de Integração: GeradorDeRelatorio + CalculadorDeRisco + PortfolioView
# =============================================================================

class TestGeradorRelatorioIntegration:
    """Testa integração entre gerador de relatórios e serviços."""

    @pytest.fixture
    def portfolio(self):
        """Portfolio com posições para testes."""
        return PortfolioView(
            positions=[
                PositionView(
                    ticker="PETR4.SA",
                    quantity=Quantity(Decimal("100"), precision=0, min_tick=Decimal("1"), asset_type=AssetType.STOCK),
                    market_price=Money(Decimal("35.00"), Currency.BRL),
                    cost_basis=Money(Decimal("30.00"), Currency.BRL),
                ),
                PositionView(
                    ticker="VALE3.SA",
                    quantity=Quantity(Decimal("200"), precision=0, min_tick=Decimal("1"), asset_type=AssetType.STOCK),
                    market_price=Money(Decimal("65.00"), Currency.BRL),
                    cost_basis=Money(Decimal("70.00"), Currency.BRL),
                ),
            ],
            base_currency=Currency.BRL,
            cash=Money(Decimal("5000"), Currency.BRL),
        )

    @pytest.fixture
    def calculador_risco(self):
        """Calculador de risco padrão."""
        return CalculadorDeRisco()

    @pytest.fixture
    def gerador(self, calculador_risco):
        """Gerador com calculador de risco injetado."""
        return GeradorDeRelatorio(calculador_risco=calculador_risco)

    def test_gerador_relatorio_calculo_completo(self, gerador, portfolio):
        """
        DOC: GeradorDeRelatorio deve integrar com CalculadorDeRisco.

        Given: Portfolio com 2 posições (PETR4: +500, VALE3: -1000)
        When: Gerar relatório de performance
        Then:
            - Patrimônio total = posições + cash
            - Métricas de risco calculadas
            - Ranking por PnL
            - Resumo PnL correto
        """
        # WHEN: Gerar relatório
        relatorio = gerador.gerar_performance(portfolio)

        # THEN: Dados integrados corretamente
        # Patrimônio: PETR4(3500) + VALE3(13000) + cash(5000) = 21500
        assert relatorio.patrimonio_total == Decimal("21500")

        # Métricas de risco
        assert isinstance(relatorio.metricas_risco, MetricasRisco)
        assert relatorio.metricas_risco.exposicao_total == Decimal("16500")  # Sem cash
        assert relatorio.metricas_risco.var_95 == Decimal("825")  # 5% de 16500

        # Concentração (2 ativos)
        assert len(relatorio.metricas_risco.concentracao) == 2
        assert "PETR4.SA" in relatorio.metricas_risco.concentracao
        assert "VALE3.SA" in relatorio.metricas_risco.concentracao

        # Ranking por PnL
        assert len(relatorio.ranking) == 2
        # PETR4: +500 (top)
        assert relatorio.ranking[0].ticker == "PETR4.SA"
        assert relatorio.ranking[0].pnl == Decimal("500")
        # VALE3: -1000 (bottom)
        assert relatorio.ranking[1].ticker == "VALE3.SA"
        assert relatorio.ranking[1].pnl == Decimal("-1000")

        # Resumo PnL
        assert relatorio.resumo_pnl.pnl_nao_realizado == Decimal("-500")  # 500 - 1000

    def test_gerador_relatorio_serializavel(self, gerador, portfolio):
        """
        DOC: Relatório deve ser serializável via to_dict().

        Given: Relatório gerado
        When: Chamar to_dict()
        Then: Retornar dict com todos os campos serializáveis
        """
        # WHEN: Gerar e serializar
        relatorio = gerador.gerar_performance(portfolio)
        dados = relatorio.to_dict()

        # THEN: Estrutura correta
        assert isinstance(dados, dict)
        assert "data" in dados
        assert "patrimonio_total" in dados
        assert "metricas_risco" in dados
        assert "ranking" in dados
        assert "resumo_pnl" in dados

        # Tipos serializáveis (não Decimal)
        assert isinstance(dados["patrimonio_total"], float)
        assert isinstance(dados["metricas_risco"]["exposicao_total"], float)
        assert isinstance(dados["ranking"][0]["pnl"], float)


# =============================================================================
# Testes de Integração: Eventos End-to-End
# =============================================================================

class TestEventFlowIntegration:
    """Testa fluxo de eventos entre componentes."""

    @pytest.fixture
    def cashbook(self):
        return CashBook.from_single_currency(Currency.BRL, Decimal("10000"))

    @pytest.fixture
    def event_bus(self):
        return EventBus()

    @pytest.fixture
    def validador(self, cashbook, datafeed, event_bus):
        return ValidadorDeOrdem(
            datafeed=datafeed,
            cashbook=cashbook,
            posicoes=None,
            event_bus=event_bus,
        )

    @pytest.fixture
    def datafeed(self):
        return MockDataFeedPort(cotacoes={
            "PETR4.SA": Cotacao("PETR4.SA", Decimal("30.00"), 1000000, "2026-03-31"),
        })

    @pytest.fixture
    def broker(self):
        return MockBrokerPort()

    @pytest.fixture
    def executor(self, validador, datafeed, broker, event_bus):
        return ExecutorDeOrdem(
            broker=broker,
            datafeed=datafeed,
            event_bus=event_bus,
            validator=validador,
        )

    @pytest.mark.asyncio
    async def test_evento_ordem_executada_flui_por_todo_sistema(self, executor, event_bus):
        """
        DOC: OrdemExecutada deve fluir via EventBus para todo sistema.

        Given: Executor configurado
        When: Executar ordem com sucesso
        Then: OrdemExecutada publicado e capturado por subscribers
        """
        # Setup: 2 subscribers (simulando diferentes componentes)
        log_risco = []
        log_cashbook = []

        def risk_handler(evento):
            log_risco.append(evento)

        def cashbook_handler(evento):
            log_cashbook.append(evento)

        event_bus.subscribe(OrdemExecutada, risk_handler)
        event_bus.subscribe(OrdemExecutada, cashbook_handler)

        # WHEN: Executar ordem
        resultado = await executor.executar_ordem(
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade=100,
            preco_limit=Decimal("30.00"),
        )

        # THEN: Ambos subscribers receberam
        assert resultado.resultado == ExecutorResult.EXECUTADA
        assert len(log_risco) == 1
        assert len(log_cashbook) == 1

        # Mesmo evento em ambos
        assert log_risco[0].ordem_id == log_cashbook[0].ordem_id
        assert log_risco[0].ordem_id == "broker-0"
