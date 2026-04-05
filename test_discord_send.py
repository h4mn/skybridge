#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste direto de envio de mensagem com bot start."""
import asyncio
import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from dotenv import dotenv_values
from discord import Client, Intents, Embed
from discord.ui import View, Button, button
from discord import ButtonStyle

STATE_DIR = Path.home() / ".claude" / "channels" / "discord"
CHANNEL_ID = 1487929503073173727

class TestBot(Client):
    def __init__(self):
        super().__init__(intents=Intents.default())

    async def on_ready(self):
        print(f"Bot ready: {self.user}")

        # Teste 1: get_channel
        print("\n[TESTE 1] get_channel")
        ch1 = self.get_channel(CHANNEL_ID)
        print(f"get_channel result: {ch1}")

        # Teste 2: fetch_channel
        print("\n[TESTE 2] fetch_channel")
        try:
            ch2 = await self.fetch_channel(CHANNEL_ID)
            print(f"fetch_channel result: {ch2}")
        except Exception as e:
            print(f"fetch_channel error: {e}")
            return

        # Teste 3: Enviar mensagem simples
        print("\n[TESTE 3] send mensagem simples")
        try:
            msg = await ch2.send("Teste 1: mensagem simples")
            print(f"Mensagem enviada ID: {msg.id}")
        except Exception as e:
            print(f"Erro ao enviar: {e}")
            return

        # Teste 4: Enviar embed com botão
        print("\n[TESTE 4] send embed com botão")
        try:
            view = View()
            view.add_item(Button(label="Teste", style=ButtonStyle.primary))
            msg2 = await ch2.send(embed=Embed(title="Teste", description="Embed teste"), view=view)
            print(f"Botão enviado ID: {msg2.id}")
        except Exception as e:
            print(f"Erro ao enviar botão: {e}")
            return

        print("\n=== TODOS OS TESTES COMPLETADOS ===")

async def main():
    config = dotenv_values(STATE_DIR / ".env")
    token = config.get("DISCORD_BOT_TOKEN")
    if not token:
        print("ERRO: Sem token")
        return

    bot = TestBot()

    # Inicia bot em background
    asyncio.create_task(bot.start(token))

    # Aguarda bot ficar pronto
    print("Aguardando bot ready...")
    await bot.wait_until_ready()
    print("Bot está ready!")

    # Aguarda um pouco para on_ready completar
    await asyncio.sleep(2)

    # Encerra
    await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
