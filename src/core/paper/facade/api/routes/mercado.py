# -*- coding: utf-8 -*-
"""Rotas de mercado - cotações e histórico."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ....application.queries.consultar_cotacao import ConsultarCotacaoQuery
from ....application.queries.consultar_historico import ConsultarHistoricoQuery
from ....application.handlers.consultar_cotacao_handler import ConsultarCotacaoHandler
from ....application.handlers.consultar_historico_handler import ConsultarHistoricoHandler
from ..dependencies import get_consultar_cotacao_handler, get_consultar_historico_handler
from pydantic import BaseModel


router = APIRouter(prefix="/mercado", tags=["mercado"])


# ==================== Schemas ====================


class CotacaoResponse(BaseModel):
    ticker: str
    preco: float
    variacao: float | None = None
    timestamp: str | None = None


class CandleResponse(BaseModel):
    timestamp: str
    abertura: float
    alta: float
    baixa: float
    fechamento: float
    volume: int | None = None


# ==================== Rotas ====================


@router.get(
    "/cotacao/{ticker}",
    response_model=CotacaoResponse,
    summary="Preço atual de um ativo",
)
async def get_cotacao(
    ticker: str,
    handler: ConsultarCotacaoHandler = Depends(get_consultar_cotacao_handler),
):
    """Retorna a cotação mais recente via Yahoo Finance.

    **Tickers suportados:**
    - B3: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`
    - Cripto: `BTC-USD`, `ETH-USD`, `SOL-USD`
    - EUA: `AAPL`, `MSFT`, `TSLA`
    """
    try:
        query = ConsultarCotacaoQuery(ticker=ticker.upper())
        result = await handler.handle(query)
        return CotacaoResponse(
            ticker=result.ticker,
            preco=float(result.preco),
            variacao=float(result.variacao) if result.variacao else None,
            timestamp=result.timestamp,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao buscar cotação: {e}")


@router.get(
    "/historico/{ticker}",
    response_model=List[CandleResponse],
    summary="Histórico de preços",
)
async def get_historico(
    ticker: str,
    dias: int = 30,
    handler: ConsultarHistoricoHandler = Depends(get_consultar_historico_handler),
):
    """Retorna histórico de preços (OHLCV).

    **Parâmetros:**
    - `dias`: Número de dias (1-365, padrão: 30)
    """
    if not 1 <= dias <= 365:
        raise HTTPException(status_code=400, detail="'dias' deve estar entre 1 e 365")

    try:
        query = ConsultarHistoricoQuery(ticker=ticker.upper(), dias=dias)
        result = await handler.handle(query)
        return [
            CandleResponse(
                timestamp=c.timestamp,
                abertura=float(c.abertura),
                alta=float(c.alta),
                baixa=float(c.baixa),
                fechamento=float(c.fechamento),
                volume=c.volume,
            )
            for c in result.candles
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao buscar histórico: {e}")
