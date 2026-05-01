# -*- coding: utf-8 -*-
"""
Infrastructure Adapters - Adaptadores de infraestrutura Discord.

NOTA: discord_adapter depende de discord.py e nao e importado no nivel do
modulo para evitar colisao de namespace durante coleta do pytest.
Importar diretamente do submodulo:
    from src.core.discord.infrastructure.adapters.discord_adapter import DiscordAdapter
"""

from .mcp_adapter import MCPAdapter, create_mcp_adapter

__all__ = [
    "MCPAdapter",
    "create_mcp_adapter",
]
