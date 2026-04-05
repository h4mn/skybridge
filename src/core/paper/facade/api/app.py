# -*- coding: utf-8 -*-
"""
Paper Trading API - FastAPI Application.

Aplicação FastAPI para o módulo de paper trading.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import mercado, ordens, portfolio
from .dependencies import get_feed


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    # Startup
    feed = get_feed()
    await feed.conectar()
    yield
    # Shutdown
    await feed.desconectar()


def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI."""
    app = FastAPI(
        title="Paper Trading API",
        description=(
            "API REST para paper trading com dados de mercado reais.\n\n"
            "**Funcionalidades:**\n"
            "- Consulta de cotações em tempo real (Yahoo Finance)\n"
            "- Histórico de preços\n"
            "- Execução de ordens paper\n"
            "- Gestão de portfolio com PnL\n\n"
            "**Tickers suportados:**\n"
            "- B3: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`\n"
            "- Cripto: `BTC-USD`, `ETH-USD`\n"
            "- EUA: `AAPL`, `MSFT`, `TSLA`"
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Registra rotas
    app.include_router(mercado.router, prefix="/api/v1/paper")
    app.include_router(ordens.router, prefix="/api/v1/paper")
    app.include_router(portfolio.router, prefix="/api/v1/paper")

    # Health check
    @app.get("/health", tags=["meta"])
    async def health():
        return {"status": "healthy", "service": "paper-trading-api"}

    return app


# Instância padrão para uvicorn
app = create_app()
