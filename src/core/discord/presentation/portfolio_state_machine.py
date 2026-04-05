# -*- coding: utf-8 -*-
"""
Portfolio State Machine - Discord Integration.

Máquina de estados para painel Portfolio fixo no Discord.

Estados:
- MAIN: Painel reduzido fixo
- EXPANDED: Painel maximizado
- ASSET_DETAIL: Detalhes de ativo específico

Cada estado mantém:
1. Painel reduzido fixo (sempre presente)
2. Embed dinâmico (muda conforme estado)
3. Barra de menu (navegação entre estados)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Literal
from decimal import Decimal

import discord
from discord.ui import View, button, Button
from discord import Embed

from src.core.discord.presentation.portfolio_views import (
    PortfolioReadModel,
    AssetCardReadModel,
    PortfolioColors,
)


# ═══════════════════════════════════════════════════════════════════════
# State Enum
# ═══════════════════════════════════════════════════════════════════════

class PortfolioState(str, Enum):
    """Estados do painel Portfolio."""
    MAIN = "main"              # Painel reduzido fixo
    EXPANDED = "expanded"      # Painel maximizado
    ASSET_DETAIL = "detail"    # Detalhes de ativo


# ═══════════════════════════════════════════════════════════════════════
# State Machine
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class PortfolioStateMachine:
    """
    Máquina de estados para painel Portfolio.

    Gerencia transições entre estados e mantém referências às mensagens.
    """

    channel_id: int
    topic_message_id: int  # Mensagem fixa do painel reduzido
    dynamic_message_id: int  # Mensagem dinâmica (muda com estado)

    current_state: PortfolioState = PortfolioState.MAIN
    selected_asset: Optional[str] = None  # Ticker do ativo selecionado

    # Portfolio data
    portfolio: Optional[PortfolioReadModel] = None

    def transition_to(self, new_state: PortfolioState) -> bool:
        """
        Transiciona para novo estado.

        Args:
            new_state: Estado destino

        Returns:
            True se transição é válida
        """
        valid_transitions = {
            PortfolioState.MAIN: [PortfolioState.EXPANDED, PortfolioState.ASSET_DETAIL],
            PortfolioState.EXPANDED: [PortfolioState.MAIN],
            PortfolioState.ASSET_DETAIL: [PortfolioState.MAIN, PortfolioState.EXPANDED],
        }

        if new_state in valid_transitions.get(self.current_state, []):
            self.current_state = new_state
            return True

        return False

    def set_asset(self, ticker: str) -> None:
        """Define ativo selecionado e vai para estado DETAIL."""
        self.selected_asset = ticker
        self.transition_to(PortfolioState.ASSET_DETAIL)

    def get_menu_buttons(self) -> list[dict]:
        """
        Retorna botões da barra de menu baseados no estado atual.

        Returns:
            Lista de dicts com {label, style, custom_id, emoji}
        """
        if self.current_state == PortfolioState.MAIN:
            return [
                {"label": "Expandir", "style": "primary", "id": "expand", "emoji": "📊"},
                {"label": "Ativos", "style": "secondary", "id": "assets", "emoji": "📋"},
            ]
        elif self.current_state == PortfolioState.EXPANDED:
            return [
                {"label": "Recolher", "style": "secondary", "id": "collapse", "emoji": "📉"},
                {"label": "Gráficos", "style": "secondary", "id": "charts", "emoji": "📈"},
            ]
        elif self.current_state == PortfolioState.ASSET_DETAIL:
            return [
                {"label": "Voltar", "style": "secondary", "id": "back", "emoji": "⬅️"},
                {"label": "Gráfico", "style": "primary", "id": "chart", "emoji": "📊"},
            ]

        return []


# ═══════════════════════════════════════════════════════════════════════
# PortfolioPanelView
# ═══════════════════════════════════════════════════════════════════════
# PortfolioPanelView foi movido para portfolio_panel_view.py
# para manter responsabilidade única e evitar conflitos.
#
# Use: from .portfolio_panel_view import PortfolioPanelView
# ═══════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════
# Embed Creators
# ═══════════════════════════════════════════════════════════════════════

def create_reduced_panel_embed(portfolio: PortfolioReadModel) -> Embed:
    """
    Cria embed do painel reduzido (fixo).

    Sempre presente no tópico.
    """
    pnl = portfolio.lucro_prejuizo
    pnl_percent = portfolio.lucro_prejuizo_percentual

    # Cor baseada no PnL
    color = PortfolioColors.SUCCESS if pnl >= 0 else PortfolioColors.DANGER

    embed = Embed(
        title="📊 Meu Portfólio",
        description="Visão geral dos investimentos",
        color=color,
    )

    embed.add_field(
        name="💰 Valor Total",
        value=f"R$ {portfolio.valor_total:,.2f}",
        inline=True,
    )

    embed.add_field(
        name="📈 Lucro/Prejuízo",
        value=f"R$ {pnl:,.2f} ({pnl_percent:+.2f}%)",
        inline=True,
    )

    embed.add_field(
        name="📊 Ativos",
        value=str(len(portfolio.ativos)),
        inline=True,
    )

    embed.set_footer(text="Paper Trading – Dados simulados")

    return embed


def create_expanded_panel_embed(portfolio: PortfolioReadModel) -> Embed:
    """
    Cria embed do painel maximizado.

    Mostra todos os ativos com detalhes.
    """
    pnl = portfolio.lucro_prejuizo
    pnl_percent = portfolio.lucro_prejuizo_percentual
    total = portfolio.valor_total

    color = PortfolioColors.SUCCESS if pnl >= 0 else PortfolioColors.DANGER

    embed = Embed(
        title="📊 Meu Portfólio - Completo",
        description=f"Valor Total: R$ {total:,.2f} | PnL: {pnl_percent:+.2f}%",
        color=color,
    )

    # Adiciona até 5 ativos no embed
    for i, ativo in enumerate(portfolio.ativos[:5]):
        var_emoji = "📈" if ativo.variação_percentual >= 0 else "📉"

        value = (
            f"Qtd: {ativo.quantidade} | "
            f"PM: R$ {ativo.preco_medio:,.2f} | "
            f"PA: R$ {ativo.preco_atual:,.2f}\n"
            f"{var_emoji} {ativo.variação_percentual:+.2f}% | "
            f"PnL: R$ {ativo.lucro_prejuizo:,.2f}"
        )

        embed.add_field(
            name=f"{ativo.ticker}",
            value=value,
            inline=True if i % 2 == 0 else False,
        )

    if len(portfolio.ativos) > 5:
        embed.add_field(
            name="...",
            value=f"+{len(portfolio.ativos) - 5} ativos não exibidos",
            inline=False,
        )

    embed.set_footer(text="Paper Trading – Use /portfolio para mais opções")

    return embed


def create_asset_detail_embed(asset: AssetCardReadModel) -> Embed:
    """
    Cria embed com detalhes de um ativo específico.
    """
    var_emoji = "📈" if asset.variação_percentual >= 0 else "📉"
    tipo_emoji = {"Cripto": "₿", "Ação": "📈", "FII": "🏢"}.get(asset.tipo, "📊")

    color = PortfolioColors.SUCCESS if asset.lucro_prejuizo >= 0 else PortfolioColors.DANGER

    embed = Embed(
        title=f"{tipo_emoji} {asset.ticker} - {asset.nome}",
        description=f"Tipo: {asset.tipo}",
        color=color,
    )

    embed.add_field(
        name="Variação",
        value=f"{var_emoji} {asset.variação_percentual:+.2f}%",
        inline=True,
    )

    embed.add_field(
        name="Quantidade",
        value=str(asset.quantidade),
        inline=True,
    )

    embed.add_field(
        name="Preço Médio",
        value=f"R$ {asset.preco_medio:,.2f}",
        inline=True,
    )

    embed.add_field(
        name="Preço Atual",
        value=f"R$ {asset.preco_atual:,.2f}",
        inline=True,
    )

    embed.add_field(
        name="Valor Total",
        value=f"R$ {asset.valor_total:,.2f}",
        inline=True,
    )

    embed.add_field(
        name="💰 Lucro/Prejuízo",
        value=f"R$ {asset.lucro_prejuizo:,.2f}",
        inline=False,
    )

    embed.set_footer(text="Paper Trading – Dados simulados")

    return embed


# ═══════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════

def get_dynamic_embed(state_machine: PortfolioStateMachine) -> Embed:
    """
    Retorna embed dinâmico baseado no estado atual.

    Args:
        state_machine: Máquina de estados

    Returns:
        Embed correspondente ao estado
    """
    if state_machine.current_state == PortfolioState.MAIN:
        return create_reduced_panel_embed(state_machine.portfolio)
    elif state_machine.current_state == PortfolioState.EXPANDED:
        return create_expanded_panel_embed(state_machine.portfolio)
    elif state_machine.current_state == PortfolioState.ASSET_DETAIL:
        # Busca ativo selecionado
        if state_machine.selected_asset and state_machine.portfolio:
            asset = next(
                (a for a in state_machine.portfolio.ativos
                 if a.ticker == state_machine.selected_asset),
                None
            )
            if asset:
                return create_asset_detail_embed(asset)

    return create_reduced_panel_embed(state_machine.portfolio)


__all__ = [
    "PortfolioState",
    "PortfolioStateMachine",
    "create_reduced_panel_embed",
    "create_expanded_panel_embed",
    "create_asset_detail_embed",
    "get_dynamic_embed",
]
