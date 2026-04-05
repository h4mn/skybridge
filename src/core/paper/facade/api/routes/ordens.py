# -*- coding: utf-8 -*-
"""Rotas de Ordens - Paper Trading API.

Endpoints para gerenciamento de ordens de compra/venda.
"""
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ....application.commands.criar_ordem import CriarOrdemCommand
from ....application.queries.consultar_ordens import ConsultarOrdensQuery
from ....application.handlers.criar_ordem_handler import CriarOrdemHandler
from ....application.handlers.consultar_ordens_handler import ConsultarOrdensHandler
from ..dependencies import get_criar_ordem_handler, get_consultar_ordens_handler
from ....adapters.brokers import SaldoInsuficienteError


router = APIRouter(prefix="/ordens", tags=["trading"])


# ==================== Schemas ====================


class CriarOrdemRequest(BaseModel):
    ticker: str
    lado: str  # "COMPRA" ou "VENDA"
    quantidade: int
    preco_limite: Optional[float] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"ticker": "PETR4.SA", "lado": "COMPRA", "quantidade": 100},
                {"ticker": "BTC-USD", "lado": "COMPRA", "quantidade": 1},
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


class OrdensListResponse(BaseModel):
    ordens: List[OrdemResponse]
    total: int


# ==================== Rotas ====================


@router.post(
    "/",
    response_model=OrdemResponse,
    summary="Criar ordem de compra ou venda",
)
async def criar_ordem(
    req: CriarOrdemRequest,
    handler: CriarOrdemHandler = Depends(get_criar_ordem_handler),
):
    """Executa uma ordem paper ao preço de mercado atual.

    O preço de execução é buscado em tempo real no Yahoo Finance.
    O saldo é debitado (compra) ou creditado (venda) automaticamente.
    """
    try:
        command = CriarOrdemCommand(
            ticker=req.ticker,
            lado=req.lado.upper(),
            quantidade=req.quantidade,
            preco_limite=Decimal(str(req.preco_limite)) if req.preco_limite else None,
        )
        result = await handler.handle(command)
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


@router.get(
    "/",
    response_model=OrdensListResponse,
    summary="Listar ordens executadas",
)
async def listar_ordens(
    ticker: Optional[str] = None,
    lado: Optional[str] = None,
    status: Optional[str] = None,
    limite: Optional[int] = None,
    handler: ConsultarOrdensHandler = Depends(get_consultar_ordens_handler),
):
    """Lista ordens do portfolio com filtros opcionais.

    **Filtros:**
    - `ticker`: Filtrar por ativo
    - `lado`: Filtrar por COMPRA ou VENDA
    - `status`: Filtrar por status
    - `limite`: Limitar quantidade de resultados
    """
    try:
        query = ConsultarOrdensQuery(
            ticker=ticker.upper() if ticker else None,
            lado=lado.upper() if lado else None,
            status=status,
            limite=limite,
        )
        result = await handler.handle(query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return OrdensListResponse(
        ordens=[
            OrdemResponse(
                ordem_id=o.id,
                ticker=o.ticker,
                lado=o.lado,
                quantidade=o.quantidade,
                preco_execucao=o.preco_execucao,
                valor_total=o.valor_total,
                status=o.status,
                timestamp=o.timestamp,
            )
            for o in result.ordens
        ],
        total=result.total,
    )
