#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para executar o Discord MCP Server.

Uso:
    python run_discord_mcp.py

Variáveis de ambiente (carregadas do .env da Skybridge):
    DISCORD_BOT_TOKEN: Token do bot Discord (obrigatório)
    LINEAR_API_KEY: API Key do Linear para comandos /inbox

NOTA: Carrega APENAS o .env da Skybridge localizado na raiz do projeto.
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

# =============================================================================
# Carrega APENAS o .env da Skybridge
# =============================================================================
# O .env do projeto Skybridge contém TODAS as configurações necessárias
# including LINEAR_API_KEY, DISCORD_BOT_TOKEN, etc.
skybridge_env = Path(__file__).parent / ".env"
if skybridge_env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(skybridge_env)
        print(f"[Discord MCP] Carregado .env da Skybridge: {skybridge_env}", file=sys.stderr)
    except ImportError:
        # python-dotenv não disponível, fazer parsing manual
        for line in skybridge_env.read_text(encoding="utf-8").split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key and key not in os.environ:
                    os.environ[key] = value
else:
    print(f"[Discord MCP] AVISO: .env da Skybridge não encontrado em {skybridge_env}", file=sys.stderr)

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
