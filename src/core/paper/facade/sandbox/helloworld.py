# -*- coding: utf-8 -*-
"""Facade Sandbox - Playground de paper trading com dados reais."""
from decimal import Decimal
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ...application.commands.criar_ordem import CriarOrdemCommand
from ...application.handlers.criar_ordem_handler import CriarOrdemHandler
from ...application.handlers.consultar_cotacao_handler import ConsultarCotacaoHandler
from ...application.handlers.consultar_historico_handler import ConsultarHistoricoHandler
from ...application.handlers.consultar_portfolio_handler import ConsultarPortfolioHandler
from ...adapters.currency.yahoo_currency_adapter import YahooCurrencyAdapter
from ...ports.currency_converter_port import CurrencyConverterPort
from ...application.handlers.consultar_ordens_handler import ConsultarOrdensHandler
from ...application.queries.consultar_cotacao import ConsultarCotacaoQuery
from ...application.queries.consultar_historico import ConsultarHistoricoQuery
from ...adapters.data_feeds.yahoo_finance_feed import YahooFinanceFeed
from ...adapters.brokers.json_file_broker import JsonFilePaperBroker
from ...adapters.persistence.json_file_paper_state import JsonFilePaperState
from ...adapters.brokers import SaldoInsuficienteError


# ── Schemas ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    message: str


class CotacaoResponse(BaseModel):
    ticker: str
    preco: float
    volume: int
    timestamp: str


class CandleResponse(BaseModel):
    timestamp: str
    preco_fechamento: float
    volume: int


class OrdemRequest(BaseModel):
    ticker: str
    lado: str        # "COMPRA" ou "VENDA"
    quantidade: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"ticker": "PETR4.SA", "lado": "COMPRA", "quantidade": 100},
                {"ticker": "BTC-USD",  "lado": "COMPRA", "quantidade": 1},
            ]
        }
    }


class OrdemResponse(BaseModel):
    ordem_id: str
    ticker: str
    lado: str
    quantidade: int
    preco_execucao: float
    valor_total: float
    status: str
    timestamp: str


class PosicaoResponse(BaseModel):
    ticker: str
    quantidade: int
    preco_medio: float
    preco_atual: float
    custo_total: float
    valor_atual: float
    pnl: float
    pnl_percentual: float


class PortfolioResponse(BaseModel):
    saldo_inicial: float
    saldo_disponivel: float
    valor_posicoes: float
    patrimonio_total: float
    pnl: float
    pnl_percentual: float
    posicoes: List[PosicaoResponse]


# ── Facade ────────────────────────────────────────────────────────────────────

