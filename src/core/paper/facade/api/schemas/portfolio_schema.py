"""
Schemas de Portfolio - Paper Trading API

Modelos Pydantic para validação de portfolio e posições.
"""

from decimal import Decimal

from pydantic import BaseModel, Field


class PosicaoResponse(BaseModel):
    """Schema de resposta para posição."""

    ticker: str = Field(..., description="Código do ativo")
    quantidade: int = Field(..., description="Quantidade detida")
    preco_medio: Decimal = Field(..., description="Preço médio de aquisição")
    preco_atual: Decimal = Field(..., description="Preço atual de mercado")
    pl: Decimal = Field(..., description="Lucro/prejuízo da posição")
    pl_percentual: Decimal = Field(..., description="PL em percentual")
    valor_mercado: Decimal = Field(..., description="Valor a mercado")

    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    """Schema de resposta para portfolio."""

    id: str = Field(..., description="ID único do portfolio")
    saldo_disponivel: Decimal = Field(..., description="Saldo disponível")
    valor_total: Decimal = Field(..., description="Valor total do portfolio")
    pl_total: Decimal = Field(..., description="Lucro/prejuízo total")
    pl_percentual: Decimal = Field(..., description="PL total em percentual")
    posicoes: list[PosicaoResponse] = Field(
        default_factory=list,
        description="Lista de posições",
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "portfolio-001",
                "saldo_disponivel": "50000.00",
                "valor_total": "150000.00",
                "pl_total": "5000.00",
                "pl_percentual": "3.45",
                "posicoes": [
                    {
                        "ticker": "PETR4",
                        "quantidade": 100,
                        "preco_medio": "28.00",
                        "preco_atual": "30.00",
                        "pl": "200.00",
                        "pl_percentual": "7.14",
                        "valor_mercado": "3000.00",
                    }
                ],
            }
        }


class HistoricoResponse(BaseModel):
    """Schema de resposta para histórico de operações."""

    id: str = Field(..., description="ID da operação")
    ticker: str = Field(..., description="Código do ativo")
    lado: str = Field(..., description="Direção da operação")
    quantidade: int = Field(..., description="Quantidade executada")
    preco: Decimal = Field(..., description="Preço de execução")
    timestamp: str = Field(..., description="Data/hora da operação")

    class Config:
        from_attributes = True
