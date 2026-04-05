# -*- coding: utf-8 -*-
"""
Discord Presentation Layer - Portfolio Views.

Componentes interativos Discord para o módulo Paper Trading.
Baseados no design Figma "Portfolio Embed".

Padrão: View com @button decorators → on_interaction loga → decorator roteia.
"""

from decimal import Decimal
from typing import Optional
from dataclasses import dataclass

import discord
from discord.ui import View, button, Button
from discord import ButtonStyle, Embed


# ═══════════════════════════════════════════════════════════════════════
# Colors - Figma Design Tokens
# ═══════════════════════════════════════════════════════════════════════

class PortfolioColors:
    """Cores do design Figma."""

    SUCCESS = 0x22C55E    # Verde +15.09%
    DANGER = 0xEF4444     # Vermelho para prejuízo
    PRIMARY = 0x3B82F6    # Azul primary
    DARK = 0x1F2937       # Fundo escuro
    CRYPTO = 0xF59E0B     # Laranja para cripto
    STOCK = 0x6366F1      # Índigo para ações
    FII = 0x8B5CF6        # Roxo para FIIs


# ═══════════════════════════════════════════════════════════════════════
# Read Models - Dados para Views
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class AssetCardReadModel:
    """
    Read Model para card de ativo.

    Baseado no design Figma "Portfolio Embed".
    """
    ticker: str
    nome: str
    tipo: str  # "Ação", "Cripto", "FII"
    variação_percentual: float
    quantidade: Decimal
    preco_medio: Decimal
    preco_atual: Decimal
    valor_total: Decimal
    lucro_prejuizo: Decimal


@dataclass
class PortfolioReadModel:
    """
    Read Model principal do Portfolio.

    Dados agregados para as views Discord.
    """
    valor_total: Decimal
    valor_investido: Decimal
    lucro_prejuizo: Decimal
    lucro_prejuizo_percentual: float
    ativos: list[AssetCardReadModel]
    alocacao_por_tipo: dict[str, Decimal]


# ═══════════════════════════════════════════════════════════════════════
# View Principal - Painel Portfolio
# ═══════════════════════════════════════════════════════════════════════

