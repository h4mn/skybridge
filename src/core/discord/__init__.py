"""
Discord MCP Server - Integração Discord com Claude Code.

Este módulo implementa um servidor MCP (Model Context Protocol) que permite
ao Claude Code interagir com canais do Discord via tools.

Estrutura:
- server.py: MCP Server principal
- client.py: Discord client wrapper
- access.py: Controle de acesso (access.json)
- models.py: Modelos Pydantic
- tools/: MCP Tools (reply, fetch_messages, create_thread, etc.)

Uso:
    python -m src.core.discord

Variáveis de ambiente:
    DISCORD_BOT_TOKEN: Token do bot Discord (obrigatório)
    DISCORD_STATE_DIR: Diretório de estado (opcional)
"""

__version__ = "0.1.0"

# Lazy imports para evitar dependências circulares e importar apenas quando necessário
# Use imports diretos nos módulos: from .access import load_access
__all__ = [
    "server",
    "client",
    "access",
    "models",
    "tools",
]
