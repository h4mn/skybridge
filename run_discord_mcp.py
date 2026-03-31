#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para executar o Discord MCP Server.

Uso:
    python run_discord_mcp.py

Variáveis de ambiente (opcional - pode usar .env):
    DISCORD_BOT_TOKEN: Token do bot Discord
    DISCORD_STATE_DIR: Diretório de estado (padrao: ~/.claude/channels/discord)
"""
import os
import sys
from pathlib import Path

# UTF-8 via variáveis de ambiente (NÃO manipula stdout/stderr diretamente)
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Adiciona src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Carrega .env do diretório de estado
state_dir = Path(os.environ.get("DISCORD_STATE_DIR", Path.home() / ".claude" / "channels" / "discord"))
env_file = state_dir / ".env"

if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value

# Verifica token
token = os.environ.get("DISCORD_BOT_TOKEN")
if not token:
    sys.exit(1)

# Executa o servidor
from src.core.discord.server import DiscordMCPServer
import asyncio

server = DiscordMCPServer()

try:
    asyncio.run(server.run(token))
except KeyboardInterrupt:
    pass
except Exception as e:
    import sys
    sys.stderr.write(f"[FATAL] {type(e).__name__}: {e}\n")
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
