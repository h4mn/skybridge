# -*- coding: utf-8 -*-
"""
Discord Slash Commands

Comandos nativos do Discord com autocomplete usando discord.py app_commands.
"""

from .inbox_slash import create_inbox_tree, setup_inbox_commands

__all__ = [
    "create_inbox_tree",
    "setup_inbox_commands",
]
