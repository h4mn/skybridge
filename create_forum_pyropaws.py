#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script temporário para criar fórum no PyroPaws
"""

import asyncio
import os
import discord
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 208357890317221888


async def create_forum():
    """Cria o fórum de moderadores no PyroPaws"""

    intents = discord.Intents.default()
    intents.guilds = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Bot conectado como {client.user}")

        guild = client.get_guild(GUILD_ID)
        if not guild:
            print("Guild não encontrada!")
            await client.close()
            return

        print(f"Guild: {guild.name}")

        # Criar fórum
        try:
            forum_channel = await guild.create_forum(
                name="moderadores-hub",
                reason="Fórum para moderadores do PyroPaws"
            )
            print(f"✅ Fórum criado: {forum_channel.name} (ID: {forum_channel.id})")
            print(f"URL: https://discord.com/channels/{GUILD_ID}/{forum_channel.id}")
        except Exception as e:
            print(f"❌ Erro ao criar fórum: {e}")

        await client.close()

    await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(create_forum())
