"""
Testes unitários para ValidadorDeOrdem.

Testa validações antes de criar ordens:
1. Saldo suficiente para compra
2. Quantidade de ativos para venda
3. Ticker válido
4. Limites de ordem (QuantityRules)
"""

import pytest
from decimal import Decimal

from src.core.paper.domain.events import OrdemCriada, Lado, EventBus
from src.core.paper.domain.services.validador_ordem import (
    ValidadorDeOrdem,
    ValidacaoError,
    MotivoRejeicao,
)
from src.core.paper.services.quantity_rules import QuantityRules
from src.core.paper.ports.data_feed_port import DataFeedPort, Cotacao


class MockDataFeedPort(DataFeedPort):
    """Mock de DataFeedPort para testes."""

    def __init__(self, tickers_validos=None):
        self.tickers_validos = tickers_validos or ["PETR4.SA", "BTC-USD", "ETH-USD"]

    async def conectar(self):
        pass

    async def desconectar(self):
        pass

    async def obter_cotacao(self, ticker: str) -> Cotacao:
        if ticker not in self.tickers_validos:
            raise ValueError(f"Ticker {ticker} não encontrado")
        return Cotacao(ticker=ticker, preco=Decimal("100"), volume=1000, timestamp="2026-03-31")

    async def obter_historico(self, ticker, periodo_dias=30):
        return []

    async def stream_cotacoes(self, tickers):
        yield

    async def validar_ticker(self, ticker: str) -> bool:
        return ticker in self.tickers_validos


class MockCashbook:
    """Mock de Cashbook para verificar saldo."""

    def __init__(self, saldo_brl=Decimal("10000")):
        from src.core.paper.domain.currency import Currency
        from src.core.paper.domain.cashbook import CashEntry

        # Usar lista mutável para permitir modificar o saldo
        self._saldo_brl = [saldo_brl]

        def _make_entry():
            return CashEntry(Currency.BRL, self._saldo_brl[0], Decimal("1.0"))

        self._entry_getter = _make_entry

    def get(self, currency):
        """Retorna CashEntry mockado."""
        from src.core.paper.domain.currency import Currency

        if currency == Currency.BRL:
            # Recria entry com saldo atual
            from src.core.paper.domain.cashbook import CashEntry
            return CashEntry(Currency.BRL, self._saldo_brl[0], Decimal("1.0"))
        # Retorna entry vazia para outras moedas
        from src.core.paper.domain.cashbook import CashEntry
        return CashEntry(currency, Decimal("0"), Decimal("0"))

    def set_saldo(self, valor):
        """Modifica o saldo (para testes)."""
        self._saldo_brl[0] = valor


class MockPosicoes:
    """Mock de Posições para verificar quantidade de ativos."""

    def __init__(self):
        self.posicoes = {}  # ticker -> quantidade

    def get_quantidade(self, ticker) -> int:
        return self.posicoes.get(ticker, 0)


