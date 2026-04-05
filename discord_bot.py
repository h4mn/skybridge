# -*- coding: utf-8 -*-
"""
Portfolio Bot - Discord Bot com State Machine.

Bot que monitora um tópico e mantém:
1. Painel reduzido fixo (sempre presente)
2. Embed dinâmico (muda com estado)
3. Barra de menu (navegação entre estados)

Uso:
    python -m discord_bot
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Fix UTF-8 no Windows - apenas quando stdout/stderr estão disponíveis
if sys.platform == "win32" and sys.stdout.isatty() and sys.stderr.isatty():
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except (ValueError, OSError):
        # Ignora se stdout/stderr não puderem ser redefinidos
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


# ═══════════════════════════════════════════════════════════════════════
# Mock Portfolio Data
# ═══════════════════════════════════════════════════════════════════════

def create_mock_portfolio() -> PortfolioReadModel:
    """Cria portfolio mockado para demo."""
    return PortfolioReadModel(
        valor_total=Decimal("160730.00"),
        valor_investido=Decimal("149640.00"),
        lucro_prejuizo=Decimal("11090.00"),
        lucro_prejuizo_percentual=7.41,
        ativos=[
            AssetCardReadModel(
                ticker="BTC",
                nome="Bitcoin",
                tipo="Cripto",
                variação_percentual=8.33,
                quantidade=Decimal("0.5"),
                preco_medio=Decimal("180000.00"),
                preco_atual=Decimal("195000.00"),
                valor_total=Decimal("97500.00"),
                lucro_prejuizo=Decimal("7500.00"),
            ),
            AssetCardReadModel(
                ticker="ETH",
                nome="Ethereum",
                tipo="Cripto",
                variação_percentual=7.37,
                quantidade=Decimal("2"),
                preco_medio=Decimal("9500.00"),
                preco_atual=Decimal("10200.00"),
                valor_total=Decimal("20400.00"),
                lucro_prejuizo=Decimal("1400.00"),
            ),
            AssetCardReadModel(
                ticker="HGLG11",
                nome="CSHG Logística",
                tipo="FII",
                variação_percentual=4.55,
                quantidade=Decimal("200"),
                preco_medio=Decimal("165.00"),
                preco_atual=Decimal("172.50"),
                valor_total=Decimal("34500.00"),
                lucro_prejuizo=Decimal("1500.00"),
            ),
            AssetCardReadModel(
                ticker="MXRF11",
                nome="Maxi Renda",
                tipo="FII",
                variação_percentual=6.37,
                quantidade=Decimal("150"),
                preco_medio=Decimal("10.20"),
                preco_atual=Decimal("10.85"),
                valor_total=Decimal("1627.50"),
                lucro_prejuizo=Decimal("97.50"),
            ),
            AssetCardReadModel(
                ticker="PETR4",
                nome="Petrobras PN",
                tipo="Ação",
                variação_percentual=15.09,
                quantidade=Decimal("100"),
                preco_medio=Decimal("28.50"),
                preco_atual=Decimal("32.80"),
                valor_total=Decimal("3280.00"),
                lucro_prejuizo=Decimal("430.00"),
            ),
            AssetCardReadModel(
                ticker="VALE3",
                nome="Vale ON",
                tipo="Ação",
                variação_percentual=4.98,
                quantidade=Decimal("50"),
                preco_medio=Decimal("65.20"),
                preco_atual=Decimal("68.45"),
                valor_total=Decimal("3422.50"),
                lucro_prejuizo=Decimal("162.50"),
            ),
        ],
        alocacao_por_tipo={
            "Cripto": Decimal("117900.00"),
            "Ações": Decimal("6702.50"),
            "FIIs": Decimal("36127.50"),
            "total": Decimal("160730.00"),
        },
    )


# ═══════════════════════════════════════════════════════════════════════
# Discord Bot
# ═══════════════════════════════════════════════════════════════════════

class PortfolioBot(discord.Client):
    """
    Bot Discord que mantém painel Portfolio com state machine.

    Monitora um tópico específico e atualiza conforme interações.
    """

    def __init__(self, channel_id: int):
        intents = Intents.default()
        super().__init__(intents=intents)

        self.channel_id = channel_id

        # State Machine
        self.state_machine = PortfolioStateMachine(
            channel_id=channel_id,
            topic_message_id=None,  # Será definido ao criar
            dynamic_message_id=None,  # Será definido ao criar
            portfolio=create_mock_portfolio(),
        )

    async def on_ready(self):
        """Bot está pronto - cria painel no canal."""
        print(f"[OK] Bot conectado como {self.user}")

        channel = self.get_channel(self.channel_id)
        if not channel:
            print(f"[ERRO] Canal {self.channel_id} não encontrado!")
            return

        print(f"[INFO] Canal: #{channel.name}")

        # Cria painel reduzido fixo
        await self._create_panel(channel)

        print("[OK] Painel criado! Use os botões para interagir.")

    async def _create_panel(self, channel):
        """
        Cria painel no canal com mensagem fixa + dinâmica.

        Estrutura:
        1. Mensagem com painel reduzido (FIXA)
        2. Mensagem com embed dinâmico (MUDA)
        3. View com botões de navegação
        """
        # Cria state machine e view
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

    async def update_panel(self):
        """
        Atualiza painel conforme estado da máquina de estados.

        Edita a mensagem dinâmica com novo embed e view.
        """
        channel = self.get_channel(self.channel_id)
        if not channel:
            return

        # Busca mensagens
        try:
            topic_msg = await channel.fetch_message(self.state_machine.topic_message_id)
            dynamic_msg = await channel.fetch_message(self.state_machine.dynamic_message_id)

            # Atualiza embed dinâmico
            new_embed = get_dynamic_embed(self.state_machine)
            new_view = PortfolioPanelView(self.state_machine)

            # Edita mensagem dinâmica
            await dynamic_msg.edit(embed=new_embed, view=new_view)

            print(f"  [INFO] Painel atualizado: {self.state_machine.current_state.value}")

        except discord.NotFound:
            print(f"  [ERRO] Mensagem nao encontrada!")

    async def on_interaction(self, interaction):
        """
        Processa interações com botões do painel.

        Roteia cliques para transições de estado.
        """
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")
        if not custom_id.startswith("portfolio_"):
            return

        # Extrai ação
        action = custom_id.replace("portfolio_", "")

        print(f"  [INFO] Botao pressionado: {action}")

        # Processa ação
        if action == "expand":
            self.state_machine.transition_to(PortfolioState.EXPANDED)
        elif action == "collapse":
            self.state_machine.transition_to(PortfolioState.MAIN)
        elif action == "assets":
            self.state_machine.transition_to(PortfolioState.EXPANDED)
        elif action == "back":
            self.state_machine.transition_to(PortfolioState.MAIN)
        elif action == "chart" and self.state_machine.current_state == PortfolioState.ASSET_DETAIL:
            # TODO: Gerar gráfico do ativo
            pass
        elif action == "charts":
            # TODO: Gerar gráficos gerais
            pass

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
    """Inicia bot Portfolio."""
    # Carrega configuração
    config = dotenv_values(Path.home() / ".claude/channels/discord" / ".env")
    token = config.get("DISCORD_BOT_TOKEN")

    if not token:
        print("[ERRO] DISCORD_BOT_TOKEN nao encontrado em .env")
        return

    # Canal #paper-heartbeat
    CHANNEL_ID = 1488599448882909204

    # Cria e inicia bot
    bot = PortfolioBot(channel_id=CHANNEL_ID)

    print("\n" + "="*60)
    print("PORTFOLIO BOT - Discord")
    print("="*60)
    print(f"Canal alvo: #{1488599448882909204} (#paper-heartbeat)")
    print("\nIniciando bot...")

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
