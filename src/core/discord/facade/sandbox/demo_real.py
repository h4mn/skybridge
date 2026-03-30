# -*- coding: utf-8 -*-
"""
Demo Real - Envia mensagens para o Discord!

Este script conecta ao bot Discord e envia mensagens EMBEDS reais.
"""

import asyncio
import logging
from pathlib import Path

import discord
from discord import Embed
from dotenv import load_dotenv

# Adicionar caminho do projeto ao sys.path
import sys
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.discord.access import load_access


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscordBot(discord.Client):
    """Bot Discord para demonstracoes."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.integrations = True  # OBRIGATÓRIO para botões funcionarem!
        super().__init__(intents=intents)
        self.is_ready = False

    async def setup_hook(self):
        """Quando o bot esta pronto."""
        logger.info(f"Bot conectado como {self.user}")

    async def on_ready(self):
        """Quando o bot está pronto para uso."""
        logger.info(f"Bot pronto! Conectado como {self.user}")
        self.is_ready = True

    async def on_interaction_create(self, interaction):
        """
        Handler para interacoes (botoes).

        Processa cliques de botao e faz acknowledge para evitar timeout.
        """
        try:
            # Apenas interacoes de componente (botoes)
            if interaction.type != discord.InteractionType.component:
                return

            # Extrair custom_id do botao
            custom_id = getattr(interaction.data, 'custom_id', None)
            if not custom_id:
                return

            # Fazer acknowledge para evitar "Esta interacao falhou"
            try:
                await interaction.response.acknowledge()
                logger.info(
                    f"✓ Botao clicado: {custom_id} "
                    f"por {interaction.user.name} ({interaction.user.id}) "
                    f"no canal {interaction.channel_id}"
                )
            except Exception:
                # Se acknowledge falhar, tenta defer
                try:
                    await interaction.response.defer()
                except Exception as e:
                    logger.error(f"Erro ao responder interacao: {e}")
                    return

        except Exception as e:
            logger.error(f"Erro no handler de interacao: {e}")


async def send_demo_embed(bot: DiscordBot, channel_id: str):
    """Envia embed de demonstracao."""
    try:
        logger.info(f"Buscando canal {channel_id}...")
        channel = await bot.fetch_channel(channel_id)
        logger.info(f"Canal encontrado: {channel.name}")
    except Exception as e:
        logger.error(f"Erro ao buscar canal: {e}")
        raise

    try:
        # Embed VERDE (portfolio positivo)
        embed1 = Embed(
            title="Portfolio Atualizado",
            description="Seu portfolio foi atualizado com novos precos.",
            color=65280,  # Verde
        )
        embed1.add_field(name="Saldo", value="R$ 50.000,00", inline=True)
        embed1.add_field(name="PnL", value="R$ 3.500,00 (+7.5%)", inline=True)
        embed1.add_field(name="Posicoes", value="2 ativos", inline=False)
        embed1.set_footer(text="Paper Trading via Discord DDD")

        await channel.send(embed=embed1)
        logger.info("✓ Embed de portfolio enviado!")

        # EMBED DE CONFIRMACAO DE ORDEM
        embed2 = Embed(
            title="Confirmar Ordem",
            description="Deseja confirmar esta operacao?",
            color=3447003,  # Azul
        )
        embed2.add_field(name="Ativo", value="PETR4", inline=True)
        embed2.add_field(name="Quantidade", value="100", inline=True)
        embed2.add_field(name="Preco", value="R$ 38,50", inline=True)
        embed2.add_field(name="Total", value="R$ 3.850,00", inline=False)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Confirmar",
            style=discord.ButtonStyle.success,
            custom_id="ordem_confirm",
        ))
        view.add_item(discord.ui.Button(
            label="Cancelar",
            style=discord.ButtonStyle.danger,
            custom_id="ordem_cancel",
        ))

        await channel.send(embed=embed2, view=view)
        logger.info("✓ Botoes de confirmacao enviados!")

        # EMBED DE ALERTA (VERMELHO)
        embed3 = Embed(
            title="ALERTA DE RISCO",
            description="Limite de perda maxima diaria atingido!",
            color=16711680,  # Vermelho
        )
        embed3.add_field(name="Tipo", value="PERDA_MAXIMA_DIA", inline=True)
        embed3.add_field(name="Perda", value="-5.2%", inline=True)
        embed3.add_field(name="Valor", value="R$ -2.500,00", inline=True)
        embed3.add_field(name="Limite", value="-5.0%", inline=True)
        embed3.set_footer(text="Sistema de Gestao de Riscos")

        await channel.send(embed=embed3)
        logger.info("✓ Alerta de risco enviado!")
    except Exception as e:
        logger.error(f"Erro ao enviar embeds: {e}")
        raise


async def main():
    """Executa a demo real."""
    import sys

    # Carregar variaveis de ambiente do .env
    load_dotenv()

    # Carregar configuracoes
    access = load_access()

    # Verificar canais autorizados
    if not access.groups:
        print("ERRO: Nenhum canal configurado em access.json!")
        print("Use: /discord:access para configurar")
        return

    # Lista canais disponiveis
    channel_ids = list(access.groups.keys())
    print("=" * 60)
    print("DEMO REAL - ENVIANDO CARDS PARA O DISCORD")
    print("=" * 60)
    print("Canais disponiveis:")
    for i, channel_id in enumerate(channel_ids):
        group = access.groups[channel_id]
        print(f"  {i + 1}. {channel_id} ({len(group.allow_from) if group.allow_from else 0} usuarios autorizados)")

    print()

    # Escolher canal (automatico em modo non-interactive)
    if len(sys.argv) > 1:
        try:
            choice = int(sys.argv[1]) - 1
            channel_id = channel_ids[choice]
        except (ValueError, IndexError):
            print("Argumento invalido! Usando primeiro canal.")
            channel_id = channel_ids[0]
    elif not sys.stdin.isatty():
        # Modo non-interactive (pipe, etc)
        print("Modo non-interactive detectado. Usando primeiro canal.")
        channel_id = channel_ids[0]
    else:
        # Modo interativo
        try:
            choice = int(input(f"Escolha o canal (1-{len(channel_ids)}): ")) - 1
            channel_id = channel_ids[choice]
        except (ValueError, IndexError):
            print("Escolha invalida!")
            return

    print()
    print("Obtendo token... (verifique .env ou access.json)")

    # O token pode estar em varios lugares
    token = None

    # Tentar do access.json (se existir campo customizado)
    if hasattr(access, 'token') and access.token:
        token = access.token
    else:
        # Tentar do environment (suporta DISCORD_TOKEN ou DISCORD_BOT_TOKEN)
        import os
        token = os.environ.get("DISCORD_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")

    if not token:
        print("ERRO: Token nao encontrado!")
        print("Configure em:")
        print("  1. access.json (campo 'token')")
        print("  2. Variavel de ambiente DISCORD_TOKEN")
        return

    print(f"Token: {token[:10]}...{token[-4:]}")
    print()
    print("Conectando ao Discord...")

    # Criar bot
    bot = DiscordBot()

    try:
        # Criar task para manter o bot rodando
        print("Iniciando bot...")

        async def run_bot():
            await bot.login(token)
            await bot.connect()

        # Start bot in background
        bot_task = asyncio.create_task(run_bot())

        # Esperar bot estar pronto
        print("Aguardando bot ficar pronto...")
        for _ in range(50):  # Esperar até 5 segundos
            if bot.is_ready:
                break
            await asyncio.sleep(0.1)

        if not bot.is_ready:
            print("WARNING: Bot não ficou pronto a tempo. Tentando mesmo assim...")

        print(f"Bot pronto! Enviando cards para o canal {channel_id}...")

        # Enviar demo
        await send_demo_embed(bot, channel_id)

        print()
        print("=" * 60)
        print("CARDS ENVIADOS PARA O DISCORD!")
        print(f"Verifique o canal {channel_id}")
        print("=" * 60)

    finally:
        # Cancelar bot task e fechar
        if 'bot_task' in locals():
            bot_task.cancel()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