class TestValidadorDeOrdem:
    """Testes para ValidadorDeOrdem."""

    @pytest.fixture
    def validador(self):
        """Cria validador com mocks."""
        datafeed = MockDataFeedPort()
        cashbook = MockCashbook(saldo_brl=Decimal("10000"))
        posicoes = MockPosicoes()
        event_bus = EventBus()
        quantity_rules = QuantityRules()

        return ValidadorDeOrdem(
            datafeed=datafeed,
            cashbook=cashbook,
            posicoes=posicoes,
            event_bus=event_bus,
            quantity_rules=quantity_rules,
        )

    @pytest.mark.asyncio
    async def test_validar_compra_sucesso(self, validador):
        """Compra com saldo suficiente deve emitir OrdemCriada."""
        received = []

        def handler(event):
            received.append(event)

        validador._event_bus.subscribe(OrdemCriada, handler)

        event = await validador.validar_e_criar_ordem(
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade=100,
            preco_limit=Decimal("25.50"),
        )

        assert len(received) == 1
        assert isinstance(received[0], OrdemCriada)
        assert received[0].ticker == "PETR4.SA"
        assert received[0].quantidade == 100

    @pytest.mark.asyncio
    async def test_validar_compra_saldo_insuficiente(self, validador):
        """Compra sem saldo deve ser rejeitada."""
        # Modifica cashbook para ter saldo baixo
        validador._cashbook.set_saldo(Decimal("100"))

        with pytest.raises(ValidacaoError) as exc:
            await validador.validar_e_criar_ordem(
                ticker="PETR4.SA",
                lado=Lado.COMPRA,
                quantidade=100,
                preco_limit=Decimal("25.50"),
            )

        assert exc.value.motivo == MotivoRejeicao.SALDO_INSUFICIENTE

    @pytest.mark.asyncio
    async def test_validar_venda_sucesso(self, validador):
        """Venda com quantidade suficiente deve emitir OrdemCriada."""
        # Adiciona posição
        validador._posicoes.posicoes["PETR4.SA"] = 200

        received = []

        def handler(event):
            received.append(event)

        validador._event_bus.subscribe(OrdemCriada, handler)

        event = await validador.validar_e_criar_ordem(
            ticker="PETR4.SA",
            lado=Lado.VENDA,
            quantidade=100,
        )

        assert len(received) == 1
        assert received[0].lado == "venda"

    @pytest.mark.asyncio
    async def test_validar_venda_sem_posicao(self, validador):
        """Venda sem quantidade deve ser rejeitada."""
        with pytest.raises(ValidacaoError) as exc:
            await validador.validar_e_criar_ordem(
                ticker="PETR4.SA",
                lado=Lado.VENDA,
                quantidade=100,
            )

        assert exc.value.motivo == MotivoRejeicao.QUANTIDADE_INSUFICIENTE

    @pytest.mark.asyncio
    async def test_validar_ticker_invalido(self, validador):
        """Ticker inválido deve ser rejeitado."""
        with pytest.raises(ValidacaoError) as exc:
            await validador.validar_e_criar_ordem(
                ticker="INVALIDO",
                lado=Lado.COMPRA,
                quantidade=100,
            )

        assert exc.value.motivo == MotivoRejeicao.TICKER_INVALIDO

    @pytest.mark.asyncio
    async def test_validar_quantidade_abaixo_minimo(self, validador):
        """Quantidade abaixo do mínimo deve ser rejeitada."""
        # PETR4.SA tem lote mínimo de 100
        with pytest.raises(ValidacaoError) as exc:
            await validador.validar_e_criar_ordem(
                ticker="PETR4.SA",
                lado=Lado.COMPRA,
                quantidade=50,  # Abaixo do lote de 100
            )

        assert exc.value.motivo == MotivoRejeicao.QUANTIDADE_ABAIXO_MINIMO

    @pytest.mark.asyncio
    async def test_validar_quantidade_acima_maximo(self, validador):
        """Quantidade acima do máximo deve ser rejeitada."""
        with pytest.raises(ValidacaoError) as exc:
            await validador.validar_e_criar_ordem(
                ticker="PETR4.SA",
                lado=Lado.COMPRA,
                quantidade=1_000_000_000,  # Acima do máximo
            )

        assert exc.value.motivo == MotivoRejeicao.QUANTIDADE_ACIMA_MAXIMO

    @pytest.mark.asyncio
    async def test_validar_crypto_precisao_correta(self, validador):
        """Crypto deve permitir precisão de 8 casas."""
        # Aumenta saldo para comprar BTC
        validador._cashbook.set_saldo(Decimal("100000"))

        received = []

        def handler(event):
            received.append(event)

        validador._event_bus.subscribe(OrdemCriada, handler)

        # BTC tem precisão de 8 casas
        event = await validador.validar_e_criar_ordem(
            ticker="BTC-USD",
            lado=Lado.COMPRA,
            quantidade=1,
            preco_limit=Decimal("50000"),
        )

        assert len(received) == 1
