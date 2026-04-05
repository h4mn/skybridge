# -*- coding: utf-8 -*-
"""Rotas de Portfolio - Paper Trading API.

Endpoints para consulta e gerenciamento de portfolio.
"""
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ....application.commands.depositar import DepositarCommand
from ....application.commands.resetar import ResetarCommand
from ....application.handlers.depositar_handler import DepositarHandler
from ....application.handlers.resetar_handler import ResetarHandler
from ....application.handlers.consultar_portfolio_handler import ConsultarPortfolioHandler
from ..dependencies import (
    get_depositar_handler,
    get_resetar_handler,
    get_consultar_portfolio_handler,
    get_broker,
    get_currency_converter,
)
from ....adapters.brokers.json_file_broker import JsonFilePaperBroker

if TYPE_CHECKING:
    from ....ports.currency_converter_port import CurrencyConverterPort


router = APIRouter(prefix="/portfolio", tags=["trading"])


# ==================== Schemas ====================


class CashEntryResponse(BaseModel):
    """Saldo em uma moeda específica."""
    currency: str
    amount: float
    conversion_rate: float
    value_in_base_currency: float


class CashbookResponse(BaseModel):
    """Cashbook multi-moeda."""
    base_currency: str
    entries: list[CashEntryResponse]
    total_in_base_currency: float


class PortfolioResponse(BaseModel):
    saldo_inicial: float
    saldo_disponivel: float
    valor_posicoes: float
    patrimonio_total: float
    pnl: float
    pnl_percentual: float
    currency: str = "BRL"  # Moeda do resultado
    cashbook: CashbookResponse  # Detalhamento por moeda


class PosicaoResponse(BaseModel):
    ticker: str
    quantidade: int
    preco_medio: float
    preco_atual: float
    custo_total: float
    valor_atual: float
    pnl: float
    pnl_percentual: float
    currency: str = "BRL"  # Moeda da posição


class DepositoRequest(BaseModel):
    valor: float
    currency: str = "BRL"  # Moeda do depósito (opcional)


class DepositoResponse(BaseModel):
    saldo_anterior: float
    valor_depositado: float
    saldo_atual: float
    currency: str  # Moeda do depósito


class ResetResponse(BaseModel):
    saldo_anterior: float
    saldo_novo: float
    ordens_removidas: int
    posicoes_removidas: int


# ==================== Rotas ====================


