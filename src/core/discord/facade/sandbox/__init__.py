# -*- coding: utf-8 -*-
"""
Discord Facade - Sandbox.

Ambiente isolado para demonstrações e testes dos handlers Discord.

DOC: openspec/changes/discord-ddd-migration/specs/
"""

from .demo_handlers import demo_send_buttons, demo_send_embed, demo_send_message
from .demo_integration import demo_ordem_confirmation, demo_ordem_executed, demo_portfolio_notification, demo_risk_alert

__all__ = [
    # Handlers
    "demo_send_message",
    "demo_send_embed",
    "demo_send_buttons",
    # Integration
    "demo_portfolio_notification",
    "demo_ordem_confirmation",
    "demo_ordem_executed",
    "demo_risk_alert",
]