class HelloWorldFacade:
    """Facade HelloWorld — playground de paper trading com dados reais.

    Endpoints:
        GET  /cotacao/{ticker}   → preço real via Yahoo Finance
        GET  /historico/{ticker} → histórico diário (param: ?dias=30)
        POST /ordem              → executa compra ou venda paper
        GET  /posicoes           → carteira marcada a mercado
        GET  /portfolio          → resumo completo com PnL real
        GET  /ordens             → histórico de ordens executadas
    """

    SALDO_INICIAL = Decimal("100000")

    def __init__(self):
        # Infraestrutura
        self.feed = YahooFinanceFeed()
        self.paper_state = JsonFilePaperState("paper_state.json")
        self.broker = JsonFilePaperBroker(
            feed=self.feed,
            paper_state=self.paper_state,
            saldo_inicial=self.SALDO_INICIAL,
        )
        self.converter = YahooCurrencyAdapter()

        # Handlers (Application Layer)
        self.criar_ordem_handler = CriarOrdemHandler(self.broker)
        self.consultar_cotacao_handler = ConsultarCotacaoHandler(self.feed)
        self.consultar_historico_handler = ConsultarHistoricoHandler(self.feed)
        self.consultar_portfolio_handler = ConsultarPortfolioHandler(
            self.broker, self.feed, self.converter
        )
        self.consultar_ordens_handler = ConsultarOrdensHandler(self.broker, self.paper_state)

        # FastAPI App
        self.app = FastAPI(
            title="Paper Trading — Hello World Playground",
            description=(
                "Dados reais de mercado + paper trading em memória.\n\n"
                "**Tickers B3:** `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`, `BBDC4.SA`\n\n"
                "**Cripto:** `BTC-USD`, `ETH-USD`, `SOL-USD`\n\n"
                "**EUA:** `AAPL`, `MSFT`, `TSLA`\n\n"
                f"Saldo inicial: R$ {float(self.SALDO_INICIAL):,.0f}"
            ),
            version="0.4.0",
        )
        self._setup_routes()

    def _setup_routes(self):

        @self.app.on_event("startup")
        async def startup():
            await self.feed.conectar()

        @self.app.on_event("shutdown")
        async def shutdown():
            await self.feed.desconectar()

        # ── Meta ─────────────────────────────────────────────────────────────

        @self.app.get("/", response_model=HealthResponse, tags=["meta"])
        async def root():
            return HealthResponse(
                status="ok",
                message="Paper Trading Playground — dados reais, dinheiro fictício",
            )

        @self.app.get("/health", response_model=HealthResponse, tags=["meta"])
        async def health():
            return HealthResponse(status="healthy", message="rodando")

        # ── Mercado ──────────────────────────────────────────────────────────

        @self.app.get(
            "/cotacao/{ticker}",
            response_model=CotacaoResponse,
            tags=["mercado"],
            summary="Preço atual de um ativo",
        )
        async def get_cotacao(ticker: str):
            """Retorna a cotação mais recente via Yahoo Finance.

            - B3: `PETR4.SA`, `VALE3.SA`
            - Cripto: `BTC-USD`, `ETH-USD`
            - EUA: `AAPL`, `TSLA`
            """
            try:
                query = ConsultarCotacaoQuery(ticker=ticker.upper())
                result = await self.consultar_cotacao_handler.handle(query)
                # Busca volume diretamente do feed (não está no CotacaoResult ainda)
                c = await self.feed.obter_cotacao(ticker.upper())
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Erro ao buscar dados: {e}")
            return CotacaoResponse(
                ticker=result.ticker,
                preco=float(result.preco),
                volume=c.volume,
                timestamp=result.timestamp or c.timestamp,
            )

        @self.app.get(
            "/historico/{ticker}",
            response_model=List[CandleResponse],
            tags=["mercado"],
            summary="Histórico de fechamentos diários",
        )
        async def get_historico(ticker: str, dias: int = 30):
            """Retorna os últimos N dias de fechamento (padrão: 30).

            Use `?dias=7` para uma semana, `?dias=90` para 3 meses.
            """
            if not 1 <= dias <= 365:
                raise HTTPException(
                    status_code=400, detail="'dias' deve estar entre 1 e 365."
                )
            try:
                query = ConsultarHistoricoQuery(ticker=ticker.upper(), dias=dias)
                result = await self.consultar_historico_handler.handle(query)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Erro ao buscar histórico: {e}")
            return [
                CandleResponse(
                    timestamp=c.timestamp,
                    preco_fechamento=float(c.fechamento),
                    volume=c.volume,
                )
                for c in result.candles
            ]

        # ── Trading ──────────────────────────────────────────────────────────

        @self.app.post(
            "/ordem",
            response_model=OrdemResponse,
            tags=["trading"],
            summary="Executar ordem de compra ou venda",
        )
        async def post_ordem(req: OrdemRequest):
            """Executa uma ordem paper ao preço de mercado atual.

            O preço de execução é buscado em tempo real no Yahoo Finance.
            O saldo é debitado (compra) ou creditado (venda) automaticamente.
            """
            try:
                command = CriarOrdemCommand(
                    ticker=req.ticker,
                    lado=req.lado,
                    quantidade=req.quantidade,
                )
                result = await self.criar_ordem_handler.handle(command)
            except SaldoInsuficienteError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Erro ao executar ordem: {e}")

            return OrdemResponse(
                ordem_id=result.id,
                ticker=result.ticker,
                lado=result.lado,
                quantidade=result.quantidade,
                preco_execucao=result.preco_execucao,
                valor_total=result.valor_total,
                status=result.status,
                timestamp=result.timestamp,
            )

        @self.app.get(
            "/posicoes",
            response_model=List[PosicaoResponse],
            tags=["trading"],
            summary="Carteira atual marcada a mercado",
        )
        async def get_posicoes():
            """Lista todas as posições abertas com PnL calculado ao preço atual."""
            try:
                posicoes = await self.broker.listar_posicoes_marcadas()
            except Exception as e:
                raise HTTPException(status_code=502, detail=str(e))
            return [PosicaoResponse(**p) for p in posicoes]

        @self.app.get(
            "/portfolio",
            response_model=PortfolioResponse,
            tags=["trading"],
            summary="Resumo completo do portfolio",
        )
        async def get_portfolio():
            """Portfolio completo: saldo + posições marcadas a mercado + PnL total."""
            try:
                posicoes = await self.broker.listar_posicoes_marcadas()
            except Exception as e:
                raise HTTPException(status_code=502, detail=str(e))

            saldo_disponivel = float(self.broker.saldo)
            valor_posicoes = sum(p["valor_atual"] for p in posicoes)
            patrimonio_total = saldo_disponivel + valor_posicoes
            pnl = patrimonio_total - float(self.SALDO_INICIAL)
            pnl_pct = (pnl / float(self.SALDO_INICIAL)) * 100

            return PortfolioResponse(
                saldo_inicial=self.SALDO_INICIAL,
                saldo_disponivel=round(saldo_disponivel, 2),
                valor_posicoes=round(valor_posicoes, 2),
                patrimonio_total=round(patrimonio_total, 2),
                pnl=round(pnl, 2),
                pnl_percentual=round(pnl_pct, 2),
                posicoes=[PosicaoResponse(**p) for p in posicoes],
            )

        @self.app.get(
            "/ordens",
            response_model=List[OrdemResponse],
            tags=["trading"],
            summary="Histórico de ordens executadas",
        )
        async def get_ordens():
            """Retorna todas as ordens executadas nesta sessão."""
            return [
                OrdemResponse(**{**o, "ordem_id": o["id"]})
                for o in self.broker.listar_ordens()
            ]


# ── Entry point ───────────────────────────────────────────────────────────────

def create_hello_world_app() -> FastAPI:
    facade = HelloWorldFacade()
    return facade.app


app = create_hello_world_app()
