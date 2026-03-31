# -*- coding: utf-8 -*-
"""
Ordem UI Handler - Discord → Paper Integration.

Manipula eventos de UI relacionados a ordens.

DOC: DDD Migration - Integration Layer Handlers
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from ..projections.ordem_projection import (
    OrdemProjection,
    OrdemEmbed,
    ConfirmacaoOrdemButtons,
    OrdemStatus
)

if TYPE_CHECKING:
    from src.core.discord.application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)


class OrdemUIHandler:
    """Handler para eventos de UI de ordens."""

    def __init__(self, discord_service: "DiscordService"):
        """
        Inicializa handler.

        Args:
            discord_service: Instância do DiscordService
        """
        self._discord = discord_service
        self._projection = OrdemProjection()
        self._pending_confirmations: dict[str, dict] = {}  # order_id -> dados

    async def send_ordem_confirmacao(
        self,
        channel_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float],
        order_id: str
    ) -> str:
        """
        Envia solicitação de confirmação de ordem.

        Args:
            channel_id: ID do canal Discord
            symbol: Símbolo do ativo
            side: "buy" ou "sell"
            quantity: Quantidade
            price: Preço (None para mercado)
            order_id: ID da ordem

        Returns:
            ID da mensagem enviada
        """
        from decimal import Decimal

        # Projeta embed e botões
        embed, buttons = self._projection.project_ordem_confirmacao(
            symbol=symbol,
            side=side,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)) if price else None,
            order_id=order_id
        )

        # Converte embed para dict
        embed_dict = embed.to_embed_dict()

        # Converte botões
        from src.core.discord.application.services.discord_service import ButtonConfig
        button_configs = [
            ButtonConfig(
                label=btn["label"],
                style=btn["style"],
                custom_id=btn["custom_id"]
            )
            for btn in buttons.buttons
        ]

        # Envia via DiscordService
        message = await self._discord.send_buttons(
            channel_id=channel_id,
            title=embed_dict["title"],
            buttons=button_configs,
            embed_data={
                "color": embed_dict["color"],
                "fields": embed_dict["fields"]
            }
        )

        # Guarda confirmação pendente
        self._pending_confirmations[order_id] = {
            "channel_id": channel_id,
            "message_id": str(message.id) if message else "",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price
        }

        logger.info(f"Confirmação de ordem {order_id} enviada para {channel_id}")
        return str(message.id) if message else ""

    async def send_ordem_executada(
        self,
        channel_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_id: str
    ) -> str:
        """
        Envia notificação de ordem executada.

        Args:
            channel_id: ID do canal Discord
            symbol: Símbolo do ativo
            side: "buy" ou "sell"
            quantity: Quantidade executada
            price: Preço de execução
            order_id: ID da ordem

        Returns:
            ID da mensagem enviada
        """
        from decimal import Decimal

        embed = self._projection.project_ordem_executada(
            symbol=symbol,
            side=side,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            order_id=order_id
        )

        # Converte para dict
        embed_dict = embed.to_embed_dict()

        # Remove confirmação pendente se existir
        self._pending_confirmations.pop(order_id, None)

        # Envia embed
        message = await self._discord.send_embed(
            channel_id=channel_id,
            title=embed_dict["title"],
            color=embed_dict["color"],
            fields=embed_dict["fields"]
        )

        logger.info(f"Ordem {order_id} executada notificada em {channel_id}")
        return str(message.id) if message else ""

    async def send_ordem_cancelada(
        self,
        channel_id: str,
        order_id: str,
        reason: str = ""
    ) -> str:
        """
        Envia notificação de ordem cancelada.

        Args:
            channel_id: ID do canal Discord
            order_id: ID da ordem
            reason: Motivo do cancelamento

        Returns:
            ID da mensagem enviada
        """
        embed = self._projection.project_ordem_cancelada(
            order_id=order_id,
            reason=reason
        )

        # Converte para dict
        embed_dict = embed.to_embed_dict()

        # Remove confirmação pendente se existir
        self._pending_confirmations.pop(order_id, None)

        # Envia embed
        message = await self._discord.send_embed(
            channel_id=channel_id,
            title=embed_dict["title"],
            color=embed_dict["color"],
            fields=embed_dict["fields"]
        )

        logger.info(f"Ordem {order_id} cancelada notificada em {channel_id}")
        return str(message.id) if message else ""

    async def handle_ordem_confirmation(self, custom_id: str, confirmed: bool) -> None:
        """
        Manipula resposta de confirmação de ordem.

        Args:
            custom_id: ID customizado do botão (ex: "confirm_order_123")
            confirmed: Se usuário confirmou (True) ou cancelou (False)
        """
        # Extrai order_id do custom_id
        parts = custom_id.split("_")
        if len(parts) < 3 or parts[0] not in ["confirm", "cancel"]:
            logger.warning(f"Custom ID inválido: {custom_id}")
            return

        action = parts[0]  # "confirm" ou "cancel"
        order_id = parts[2]  # ID da ordem

        # Busca dados pendentes
        pending = self._pending_confirmations.get(order_id)
        if not pending:
            logger.warning(f"Nenhuma confirmação pendente para ordem {order_id}")
            return

        # Processa confirmação
        if action == "confirm" and confirmed:
            await self._process_ordem_confirmada(order_id, pending)
        else:
            await self._process_ordem_rejeitada(order_id, pending)

    async def _process_ordem_confirmada(self, order_id: str, pending: dict) -> None:
        """Processa ordem confirmada pelo usuário."""
        logger.info(f"Ordem {order_id} confirmada pelo usuário")

        # TODO: Enviar confirmação para Paper Trading module
        # Isso será implementado na integração completa

        await self._discord.send_message(
            channel_id=pending["channel_id"],
            content=f"✅ Ordem confirmada! Enviando para execução...\nOrder ID: `{order_id}`"
        )

    async def _process_ordem_rejeitada(self, order_id: str, pending: dict) -> None:
        """Processa ordem cancelada pelo usuário."""
        logger.info(f"Ordem {order_id} cancelada pelo usuário")

        await self.send_ordem_cancelada(
            channel_id=pending["channel_id"],
            order_id=order_id,
            reason="Cancelada pelo usuário"
        )

        # Desabilita botões da mensagem original
        if pending.get("message_id"):
            await self._discord.edit_message(
                channel_id=pending["channel_id"],
                message_id=pending["message_id"],
                content="❌ Ordem cancelada"
            )
            # TODO: Adicionar método para desabilitar botões (update_component)

    def get_pending_confirmation(self, order_id: str) -> Optional[dict]:
        """
        Retorna dados de confirmação pendente.

        Args:
            order_id: ID da ordem

        Returns:
            Dict com dados pendentes ou None
        """
        return self._pending_confirmations.get(order_id)

    def clear_pending_confirmation(self, order_id: str) -> None:
        """
        Remove confirmação pendente.

        Args:
            order_id: ID da ordem
        """
        self._pending_confirmations.pop(order_id, None)
