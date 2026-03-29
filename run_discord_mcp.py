#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para executar o Discord MCP Server.

Uso:
    python run_discord_mcp.py

Variaveis de ambiente (opcional - pode usar .env):
    DISCORD_BOT_TOKEN: Token do bot Discord
    DISCORD_STATE_DIR: Diretorio de estado (padrao: ~/.claude/channels/discord)
"""
import os
import sys
import io
from pathlib import Path

# =============================================================================
# FORCAR UTF-8 NO WINDOWS
# =============================================================================
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Adiciona src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Carrega .env do diretório de estado
state_dir = Path(os.environ.get("DISCORD_STATE_DIR", Path.home() / ".claude" / "channels" / "discord"))
env_file = state_dir / ".env"

if env_file.exists():
    print(f"[INFO] Carregando variáveis de {env_file}")
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
    print("[ERRO] DISCORD_BOT_TOKEN não configurado!")
    print(f"\nCrie o arquivo {env_file} com:")
    print('DISCORD_BOT_TOKEN="seu_token_aqui"')
    sys.exit(1)

print(f"[INFO] Iniciando Discord MCP Server...")
print(f"[INFO] State dir: {state_dir}")

# Executa o servidor
from src.core.discord.server import DiscordMCPServer
import asyncio

server = DiscordMCPServer()

try:
    asyncio.run(server.run(token))
except KeyboardInterrupt:
    print("\n[INFO] Interrompido pelo usuário")
except Exception as e:
    print(f"[ERRO] {e}")
    sys.exit(1)
