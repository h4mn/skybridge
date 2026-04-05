# -*- coding: utf-8 -*-
"""Tool: Criar Ordem - Paper Trading MCP.

Ferramenta MCP para criar ordens de compra/venda via LLM.
"""
from decimal import Decimal
from typing import Optional

from ....application.commands.criar_ordem import CriarOrdemCommand
from ....application.handlers.criar_ordem_handler import CriarOrdemHandler
from ....adapters.brokers import SaldoInsuficienteError


class CriarOrdemTool:
    """Tool MCP para criação de ordens.

    Nome da tool: paper_criar_ordem
    """

    name = "paper_criar_ordem"
    description = """
    Cria uma nova ordem de compra ou venda no sistema de paper trading.

    Use esta ferramenta quando o usuário quiser:
    - Comprar um ativo
    - Vender um ativo
    - Abrir uma posição
    - Fechar uma posição

    Parâmetros:
    - ticker: Código do ativo (ex: PETR4.SA, BTC-USD)
    - lado: COMPRA ou VENDA
    - quantidade: Número de unidades
    """

    def __init__(self, handler: CriarOrdemHandler):
        self._handler = handler

    async def execute(
        self,
        ticker: str,
        lado: str,
        quantidade: int,
        preco_limite: Optional[float] = None,
        portfolio_id: str = "default",
    ) -> dict:
        """Executa a criação da ordem."""
        try:
            command = CriarOrdemCommand(
                ticker=ticker.upper(),
                lado=lado.upper(),
                quantidade=quantidade,
                preco_limite=Decimal(str(preco_limite)) if preco_limite else None,
                portfolio_id=portfolio_id,
            )
            result = await self._handler.handle(command)

            return {
                "sucesso": True,
                "ordem_id": result.id,
                "ticker": result.ticker,
                "lado": result.lado,
                "quantidade": result.quantidade,
                "preco_execucao": result.preco_execucao,
                "valor_total": result.valor_total,
                "status": result.status,
                "timestamp": result.timestamp,
            }
        except SaldoInsuficienteError as e:
            return {"sucesso": False, "erro": str(e)}
        except ValueError as e:
            return {"sucesso": False, "erro": str(e)}

    def get_schema(self) -> dict:
        """Retorna schema JSON para validação de parâmetros."""
        return {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Código do ativo (ex: PETR4.SA)",
                },
                "lado": {
                    "type": "string",
                    "enum": ["COMPRA", "VENDA"],
                    "description": "Direção da operação",
                },
                "quantidade": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Número de unidades",
                },
                "preco_limite": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Preço limite (opcional)",
                },
            },
            "required": ["ticker", "lado", "quantidade"],
        }
