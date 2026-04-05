# -*- coding: utf-8 -*-
"""
Portfolio Projection - Discord → Paper Integration.

Projeta estado do Paper Trading para representação Discord.

DOC: DDD Migration - Integration Layer Projections
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal


@dataclass
class PortfolioEmbed:
    """Representação de portfolio para embed Discord."""
    title: str
    balance_btc: Decimal
    balance_usd: Decimal
    positions: List[dict]
    pnl_percent: float
    color: int = 3447003  # Azul padrão

    def to_embed_dict(self) -> dict:
        """Converte para dict compatível com discord.Embed."""
        fields = [
            {
                "name": "💰 Saldo BTC",
                "value": f"{self.balance_btc:.8f} BTC",
                "inline": True
            },
            {
                "name": "💵 Saldo USD",
                "value": f"${self.balance_usd:,.2f} USD",
                "inline": True
            },
            {
                "name": "📈 P&L",
                "value": f"{self.pnl_percent:+.2f}%",
                "inline": True
            }
        ]

        # Adiciona posições
        for pos in self.positions[:5]:  # Máximo 5 posições
            symbol = pos.get("symbol", "N/A")
            side = "🟢 Long" if pos.get("side") == "long" else "🔴 Short"
            pnl = pos.get("pnl_percent", 0)
            fields.append({
                "name": f"{side} {symbol}",
                "value": f"P&L: {pnl:+.2f}%",
                "inline": True
            })

        return {
            "title": self.title,
            "description": f"Portfolio Paper Trading",
            "color": self.color,
            "fields": fields
        }


@dataclass
class PortfolioMenuOptions:
    """Opções de menu para portfolio."""
    options: List[dict]

    @classmethod
    def from_portfolio(cls, has_positions: bool) -> "PortfolioMenuOptions":
        """Cria opções baseadas no estado do portfolio."""
        options = [
            {
                "label": "📊 Ver Resumo",
                "value": "portfolio_summary",
                "description": "Mostrar resumo completo do portfolio"
            },
            {
                "label": "📈 Ver Gráficos",
                "value": "portfolio_charts",
                "description": "Mostrar gráficos de desempenho"
            }
        ]

        if has_positions:
            options.extend([
                {
                    "label": "📋 Minhas Posições",
                    "value": "portfolio_positions",
                    "description": "Listar todas as posições abertas"
                },
                {
                    "label": "🔒 Fechar Posição",
                    "value": "close_position",
                    "description": "Fechar uma posição específica"
                }
            ])

        options.append({
            "label": "⚙️ Configurações",
            "value": "portfolio_settings",
            "description": "Abrir configurações do portfolio"
        })

        return cls(options=options)


class PortfolioProjection:
    """Projection do estado Paper Trading para Discord."""

    @staticmethod
    def project_embed(
        balance_btc: Decimal,
        balance_usd: Decimal,
        positions: List[dict],
        pnl_percent: float
    ) -> PortfolioEmbed:
        """
        Projeta estado do portfolio para embed Discord.

        Args:
            balance_btc: Saldo em BTC
            balance_usd: Saldo em USD
            positions: Lista de posições abertas
            pnl_percent: P&L percentual total

        Returns:
            PortfolioEmbed pronto para enviar via send_embed
        """
        # Define cor baseada no P&L
        if pnl_percent > 0:
            color = 3066993  # Verde
        elif pnl_percent < 0:
            color = 15158332  # Vermelho
        else:
            color = 3447003  # Azul

        return PortfolioEmbed(
            title="📊 Portfolio Paper Trading",
            balance_btc=balance_btc,
            balance_usd=balance_usd,
            positions=positions,
            pnl_percent=pnl_percent,
            color=color
        )

    @staticmethod
    def project_menu(has_positions: bool) -> PortfolioMenuOptions:
        """
        Projeta opções de menu baseadas no estado.

        Args:
            has_positions: Se há posições abertas

        Returns:
            PortfolioMenuOptions com opções dinâmicas
        """
        return PortfolioMenuOptions.from_portfolio(has_positions)
