# -*- coding: utf-8 -*-
"""
Portfolio UI Handler - Discord → Paper Integration.

Manipula eventos de UI relacionados ao portfolio.

DOC: DDD Migration - Integration Layer Handlers
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..projections.portfolio_projection import PortfolioProjection, PortfolioEmbed, PortfolioMenuOptions

if TYPE_CHECKING:
    from src.core.discord.application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


class PortfolioUIHandler:
    """Handler para eventos de UI do portfolio."""

    def __init__(self, discord_service: "DiscordService"):
        """
        Inicializa handler.

        Args:
            discord_service: Instância do DiscordService
        """
        self._discord = discord_service
        self._projection = PortfolioProjection()

    async def send_portfolio_embed(
        self,
        channel_id: str,
        balance_btc: float,
        balance_usd: float,
        positions: list[dict],
        pnl_percent: float
    ) -> str:
        """
        Envia embed do portfolio para canal Discord.

        Args:
            channel_id: ID do canal Discord
            balance_btc: Saldo em BTC
            balance_usd: Saldo em USD
            positions: Lista de posições
            pnl_percent: P&L percentual

        Returns:
            ID da mensagem enviada
        """
        from decimal import Decimal

        # Projeta embed
        embed = self._projection.project_embed(
            balance_btc=Decimal(str(balance_btc)),
            balance_usd=Decimal(str(balance_usd)),
            positions=positions,
            pnl_percent=pnl_percent
        )

        # Converte para dict (compatível com discord.Embed)
        embed_dict = embed.to_embed_dict()

        # Envia via DiscordService
        message = await self._discord.send_embed(
            channel_id=channel_id,
            title=embed_dict["title"],
            description=embed_dict.get("description", ""),
            color=embed_dict["color"],
            fields=embed_dict.get("fields", []),
        )

        logger.info(f"Portfolio embed enviado para {channel_id}")
        return str(message.id) if message else ""

    async def send_portfolio_menu(
        self,
        channel_id: str,
        has_positions: bool
    ) -> str:
        """
        Envia menu de opções do portfolio.

        Args:
            channel_id: ID do canal Discord
            has_positions: Se há posições abertas

        Returns:
            ID da mensagem enviada
        """
        from src.core.discord.application.services.discord_service import ButtonConfig

        # Projeta menu
        menu = self._projection.project_menu(has_positions=has_positions)

        # Converte opções para botões
        buttons = [
            ButtonConfig(
                label=opt["label"].split(" ", 1)[1],  # Remove emoji
                style="primary",
                custom_id=opt["value"],
            )
            for opt in menu.options
        ]

        # Envia via DiscordService
        message = await self._discord.send_buttons(
            channel_id=channel_id,
            title="📋 Menu Portfolio",
            description="Escolha uma ação:",
            buttons=buttons,
        )

        logger.info(f"Portfolio menu enviado para {channel_id}")
        return str(message.id) if message else ""

    async def update_portfolio_progress(
        self,
        channel_id: str,
        tracking_id: str,
        current: int,
        total: int,
        status: str
    ) -> None:
        """
        Atualiza barra de progresso de operação de portfolio.

        Args:
            channel_id: ID do canal Discord
            tracking_id: ID de rastreamento (para atualizar mesma mensagem)
            current: Valor atual
            total: Valor total
            status: Status da operação
        """
        await self._discord.send_progress(
            channel_id=channel_id,
            title="⏳ Processando Portfolio",
            current=current,
            total=total,
            status=status,
            tracking_id=tracking_id
        )

        logger.debug(f"Progresso atualizado: {current}/{total} - {status}")

    async def handle_portfolio_selection(self, selection: str, channel_id: str) -> None:
        """
        Manipula seleção no menu do portfolio.

        Args:
            selection: Valor selecionado
            channel_id: ID do canal Discord
        """
        handlers = {
            "portfolio_summary": self._handle_summary,
            "portfolio_charts": self._handle_charts,
            "portfolio_positions": self._handle_positions,
            "close_position": self._handle_close_position,
            "portfolio_settings": self._handle_settings,
        }

        handler = handlers.get(selection)
        if handler:
            await handler(channel_id)
        else:
            logger.warning(f"Seleção desconhecida: {selection}")

    async def _handle_summary(self, channel_id: str) -> None:
        """Manipula solicitação de resumo."""
        await self._discord.send_message(
            channel_id=channel_id,
            content="📊 **Resumo do Portfolio**\n\nCarregando dados..."
        )

    async def _handle_charts(self, channel_id: str) -> None:
        """Manipula solicitação de gráficos."""
        await self._discord.send_message(
            channel_id=channel_id,
            content="📈 **Gráficos de Desempenho**\n\nGerando visualizações..."
        )

    async def _handle_positions(self, channel_id: str) -> None:
        """Manipula solicitação de posições."""
        await self._discord.send_message(
            channel_id=channel_id,
            content="📋 **Posições Abertas**\n\nCarregando lista..."
        )

    async def _handle_close_position(self, channel_id: str) -> None:
        """Manipula solicitação de fechar posição."""
        await self._discord.send_message(
            channel_id=channel_id,
            content="🔒 **Fechar Posição**\n\nSelecione a posição:"
        )

    async def _handle_settings(self, channel_id: str) -> None:
        """Manipula solicitação de configurações."""
        await self._discord.send_message(
            channel_id=channel_id,
            content="⚙️ **Configurações**\n\nCarregando opções..."
        )
