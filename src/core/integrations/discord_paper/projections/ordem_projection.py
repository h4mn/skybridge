# -*- coding: utf-8 -*-
"""
Ordem Projection - Discord → Paper Integration.

Projeta estado de ordens para representação Discord.

DOC: DDD Migration - Integration Layer Projections
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from decimal import Decimal


class OrdemStatus(Enum):
    """Status de ordem para exibição."""
    PENDENTE = "pending"
    EXECUTADA = "executed"
    CANCELADA = "cancelled"
    REJEITADA = "rejected"


@dataclass
class OrdemEmbed:
    """Representação de ordem para embed Discord."""
    title: str
    symbol: str
    side: str  # "buy" ou "sell"
    quantity: Decimal
    price: Optional[Decimal]
    status: OrdemStatus
    order_id: str
    color: int

    def to_embed_dict(self) -> dict:
        """Converte para dict compatível com discord.Embed."""
        emoji_side = "🟢 COMPRA" if self.side == "buy" else "🔴 VENDA"
        emoji_status = self._status_emoji()

        fields = [
            {
                "name": "📊 Ativo",
                "value": f"**{self.symbol}**",
                "inline": True
            },
            {
                "name": "📈 Tipo",
                "value": emoji_side,
                "inline": True
            },
            {
                "name": "📦 Quantidade",
                "value": f"{self.quantity:.8f}",
                "inline": True
            }
        ]

        if self.price:
            fields.append({
                "name": "💰 Preço",
                "value": f"${self.price:,.2f}",
                "inline": True
            })

        fields.extend([
            {
                "name": "📋 Status",
                "value": emoji_status,
                "inline": True
            },
            {
                "name": "🆔 Order ID",
                "value": f"`{self.order_id}`",
                "inline": False
            }
        ])

        return {
            "title": self.title,
            "color": self.color,
            "fields": fields
        }

    def _status_emoji(self) -> str:
        """Retorna emoji baseado no status."""
        emojis = {
            OrdemStatus.PENDENTE: "⏳ Aguardando execução",
            OrdemStatus.EXECUTADA: "✅ Executada com sucesso",
            OrdemStatus.CANCELADA: "❌ Cancelada",
            OrdemStatus.REJEITADA: "⛔ Rejeitada"
        }
        return emojis.get(self.status, "❓ Desconhecido")


@dataclass
class ConfirmacaoOrdemButtons:
    """Botões de confirmação para ordem."""
    buttons: List[dict]

    @classmethod
    def create(cls, order_id: str, symbol: str) -> "ConfirmacaoOrdemButtons":
        """Cria botões de confirmação."""
        return cls(
            buttons=[
                {
                    "label": "✅ Confirmar",
                    "style": "success",
                    "custom_id": f"confirm_order_{order_id}"
                },
                {
                    "label": "❌ Cancelar",
                    "style": "danger",
                    "custom_id": f"cancel_order_{order_id}"
                }
            ]
        )


class OrdemProjection:
    """Projection do estado de ordens para Discord."""

    @staticmethod
    def project_ordem_confirmacao(
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Optional[Decimal],
        order_id: str
    ) -> tuple[OrdemEmbed, ConfirmacaoOrdemButtons]:
        """
        Projeta ordem pendente para embed de confirmação.

        Args:
            symbol: Símbolo do ativo
            side: "buy" ou "sell"
            quantity: Quantidade
            price: Preço (opcional para mercado)
            order_id: ID da ordem

        Returns:
            Tupla (OrdemEmbed, ConfirmacaoOrdemButtons)
        """
        emoji = "🟢" if side == "buy" else "🔴"
        title = f"{emoji} Ordem de {symbol.upper()}"

        return (
            OrdemEmbed(
                title=title,
                symbol=symbol.upper(),
                side=side,
                quantity=quantity,
                price=price,
                status=OrdemStatus.PENDENTE,
                order_id=order_id,
                color=16776960  # Amarelo para pendente
            ),
            ConfirmacaoOrdemButtons.create(order_id, symbol)
        )

    @staticmethod
    def project_ordem_executada(
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        order_id: str
    ) -> OrdemEmbed:
        """
        Projeta ordem executada.

        Args:
            symbol: Símbolo do ativo
            side: "buy" ou "sell"
            quantity: Quantidade executada
            price: Preço de execução
            order_id: ID da ordem

        Returns:
            OrdemEmbed com status executada
        """
        emoji = "✅" if side == "buy" else "✅"
        title = f"{emoji} Ordem Executada"

        return OrdemEmbed(
            title=title,
            symbol=symbol.upper(),
            side=side,
            quantity=quantity,
            price=price,
            status=OrdemStatus.EXECUTADA,
            order_id=order_id,
            color=3066993  # Verde para sucesso
        )

    @staticmethod
    def project_ordem_cancelada(order_id: str, reason: str = "") -> OrdemEmbed:
        """
        Projeta ordem cancelada.

        Args:
            order_id: ID da ordem
            reason: Motivo do cancelamento

        Returns:
            OrdemEmbed com status cancelada
        """
        title = "❌ Ordem Cancelada"

        embed = OrdemEmbed(
            title=title,
            symbol="N/A",
            side="N/A",
            quantity=Decimal(0),
            price=None,
            status=OrdemStatus.CANCELADA,
            order_id=order_id,
            color=15158332  # Vermelho para cancelada
        )

        if reason:
            # Adiciona motivo como campo extra
            pass  # TODO: implementar

        return embed
