# -*- coding: utf-8 -*-
"""
Bot de Teste de Botões - Simples e funcional.

Mantém botões ativos e responde a cliques sem erros.
"""

import asyncio
import os
from dotenv import load_dotenv

import discord
from discord import Embed, InteractionType

load_dotenv()

# CANAL ALVO
CANAL_ALVO = "1487929503073173727"  # Discord Redesign


class BotTeste(discord.Client):
    """Bot simples para testar botões."""

    def __init__(self):
        # Intents - IMPORTANTE: integrations é necessário para botões
        intents = discord.Intents.default()
        intents.message_content = True
        intents.integrations = True  # <<< NECESSÁRIO PARA BOTÕES!
        super().__init__(intents=intents)

    async def on_ready(self):
        """Quando bot está pronto."""
        print(f"\n{'='*60}")
        print(f"[OK] BOT CONECTADO: {self.user}")
        print(f"{'='*60}\n")

        # Enviar botões
        await self.enviar_botoes()

        print(f"\n{'='*60}")
        print(f"BOT RODANDO - Teste os botões agora!")
        print(f"Canal: {CANAL_ALVO} (Discord Redesign)")
        print(f"{'='*60}\n")

    async def on_interaction_create(self, interaction):
        """Handler de interação - RESPONDE CLIQUES!"""
        print(f"\n[INTERAÇÃO] Tipo: {interaction.type}")

        # Apenas componentes (botões)
        if interaction.type == InteractionType.component:
            custom_id = getattr(interaction.data, 'custom_id', None)
            print(f"[BOTÃO] Custom ID: {custom_id}")
            print(f"[BOTÃO] Usuário: {interaction.user.name}")

            # ACKNOWLEDGE - evita "Esta interação falhou"
            try:
                await interaction.response.send_message(
                    f"[OK] **{interaction.user.name}** clicou em: `{custom_id}`",
                    ephemeral=False  # Todos veem
                )
                print(f"[SUCESSO] Acknowledge enviado!")

            except Exception as e:
                print(f"[ERRO] {e}")
                # Tentar defer como fallback
                try:
                    await interaction.response.defer()
                    print(f"[FALLBACK] Defer funcionou")
                except:
                    print(f"[ERRO CRÍTICO] Falha total no acknowledge")

    async def enviar_botoes(self):
        """Envia os botões para o canal."""
        try:
            channel = await self.fetch_channel(CANAL_ALVO)
            print(f"\n[ENVIO] Canal: {channel.name}")

            # Botões de confirmação
            embed = Embed(
                title="Teste de Botões",
                description="Clique nos botões abaixo para testar.",
                color=3447003  # Azul
            )

            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label="✅ Confirmar",
                style=discord.ButtonStyle.success,
                custom_id="btn_confirmar"
            ))
            view.add_item(discord.ui.Button(
                label="❌ Cancelar",
                style=discord.ButtonStyle.danger,
                custom_id="btn_cancelar"
            ))

            await channel.send(embed=embed, view=view)
            print("[ENVIO] Botões enviados com sucesso!")

        except Exception as e:
            print(f"[ERRO] Falha ao enviar: {e}")


async def main():
    """Ponto de entrada."""
    token = os.getenv("DISCORD_TOKEN") or os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        print("ERRO: Token não encontrado!")
        return

    print("\nIniciando bot de teste...")

    bot = BotTeste()

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("\n\nBot encerrado.")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
