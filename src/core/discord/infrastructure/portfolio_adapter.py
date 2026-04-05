# -*- coding: utf-8 -*-
"""
Discord Infrastructure - Portfolio Adapter.

Converte interações Discord em Commands do Paper Trading.
Segue padrão DDD: Discord (UI) → Adapter → Application Layer.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from datetime import datetime

import discord
from discord import InteractionType

# TYPE_CHECKING evita import circular em runtime
if TYPE_CHECKING:
    from src.core.paper.domain.events import EventBus
    from src.core.discord.presentation.portfolio_views import PortfolioMainView
else:
    EventBus = None
    PortfolioMainView = None


# ═══════════════════════════════════════════════════════════════════════
# Commands - Discord → Paper
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class PortfolioButtonClickCommand:
    """
    Command disparado ao clicar em botão do portfolio.

    Bridges Discord interaction → Paper query.
    """
    custom_id: str
    user_id: int
    channel_id: int

    # Query payload
    action: str  # "saldo", "completo", "alocacao", "config"
    currency: str = "BRL"  # Future: multi-currency

    @classmethod
    def from_discord_interaction(cls, interaction: discord.Interaction) -> "PortfolioButtonClickCommand":
        """Cria command a partir de interação Discord."""
        return cls(
            custom_id=interaction.data.get("custom_id", ""),
            user_id=interaction.user.id,
            channel_id=interaction.channel_id,
            action=cls._extract_action(interaction.data.get("custom_id", "")),
        )

    @staticmethod
    def _extract_action(custom_id: str) -> str:
        """Extrai ação do custom_id."""
        # custom_id format: "portfolio_<action>"
        parts = custom_id.split("_")
        return parts[1] if len(parts) > 1 else "unknown"


# ═══════════════════════════════════════════════════════════════════════
# Handler - Placeholder para integração futura
# ═══════════════════════════════════════════════════════════════════════

# TODO: Implementar handler real quando Paper Trading Module estiver pronto
# Por enquanto, as views usam dados mockados diretamente

class PortfolioInteractionHandler:
    """
    Handler placeholder para interações do portfolio Discord.

    NOTA: Integração com Paper Trading será implementada futuramente.
    Por enquanto, use PortfolioMainView diretamente com dados mockados.
    """
    pass


# ═══════════════════════════════════════════════════════════════════════
# Eventos - Analytics
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class PortfolioInteractionEvent:
    """
    Evento disparado ao interagir com portfolio Discord.

    Usado para analytics e debugging.
    """
    user_id: int
    action: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


__all__ = [
    "PortfolioInteractionHandler",
    "PortfolioButtonClickCommand",
    "PortfolioInteractionEvent",
]
