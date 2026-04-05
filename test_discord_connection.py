#!/usr/bin/env python
"""Teste se o Discord client está conectado."""
import os
import sys
import asyncio
from pathlib import Path

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from core.discord.client import create_discord_client

async def test():
    client = create_discord_client()

    # Tenta conectar
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        # Lê do .env
        state_dir = Path.home() / ".claude" / "channels" / "discord"
        env_file = state_dir / ".env"
        if env_file.exists():
            for line in env_file.read_text().split("\n"):
                if "DISCORD_BOT_TOKEN=" in line:
                    token = line.split("=", 1)[1].strip()
                    break

    if not token:
        print("ERRO: Token não encontrado")
        return

    print(f"Token: {token[:20]}...")

    # Login
    print("Fazendo login...")
    await client.login(token)
    print("Login OK")

    # Connect
    print("Conectando...")
    await client.connect()
    print("Connect OK")

    # Wait ready
    print("Aguardando ready...")
    await client.wait_until_ready()
    print(f"Ready! User: {client.user}")

    # Testa fetch channel
    print("\nTestando fetch_channel...")
    channel = await client.fetch_channel(1487929503073173727)
    print(f"Channel: {channel.name} ({channel.id})")

    await client.close()

if __name__ == "__main__":
    asyncio.run(test())
