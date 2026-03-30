# -*- coding: utf-8 -*-
"""
Discord Facade.

Camada de fachada para acesso simplificado ao módulo Discord.

DOC: openspec/changes/discord-ddd-migration/specs/
"""

from .sandbox import demo_send_buttons, demo_send_embed, demo_send_message

__all__ = [
    "demo_send_buttons",
    "demo_send_embed",
    "demo_send_message",
]
