# -*- coding: utf-8 -*-
"""
Envia painel Portfolio via MCP Discord.

Usa o MCP server já conectado para enviar embeds com botões.
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, ".")

from src.core.paper.application.queries.consultar_portfolio import ConsultarPortfolioQuery
from src.core.paper.application.handlers.consultar_portfolio_handler import ConsultarPortfolioHandler
from src.core.paper.adapters.brokers.json_file_broker import JsonFilePaperBroker
from src.core.paper.adapters.data_feeds.yahoo_finance_feed import YahooFinanceFeed
from src.core.paper.adapters.currency.yahoo_currency_adapter import YahooCurrencyAdapter
from src.core.paper.adapters.persistence.json_file_paper_state import JsonFilePaperState

from src.core.discord.presentation.portfolio_state_machine import (
    PortfolioStateMachine,
    PortfolioState,
    create_reduced_panel_embed,
    create_expanded_panel_embed,
    get_dynamic_embed,
)
from src.core.discord.presentation.portfolio_views import (
    PortfolioReadModel,
    AssetCardReadModel,
)


async def get_real_portfolio() -> PortfolioReadModel:
    """Obtém portfolio real do paper módulo."""
    feed = YahooFinanceFeed()
    paper_state = JsonFilePaperState()
    converter = YahooCurrencyAdapter()

    broker = JsonFilePaperBroker(
        feed=feed,
        paper_state=paper_state,
        converter=converter,
    )

    handler = ConsultarPortfolioHandler(
        broker=broker,
        feed=feed,
        converter=converter,
    )

    query = ConsultarPortfolioQuery(portfolio_id="default")
    result = await handler.handle(query)

    # Busca posições
    posicoes = await broker.listar_posicoes_marcadas()

    ativos = []
    for pos in posicoes:
        ativos.append(AssetCardReadModel(
            ticker=pos["ticker"],
            nome=pos["ticker"],
            tipo="Ação",
            variação_percentual=pos.get("variacao_percentual", 0),
            quantidade=Decimal(str(pos["quantidade"])),
            preco_medio=Decimal(str(pos["preco_medio"])),
            preco_atual=Decimal(str(pos["preco_atual"])),
            valor_total=Decimal(str(pos["valor_atual"])),
            lucro_prejuizo=Decimal(str(pos.get("pnl", 0))),
        ))

    return PortfolioReadModel(
        valor_total=Decimal(str(result.saldo_atual)),
        valor_investido=Decimal(str(result.saldo_inicial)),
        lucro_prejuizo=Decimal(str(result.pnl)),
        lucro_prejuizo_percentual=result.pnl_percentual,
        ativos=ativos,
        alocacao_por_tipo={
            "Ações": Decimal(str(result.saldo_atual)),
            "total": Decimal(str(result.saldo_atual)),
        },
    )


def main():
    """Obtém portfolio do paper módulo."""
    print("Buscando portfolio do paper módulo...")

    portfolio = asyncio.run(get_real_portfolio())

    print(f"\nPortfolio Principal")
    print(f"Valor Total: R$ {portfolio.valor_total:,.2f}")
    print(f"Valor Investido: R$ {portfolio.valor_investido:,.2f}")
    print(f"PnL: R$ {portfolio.lucro_prejuizo:,.2f} ({portfolio.lucro_prejuizo_percentual:+.2f}%)")
    print(f"\nAtivos ({len(portfolio.ativos)}):")
    for ativo in portfolio.ativos:
        print(f"  - {ativo.ticker}: {ativo.quantidade} @ R$ {ativo.preco_atual:,.2f}")

    # Retorna para ser usado pelo MCP
    return portfolio


if __name__ == "__main__":
    main()
