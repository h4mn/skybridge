#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para validar posts no fórum
"""

import asyncio
import os
import discord
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
FORUM_ID = 1490026271445483762


async def validate_forum():
    """Valida posts no fórum"""

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        forum = client.get_channel(FORUM_ID)

        print(f"\n📋 FÓRUM: {forum.name}")
        print(f"🔗 URL: https://discord.com/channels/208357890317221888/{FORUM_ID}\n")

        # Listar tags
        print("🏷️  TAGS:")
        for tag in forum.tags:
            print(f"  {tag.emoji} {tag.name} (ID: {tag.id})")

        # Listar posts (threads no fórum)
        print(f"\n📝 POSTS ({len(forum_threads)}):")

        # Buscar threads ativas
        async for thread in forum.archived_threads(limit=None):
            pass

        async for thread in forum.active_threads(limit=None):
            print(f"  ✅ {thread.name} (ID: {thread.id})")
            print(f"     👤 Autor: {thread.owner_id}")
            print(f"     💬 {thread.message_count} mensagens")
            print()

        await client.close()

    await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(validate_forum())
