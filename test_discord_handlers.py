#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste simples do Discord client para verificar handlers.

Este script inicia o bot Discord e fica aguardando interações.
"""
import os
import sys
import io
import asyncio
from pathlib import Path

# =============================================================================
# FORÇAR UTF-8 NO WINDOWS
# =============================================================================
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
sys.stderr.reconfigure(encoding='utf-8') if hasattr(sys.stderr, 'reconfigure') else None
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Adiciona src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Carrega token
state_dir = Path(os.environ.get("DISCORD_STATE_DIR", Path.home() / ".claude" / "channels" / "discord"))
env_file = state_dir / ".env"

token = None
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            if key.strip() == "DISCORD_BOT_TOKEN":
                token = value.strip()
                break

if not token:
    token = os.environ.get("DISCORD_BOT_TOKEN")

if not token:
    print("[ERRO] DISCORD_BOT_TOKEN não encontrado!")
    sys.exit(1)

print("[TESTE] Iniciando Discord client...")

from discord import InteractionType
from src.core.discord.client import create_discord_client
from src.core.discord.application.services.event_publisher import EventPublisher
from src.core.discord.infrastructure.mcp_button_adapter import MCPButtonAdapter

discord_client = create_discord_client()

@discord_client.event
async def on_ready():
    print(f"[TESTE] === ON READY ===")
    print(f"[TESTE] Bot conectado: {discord_client.user}")

@discord_client.event
async def on_interaction_create(interaction):
    print(f"[TESTE] === INTERACTION CREATE ===")
    print(f"[TESTE] Type: {interaction.type}")
    print(f"[TESTE] Data: {interaction.data}")

    if interaction.type != InteractionType.component:
        print(f"[TESTE] Não é component, ignorando")
        return

    print(f"[TESTE] É COMPONENT! Custom ID: {interaction.data.get('custom_id', 'N/A')}")

    try:
        await interaction.response.defer()
        print(f"[TESTE] Defer OK!")
    except Exception as e:
        print(f"[TESTE] Erro no defer: {e}")
        return

    # Processar
    event_publisher = EventPublisher()
    button_adapter = MCPButtonAdapter(event_publisher)
    result = await button_adapter.handle_interaction(interaction)

    print(f"[TESTE] Resultado: {result}")

async def main():
    print("[TESTE] Fazendo login...")
    try:
        await discord_client.login(token)
    except Exception as e:
        print(f"[ERRO] Login falhou: {e}")
        return

    print("[TESTE] Conectando ao Gateway...")
    try:
        await discord_client.connect()
    except Exception as e:
        print(f"[ERRO] Connect falhou: {e}")
        return

    print("[TESTE] Bot rodando! Pressione Ctrl+C para parar.")

    # Mantém rodando
    try:
        await discord_client.wait_until_ready()
        print("[TESTE] Bot PRONTO!")
        await asyncio.Event().wait()  # Roda para sempre
    except KeyboardInterrupt:
        print("[TESTE] Interrompido")
    finally:
        await discord_client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[TESTE] Encerrado")
