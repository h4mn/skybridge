# -*- coding: utf-8 -*-
"""
Discord Facade.

Camada de fachada para acesso simplificado ao módulo Discord.

DOC: openspec/changes/discord-ddd-migration/specs/

Módulos:
- sandbox: Demos e testes interativos
- api: API FastAPI para debug HTTP
"""

from .sandbox import demo_send_buttons, demo_send_embed, demo_send_message

__all__ = [
    "demo_send_buttons",
    "demo_send_embed",
    "demo_send_message",
]
