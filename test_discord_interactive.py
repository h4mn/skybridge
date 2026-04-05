#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste interativo do Discord MCP - conecta ao Discord diretamente.

Uso:
    python test_discord_interactive.py

Envia uma mensagem de teste para um canal configurado.
"""
import asyncio
import os
import sys
from pathlib import Path

# Adiciona src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Carrega .env
state_dir = Path(os.environ.get("DISCORD_STATE_DIR", Path.home() / ".claude" / "channels" / "discord"))
env_file = state_dir / ".env"

if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            if key and key not in os.environ:
                os.environ[key] = value.strip()

import discord
from discord import Intents

# Intents necessarios
intents = Intents.default()
intents.message_content = True
intents.guilds = True
intents.dm_messages = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"\n[OK] Conectado como: {client.user}")
    print(f"[OK] ID do bot: {client.user.id}")

    # Lista servidores
    print(f"\n Servidores ({len(client.guilds)}):")
    for guild in client.guilds:
        print(f"  - {guild.name} (ID: {guild.id})")

    # Lista canais de texto
    print("\n Canais de texto:")
    for guild in client.guilds:
        for channel in guild.text_channels:
            perms = channel.permissions_for(guild.me)
            if perms.send_messages:
                print(f"  - #{channel.name} (ID: {channel.id}) [{guild.name}]")

    print("\n Para testar envio de mensagem:")
    print("  1. Adicione o channel_id ao access.json em groups")
    print("  2. Use o tool reply via MCP")

    await client.close()

@client.event
async def on_error(event, *args, **kwargs):
    print(f"[ERRO] {event}")

def main():
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("[ERRO] DISCORD_BOT_TOKEN nao configurado")
        sys.exit(1)

    print("[INFO] Conectando ao Discord...")
    client.run(token)

if __name__ == "__main__":
    main()