class PortfolioMainView(View):
    """
    View principal do painel Portfolio.

    Botões de navegação principal:
    - Ver Saldo/Posições
    - Ver Portfolio Completo
    - Ver Alocação
    - Configurações
    """

    def __init__(self, portfolio: PortfolioReadModel):
        super().__init__(timeout=None)
        self.portfolio = portfolio

    @button(label="💰 Saldo/Posições", style=ButtonStyle.primary, custom_id="portfolio_saldo", row=0)
    async def saldo_button(self, interaction: discord.Interaction, button: Button):
        """Mostra saldo e posições atuais."""
        await interaction.response.defer()

        embed = self._create_saldo_embed()
        await interaction.followup.send(embed=embed, ephemeral=True)

    @button(label="📊 Portfolio Completo", style=ButtonStyle.secondary, custom_id="portfolio_completo", row=0)
    async def completo_button(self, interaction: discord.Interaction, button: Button):
        """Mostra portfolio completo com todos os ativos e gráfico PnL."""
        await interaction.response.defer()

        # Tenta usar gráfico profissional para PnL
        try:
            from .chart_helper_pro import ProChartHelper

            # Prepara dados para gráfico de barras
            ativos_pnl = [
                {"ticker": a.ticker, "pnl": a.lucro_prejuizo}
                for a in self.portfolio.ativos
            ]

            helper = ProChartHelper(dpi=100)
            img_pnl = helper.pnl_bar_chart(ativos_pnl)

            # Envia gráfico primeiro
            await interaction.followup.send(
                "💰 **Lucro/Prejuízo por Ativo**",
                file=discord.File(img_pnl, "pnl.png"),
                ephemeral=True
            )

        except ImportError:
            pass  # Continua sem gráfico

        # Envia embeds dos ativos
        embeds = self._create_portfolio_embeds()

        # Discord limita a 10 embeds por mensagem
        await interaction.followup.send(embeds=embeds[:10], ephemeral=True)

    @button(label="📈 Ver Alocação", style=ButtonStyle.secondary, custom_id="portfolio_alocacao", row=1)
    async def alocacao_button(self, interaction: discord.Interaction, button: Button):
        """Mostra alocação por tipo de ativo com gráfico profissional."""
        await interaction.response.defer()

        # Tenta usar gráfico profissional matplotlib
        try:
            from .chart_helper_pro import ProChartHelper
            import io

            helper = ProChartHelper(dpi=100, width=8, height=8)
            img = helper.alocacao_donut(self.portfolio.alocacao_por_tipo)

            # Envia gráfico como arquivo
            await interaction.followup.send(
                "📈 **Alocação por Tipo**",
                file=discord.File(img, "alocacao.png"),
                ephemeral=True
            )
        except ImportError:
            # Fallback para embed se matplotlib não estiver disponível
            embed = self._create_alocacao_embed()
            await interaction.followup.send(embed=embed, ephemeral=True)

    @button(label="⚙️ Configurações", style=ButtonStyle.secondary, custom_id="portfolio_config", row=1)
    async def config_button(self, interaction: discord.Interaction, button: Button):
        """Abre configurações do portfolio."""
        await interaction.response.send_message(
            "⚙️ Configurações em desenvolvimento...",
            ephemeral=True
        )

    def _create_saldo_embed(self) -> Embed:
        """Cria embed com saldo e posições."""
        total = self.portfolio.valor_total
        invested = self.portfolio.valor_investido
        pnl = self.portfolio.lucro_prejuizo
        pnl_percent = self.portfolio.lucro_prejuizo_percentual

        # Cor baseada no PnL
        color = PortfolioColors.SUCCESS if pnl >= 0 else PortfolioColors.DANGER

        embed = Embed(
            title="💰 Saldo e Posições",
            description=f"**Valor Total:** {self._format_currency(total)}",
            color=color
        )

        embed.add_field(
            name="💵 Investido",
            value=self._format_currency(invested),
            inline=True
        )

        embed.add_field(
            name="📈 Lucro/Prejuízo",
            value=f"{self._format_currency(pnl)} ({pnl_percent:+.2f}%)",
            inline=True
        )

        embed.add_field(
            name="📊 Ativos",
            value=str(len(self.portfolio.ativos)),
            inline=True
        )

        embed.set_footer(text="Paper Trading – Dados simulados")

        return embed

    def _create_portfolio_embeds(self) -> list[Embed]:
        """Cria embeds para cada ativo + resumo."""
        embeds = []

        # Header embed
        header = Embed(
            title="📊 Meu Portfólio",
            description="Visão geral dos investimentos",
            color=PortfolioColors.PRIMARY
        )

        total = self.portfolio.valor_total
        pnl = self.portfolio.lucro_prejuizo
        pnl_percent = self.portfolio.lucro_prejuizo_percentual

        header.add_field(
            name="Valor Total",
            value=self._format_currency(total),
            inline=False
        )

        header.add_field(
            name="Lucro/Prejuízo",
            value=f"{self._format_currency(pnl)} ({pnl_percent:+.2f}%)",
            inline=False
        )

        embeds.append(header)

        # Asset cards (um embed por ativo)
        for asset in self.portfolio.ativos:
            embeds.append(self._create_asset_embed(asset))

        return embeds

    def _create_asset_embed(self, asset: AssetCardReadModel) -> Embed:
        """Cria embed para um ativo individual."""
        # Cor baseada no tipo e variação
        if asset.variação_percentual >= 0:
            color = PortfolioColors.SUCCESS
        else:
            color = PortfolioColors.DANGER

        # Tipo emoji
        tipo_emoji = {
            "Ação": "📈",
            "Cripto": "₿",
            "FII": "🏢"
        }.get(asset.tipo, "📊")

        embed = Embed(
            title=f"{tipo_emoji} {asset.ticker}",
            description=asset.nome,
            color=color
        )

        # Badge de variação
        var_text = f"{asset.variação_percentual:+.2f}%"
        embed.add_field(name="Variação", value=var_text, inline=True)

        # Detalhes
        embed.add_field(
            name="Quantidade",
            value=str(asset.quantidade),
            inline=True
        )

        embed.add_field(
            name="Preço Médio",
            value=self._format_currency(asset.preco_medio),
            inline=True
        )

        embed.add_field(
            name="Preço Atual",
            value=self._format_currency(asset.preco_atual),
            inline=True
        )

        embed.add_field(
            name="Valor Total",
            value=self._format_currency(asset.valor_total),
            inline=True
        )

        embed.add_field(
            name="💰 Lucro/Prejuízo",
            value=self._format_currency(asset.lucro_prejuizo),
            inline=False
        )

        embed.set_footer(text=f"Tipo: {asset.tipo}")

        return embed

    def _create_alocacao_embed(self) -> Embed:
        """Cria embed com alocação por tipo."""
        alloc = self.portfolio.alocacao_por_tipo

        embed = Embed(
            title="📈 Alocação por Tipo",
            description="Distribuição do portfolio por categoria",
            color=PortfolioColors.PRIMARY
        )

        # Barra visual simples
        total = alloc.get("total", Decimal("1"))

        for tipo, valor in alloc.items():
            if tipo == "total":
                continue

            percent = (valor / total * 100) if total > 0 else 0
            emoji = {
                "Cripto": "₿",
                "Ações": "📈",
                "FIIs": "🏢"
            }.get(tipo, "📊")

            # Barra visual
            bars = "█" * int(percent / 5)  # 1 bar = 5%
            embed.add_field(
                name=f"{emoji} {tipo}",
                value=f"{bars} {percent:.1f}% ({self._format_currency(valor)})",
                inline=False
            )

        embed.set_footer(text="Paper Trading – Alocação simulada")

        return embed

    def _format_currency(self, value: Decimal) -> str:
        """Formata valor como moeda BRL."""
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ═══════════════════════════════════════════════════════════════════════
# View Simplificada - Mensagem Inicial
# ═══════════════════════════════════════════════════════════════════════

class PortfolioWelcomeView(View):
    """
    View de boas-vindas com botão para abrir painel.
    """

    @button(label="📊 Abrir Portfolio", style=ButtonStyle.success, custom_id="portfolio_open")
    async def open_button(self, interaction: discord.Interaction, button: Button):
        """Abre o painel principal do portfolio."""
        await interaction.response.send_message(
            "📊 Carregando portfolio...",
            ephemeral=True
        )
        # TODO: Carregar portfolio e enviar PortfolioMainView


__all__ = [
    "PortfolioMainView",
    "PortfolioWelcomeView",
    "PortfolioReadModel",
    "AssetCardReadModel",
    "PortfolioColors",
]
