# -*- coding: utf-8 -*-
"""
Discord Bot integrado ao Paper Trading Module.

Usa queries e handlers do paper módulo para dados reais.
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Fix UTF-8 no Windows
if sys.platform == "win32" and sys.stdout.isatty() and sys.stderr.isatty():
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except (ValueError, OSError):
        pass

import discord
from discord import Intents
from dotenv import dotenv_values

sys.path.insert(0, ".")

from src.core.discord.presentation.portfolio_state_machine import (
    PortfolioState,
    PortfolioStateMachine,
    get_dynamic_embed,
    create_reduced_panel_embed,
)
from src.core.discord.presentation.portfolio_panel_view import PortfolioPanelView
from src.core.discord.presentation.portfolio_views import (
    PortfolioReadModel,
    AssetCardReadModel,
)

# Paper Module imports
from src.core.paper.application.queries.consultar_portfolio import ConsultarPortfolioQuery
from src.core.paper.application.handlers.consultar_portfolio_handler import ConsultarPortfolioHandler
from src.core.paper.adapters.brokers.paper_broker import PaperBroker
from src.core.paper.adapters.data_feeds.yahoo_finance_feed import YahooFinanceFeed
from src.core.paper.adapters.currency.yahoo_currency_adapter import YahooCurrencyAdapter


async def create_portfolio_from_result(result, broker) -> PortfolioReadModel:
    """Converte PortfolioResult do paper em PortfolioReadModel do Discord."""
    # Busca posições do broker
    broker.reload()
    posicoes = await broker.listar_posicoes_marcadas()

    ativos = []
    for pos in posicoes:
        ativos.append(AssetCardReadModel(
            ticker=pos["ticker"],
            nome=pos["ticker"],  # TODO: buscar nome completo
            tipo="Ação",  # TODO: detectar tipo
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


async def get_real_portfolio() -> PortfolioReadModel:
    """Obtém portfolio real do paper módulo."""
    # Cria dependências do paper module
    broker = PaperBroker()
    feed = YahooFinanceFeed()
    converter = YahooCurrencyAdapter()

    # Cria handler
    handler = ConsultarPortfolioHandler(
        broker=broker,
        feed=feed,
        converter=converter,
    )

    # Executa query
    query = ConsultarPortfolioQuery(portfolio_id="default")
    result = await handler.handle(query)

    # Converte para PortfolioReadModel
    return await create_portfolio_from_result(result, broker)


# ═══════════════════════════════════════════════════════════════════════
# Discord Bot
# ═══════════════════════════════════════════════════════════════════════

class PortfolioDiscordBot(discord.Client):
    """
    Bot Discord integrado ao Paper Trading Module.

    Usa queries reais do paper módulo para dados do portfolio.
    """

    def __init__(self, channel_id: int):
        intents = Intents.default()
        super().__init__(intents=intents)

        self.channel_id = channel_id
        self.state_machine = None  # Será criado no on_ready
        self._last_portfolio = None  # Cache do último portfolio

    async def on_ready(self):
        """Bot está pronto - cria painel no canal."""
        print(f"[OK] Bot conectado como {self.user}")

        channel = self.get_channel(self.channel_id)
        if not channel:
            print(f"[ERRO] Canal {self.channel_id} não encontrado!")
            return

        print(f"[INFO] Canal: #{channel.name}")

        # Obtém portfolio real do paper módulo
        print("[INFO] Buscando portfolio do paper módulo...")
        portfolio = await get_real_portfolio()
        self._last_portfolio = portfolio

        # Cria state machine
        self.state_machine = PortfolioStateMachine(
            channel_id=channel.id,
            topic_message_id=None,
            dynamic_message_id=None,
            portfolio=portfolio,
        )

        # Cria painel
        await self._create_panel(channel)
        print("[OK] Painel criado com dados reais!")

    async def _create_panel(self, channel):
        """Cria painel no canal com mensagem fixa + dinâmica."""
        view = PortfolioPanelView(self.state_machine)

        # 1. Envia painel reduzido fixo
        reduced_embed = create_reduced_panel_embed(self.state_machine.portfolio)
        topic_msg = await channel.send(embed=reduced_embed)
        self.state_machine.topic_message_id = topic_msg.id

        # 2. Envia embed dinâmico inicial
        dynamic_embed = get_dynamic_embed(self.state_machine)
        dynamic_msg = await channel.send(embed=dynamic_embed, view=view)
        self.state_machine.dynamic_message_id = dynamic_msg.id

        print(f"  [OK] Painel criado:")
        print(f"     - Mensagem fixa: {topic_msg.id}")
        print(f"     - Mensagem dinamica: {dynamic_msg.id}")

    async def on_interaction(self, interaction):
        """Processa interações com botões do painel."""
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")
        if not custom_id.startswith("portfolio_"):
            return

        # Extrai ação
        action = custom_id.replace("portfolio_", "")
        print(f"  [INFO] Botao pressionado: {action}")

        # Transiciona estado
        if action == "expand":
            self.state_machine.transition_to(PortfolioState.EXPANDED)
        elif action == "collapse":
            self.state_machine.transition_to(PortfolioState.MAIN)
        elif action == "assets":
            self.state_machine.transition_to(PortfolioState.EXPANDED)
        elif action == "back":
            self.state_machine.transition_to(PortfolioState.MAIN)

        # Atualiza painel
        await interaction.response.defer()

        # Atualiza embed dinâmico e view
        new_embed = get_dynamic_embed(self.state_machine)
        new_view = PortfolioPanelView(self.state_machine)

        await interaction.followup.edit_message(
            message_id=self.state_machine.dynamic_message_id,
            embed=new_embed,
            view=new_view
        )

        print(f"  [OK] Estado: {self.state_machine.current_state.value}")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

async def main():
    """Inicia bot Portfolio integrado ao paper módulo."""
    config = dotenv_values(Path.home() / ".claude/channels/discord" / ".env")
    token = config.get("DISCORD_BOT_TOKEN")

    if not token:
        print("[ERRO] DISCORD_BOT_TOKEN nao encontrado em .env")
        return

    # Canal #paper-heartbeat
    CHANNEL_ID = 1488599448882909204

    # Cria e inicia bot
    bot = PortfolioDiscordBot(channel_id=CHANNEL_ID)

    print("\n" + "="*60)
    print("PORTFOLIO BOT - Discord + Paper Module")
    print("="*60)
    print(f"Canal alvo: #{CHANNEL_ID} (#paper-heartbeat)")
    print("\nIniciando bot...")

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
