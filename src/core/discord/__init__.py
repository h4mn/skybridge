"""
Discord MCP Server - Integração Discord com Claude Code (DDD Architecture).

Este módulo implementa um servidor MCP (Model Context Protocol) que permite
ao Claude Code interagir com canais do Discord via tools.

Arquitetura DDD (Domain-Driven Design):
├── domain/           # Entidades, Value Objects, Events, Repositories
├── application/      # Commands, Queries, Handlers, Services
├── infrastructure/   # Adapters, Persistence
└── presentation/     # MCP Tools, DTOs

Estrutura Legacy (manteve para compatibilidade):
- server.py: MCP Server principal (atualizado para DDD)
- client.py: Discord client wrapper
- access.py: Controle de acesso (access.json)

Uso:
    python -m src.core.discord

Variáveis de ambiente:
    DISCORD_BOT_TOKEN: Token do bot Discord (obrigatório)
    DISCORD_STATE_DIR: Diretório de estado (opcional)

DOC: docs/spec/SPEC010-discord-ddd-migration.md
"""

__version__ = "2.0.0"  # DDD Architecture

# Lazy imports para evitar dependências circulares
__all__ = [
    # Core (DDD)
    "domain",
    "application",
    "infrastructure",
    "presentation",
    # Legacy compatibility
    "server",
    "client",
    "access",
]