@router.get(
    "/",
    response_model=PortfolioResponse,
    summary="Consultar portfolio",
)
async def consultar_portfolio(
    base_currency: Optional[str] = Query(
        None,
        description="Moeda base para consolidação (BRL, USD, EUR, GBP, BTC, ETH)",
        examples=["BRL", "USD"],
    ),
    handler: ConsultarPortfolioHandler = Depends(get_consultar_portfolio_handler),
    broker: JsonFilePaperBroker = Depends(get_broker),
):
    """Retorna resumo completo do portfolio com PnL calculado.

    **Parâmetros:**
    - `base_currency`: Moeda para consolidar o portfolio (opcional)
      - Se não informado, retorna em BRL (moeda nativa)
      - Valores aceitos: BRL, USD, EUR, GBP, BTC, ETH

    **Exemplo:**
    - `GET /portfolio?base_currency=USD` - Retorna tudo convertido para USD
    """
    from ....application.queries.consultar_portfolio import ConsultarPortfolioQuery
    from ....domain.currency import Currency

    try:
        # Converte string para Currency enum se informado
        currency_enum = None
        if base_currency:
            try:
                currency_enum = Currency(base_currency.upper())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Moeda inválida: {base_currency}. Valores aceitos: BRL, USD, EUR, GBP, BTC, ETH",
                )

        query = ConsultarPortfolioQuery(base_currency=currency_enum)
        result = await handler.handle(query)

        # Calcular valor das posições
        posicoes = await broker.listar_posicoes_marcadas()
        valor_posicoes = sum(p.get("valor_atual", 0) for p in posicoes)
        # Monta CashbookResponse
        cashbook_entries = []
        for currency, entry in broker.cashbook._entries.items():
            cashbook_entries.append(CashEntryResponse(
                currency=currency.value,
                amount=float(entry.amount),
                conversion_rate=float(entry.conversion_rate),
                value_in_base_currency=float(entry.value_in_base_currency),
            ))
        cashbook_response = CashbookResponse(
            base_currency=broker.cashbook.base_currency.value,
            entries=cashbook_entries,
            total_in_base_currency=float(broker.cashbook.total_in_base_currency),
        )
        return PortfolioResponse(
            saldo_inicial=result.saldo_inicial,
            saldo_disponivel=result.saldo_atual,
            valor_posicoes=round(valor_posicoes, 2),
            patrimonio_total=round(result.saldo_atual + valor_posicoes, 2),
            pnl=result.pnl,
            pnl_percentual=result.pnl_percentual,
            currency=result.currency.value,
            cashbook=cashbook_response,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao consultar portfolio: {e}")


@router.get(
    "/posicoes",
    response_model=List[PosicaoResponse],
    summary="Listar posições",
)
async def listar_posicoes(
    broker: JsonFilePaperBroker = Depends(get_broker),
):
    """Lista todas as posições abertas com PnL calculado ao preço atual."""
    try:
        posicoes = await broker.listar_posicoes_marcadas()
        return [PosicaoResponse(**p) for p in posicoes]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao listar posições: {e}")


@router.post(
    "/deposito",
    response_model=DepositoResponse,
    summary="Depositar saldo",
)
async def depositar(
    req: DepositoRequest,
    handler: DepositarHandler = Depends(get_depositar_handler),
    converter: Optional["CurrencyConverterPort"] = Depends(get_currency_converter),
):
    """Adiciona saldo ao portfolio.

    **Parâmetros:**
    - `valor`: Valor a depositar (positivo)
    - `currency`: Moeda do depósito (opcional, padrão: BRL)

    **Exemplos:**
    - `{"valor": 1000, "currency": "BRL"}` - Deposita R$ 1.000
    - `{"valor": 500, "currency": "USD"}` - Deposita $ 500 USD
    """
    from ....domain.currency import Currency
    from ....ports.currency_converter_port import CurrencyConverterPort

    try:
        command = DepositarCommand(valor=Decimal(str(req.valor)))
        # Converte moeda para enum
        try:
            currency_enum = Currency(req.currency.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Moeda inválida: {req.currency}. Valores aceitos: BRL, USD, EUR, GBP, BTC, ETH",
            )
        # Obtém taxa de conversão atual
        conversion_rate = Decimal("1")
        base_currency = Currency.BRL  # TODO: obter do estado
        if currency_enum != base_currency:
            # Precisa obter taxa de conversão
            if converter:
                conversion_rate = await converter.get_rate(
                    currency_enum, base_currency
                )
        result = await handler.handle(
            command,
            moeda=req.currency,
            conversion_rate=conversion_rate,
        )
        return DepositoResponse(
            saldo_anterior=float(result.saldo_anterior),
            valor_depositado=float(result.valor_depositado),
            saldo_atual=float(result.saldo_atual),
            currency=result.moeda,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/reset",
    response_model=ResetResponse,
    summary="Resetar portfolio",
)
async def resetar(
    saldo_inicial: Optional[float] = None,
    handler: ResetarHandler = Depends(get_resetar_handler),
):
    """Reseta o portfolio para estado inicial.

    Limpa todas as ordens, posições e redefine saldo.

    **Parâmetro:**
    - `saldo_inicial`: Novo saldo inicial (opcional, padrão: R$ 100.000)
    """
    try:
        command = ResetarCommand(
            saldo_inicial=Decimal(str(saldo_inicial)) if saldo_inicial is not None else None
        )
        result = await handler.handle(command)
        return ResetResponse(
            saldo_anterior=float(result.saldo_anterior),
            saldo_novo=float(result.saldo_novo),
            ordens_removidas=result.ordens_removidas,
            posicoes_removidas=result.posicoes_removidas,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao resetar: {e}")
