# -*- coding: utf-8 -*-
"""
Discord Application - Portfolio Commands.

Comandos slash e botões para o módulo Paper Trading.
"""

from decimal import Decimal

import discord
from discord import app_commands, Embed
from discord.ui import View

from src.core.discord.presentation.portfolio_views import (
    PortfolioMainView,
    PortfolioWelcomeView,
    PortfolioReadModel,
    AssetCardReadModel,
)


# ═══════════════════════════════════════════════════════════════════════
# Slash Commands
# ═══════════════════════════════════════════════════════════════════════

class PortfolioCommands(app_commands.Group):
    """
    Comandos slash para Portfolio.

    Uso:
        /portfolio              - Mostra painel principal
        /portfolio saldo        - Mostra saldo e posições
        /portfolio alocacao     - Mostra alocação por tipo
    """

    def __init__(self, bot: discord.Client):
        super().__init__(name="portfolio", description="Comandos do Portfolio Paper Trading")
        self.bot = bot

    @app_commands.command(name="mostrar", description="Mostra painel do Portfolio")
    async def mostrar(self, interaction: discord.Interaction):
        """
        Mostra painel principal do Portfolio.
        """
        # Cria portfolio mock (TODO: conectar ao Paper Trading)
        portfolio = self._create_mock_portfolio()

        # Cria view
        view = PortfolioMainView(portfolio=portfolio)

        # Cria embed principal
        embed = self._create_main_embed(portfolio)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="saldo", description="Mostra saldo e posições")
    async def saldo(self, interaction: discord.Interaction):
        """Mostra saldo e posições atuais."""
        portfolio = self._create_mock_portfolio()
        view = PortfolioMainView(portfolio=portfolio)
        embed = view._create_saldo_embed()

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="alocacao", description="Mostra alocação por tipo")
    async def alocacao(self, interaction: discord.Interaction):
        """Mostra alocação por tipo de ativo."""
        portfolio = self._create_mock_portfolio()
        view = PortfolioMainView(portfolio=portfolio)
        embed = view._create_alocacao_embed()

        await interaction.response.send_message(embed=embed, ephemeral=True)

    def _create_mock_portfolio(self) -> PortfolioReadModel:
        """
        Cria portfolio mock para demonstração.

        TODO: Integrar com Paper Trading real via queries.
        """
        return PortfolioReadModel(
            valor_total=Decimal("160730.00"),
            valor_investido=Decimal("149640.00"),
            lucro_prejuizo=Decimal("11090.00"),
            lucro_prejuizo_percentual=7.41,
            ativos=[
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
            ],
            alocacao_por_tipo={
                "Cripto": Decimal("117900.00"),
                "Ações": Decimal("6702.50"),
                "FIIs": Decimal("36127.50"),
                "total": Decimal("160730.00"),
            },
        )

    def _create_main_embed(self, portfolio: PortfolioReadModel) -> Embed:
        """Cria embed principal do portfolio."""
        pnl = portfolio.lucro_prejuizo
        pnl_percent = portfolio.lucro_prejuizo_percentual

        # Cor baseada no PnL
        if pnl >= 0:
            color = 0x22C55E  # Verde
            emoji = "📈"
        else:
            color = 0xEF4444  # Vermelho
            emoji = "📉"

        embed = Embed(
            title="📊 Meu Portfólio",
            description="Visão geral dos investimentos",
            color=color,
        )

        embed.add_field(
            name="Valor Total",
            value=f"R$ {portfolio.valor_total:,.2f}",
            inline=False,
        )

        embed.add_field(
            name=f"{emoji} Lucro/Prejuízo",
            value=f"R$ {pnl:,.2f} ({pnl_percent:+.2f}%)",
            inline=True,
        )

        embed.add_field(
            name="💵 Investido",
            value=f"R$ {portfolio.valor_investido:,.2f}",
            inline=True,
        )

        embed.add_field(
            name="📊 Ativos",
            value=str(len(portfolio.ativos)),
            inline=True,
        )

        embed.set_footer(text="Paper Trading – Dados simulados")

        return embed


# ═══════════════════════════════════════════════════════════════════════
# Setup Command Tree
# ═══════════════════════════════════════════════════════════════════════

async def setup_portfolio_commands(bot: discord.Client):
    """
    Registra comandos do Portfolio no bot.

    Args:
        bot: Cliente Discord
    """
    from discord.app_commands import CommandTree

    tree = CommandTree(bot)
    portfolio_group = PortfolioCommands(bot)
    tree.add_command(portfolio_group)

    # Sync commands (development only)
    # await tree.sync()

    return tree


__all__ = [
    "PortfolioCommands",
    "setup_portfolio_commands",
]
