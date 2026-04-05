"""
Schemas de Ordem - Paper Trading API

Modelos Pydantic para validação de ordens.
"""

from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LadoOrdem(str, Enum):
    """Direção da operação."""

    COMPRA = "COMPRA"
    VENDA = "VENDA"


class StatusOrdem(str, Enum):
    """Status da ordem."""

    PENDENTE = "PENDENTE"
    EXECUTADA = "EXECUTADA"
    CANCELADA = "CANCELADA"
    PARCIALMENTE_EXECUTADA = "PARCIALMENTE_EXECUTADA"


class OrdemCreate(BaseModel):
    """Schema para criação de nova ordem."""

    ticker: str = Field(..., description="Código do ativo", example="PETR4")
    lado: LadoOrdem = Field(..., description="Direção da operação")
    quantidade: int = Field(..., gt=0, description="Quantidade de unidades")
    preco_limite: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Preço limite (None = mercado)",
    )
    portfolio_id: str = Field(
        default="default",
        description="ID do portfolio",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "PETR4",
                "lado": "COMPRA",
                "quantidade": 100,
                "preco_limite": "28.50",
                "portfolio_id": "default",
            }
        }


class OrdemResponse(BaseModel):
    """Schema de resposta para ordem."""

    id: str = Field(..., description="ID único da ordem")
    ticker: str = Field(..., description="Código do ativo")
    lado: LadoOrdem = Field(..., description="Direção da operação")
    quantidade: int = Field(..., description="Quantidade solicitada")
    quantidade_executada: int = Field(default=0, description="Quantidade executada")
    preco_limite: Optional[Decimal] = Field(None, description="Preço limite")
    preco_medio: Optional[Decimal] = Field(None, description="Preço médio de execução")
    status: StatusOrdem = Field(..., description="Status atual")
    portfolio_id: str = Field(..., description="ID do portfolio")
    criado_em: str = Field(..., description="Data/hora de criação")
    atualizado_em: str = Field(..., description="Data/hora de atualização")

    class Config:
        from_attributes = True
