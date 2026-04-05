# -*- coding: utf-8 -*-
"""
Portfolio Panel View - Discord UI com botões fixos.

View com botões fixos para navegação entre estados do painel.
"""

from dataclasses import dataclass
from typing import Optional

import discord
from discord.ui import View, button, Button
from discord import Embed

from .portfolio_state_machine import PortfolioStateMachine, PortfolioState


@dataclass
class PortfolioPanelView(View):
    """
    View Discord com botões de navegação do painel.

    Botões fixos para cada estado - navegação simples.
    """

    state_machine: PortfolioStateMachine

    def __init__(self, state_machine: PortfolioStateMachine):
        super().__init__(timeout=None)
        self.sm = state_machine

    # Botões para estado MAIN
    @button(label="Expandir", style=discord.ButtonStyle.primary, custom_id="portfolio_expand", row=0)
    async def expand_button(self, interaction: discord.Interaction, button):
        """Expande painel para mostrar detalhes completos."""
        await self._handle_button(interaction, "expand")

    @button(label="Ativos", style=discord.ButtonStyle.secondary, custom_id="portfolio_assets", row=0)
    async def assets_button(self, interaction: discord.Interaction, button):
        """Mostra lista de todos os ativos."""
        await self._handle_button(interaction, "assets")

    # Botões para estado EXPANDED
    @button(label="Recolher", style=discord.ButtonStyle.secondary, custom_id="portfolio_collapse", row=0)
    async def collapse_button(self, interaction: discord.Interaction, button):
        """Recolhe painel para versão reduzida."""
        await self._handle_button(interaction, "collapse")

    @button(label="Graficos", style=discord.ButtonStyle.secondary, custom_id="portfolio_charts", row=1)
    async def charts_button(self, interaction: discord.Interaction, button):
        """Mostra graficos do portfolio."""
        await self._handle_button(interaction, "charts")

    # Botões para estado ASSET_DETAIL
    @button(label="Voltar", style=discord.ButtonStyle.secondary, custom_id="portfolio_back", row=0)
    async def back_button(self, interaction: discord.Interaction, button):
        """Volta para painel principal."""
        await self._handle_button(interaction, "back")

    @button(label="Grafico", style=discord.ButtonStyle.primary, custom_id="portfolio_asset_chart", row=1)
    async def asset_chart_button(self, interaction: discord.Interaction, button):
        """Mostra grafico do ativo."""
        await self._handle_button(interaction, "asset_chart")

    async def _handle_button(self, interaction: discord.Interaction, button_id: str):
        """
        Processa clique no botão.

        NOTA: A transição de estado e atualização do painel é feita pelo
        PortfolioBot.on_interaction(). Este callback apenas defere a resposta.
        """
        await interaction.response.defer()


# Mantém compatibilidade com import
PortfolioPanelView.__name__ = "PortfolioPanelView"
PortfolioPanelView.__module__ = "src.core.discord.presentation.portfolio_state_machine"
