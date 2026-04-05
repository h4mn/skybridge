# -*- coding: utf-8 -*-
"""
Discord Slash Commands

Comandos nativos do Discord com autocomplete usando discord.py app_commands.
"""

from .inbox_slash import setup_inbox_command

__all__ = [
    "setup_inbox_command",
]
