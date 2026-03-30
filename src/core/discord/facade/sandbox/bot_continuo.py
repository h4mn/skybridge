# -*- coding: utf-8 -*-
"""
Bot Contínuo - Mantém o bot Discord ativo para testar interações.

Este script conecta o bot e mantém ele rodando para responder cliques de botão.
"""

import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import sys

import discord
from discord import Embed, InteractionType

# Adicionar caminho do projeto ao sys.path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.discord.access import load_access

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfirmationView(discord.ui.View):
    """View customizada para confirmacao de ordem."""

    def __init__(self):
        super().__init__(timeout=None)  # Nunca expira

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.success, custom_id="ordem_confirm")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handler do botao Confirmar."""
        await interaction.response.send_message(
            f"[OK] **{interaction.user.name}** confirmou a ordem!"
        )
        logger.info(f"Botao Confirmar clicado por {interaction.user.name}")

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, custom_id="ordem_cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handler do botao Cancelar."""
        await interaction.response.send_message(
            f"[X] **{interaction.user.name}** cancelou a ordem!"
        )
        logger.info(f"Botao Cancelar clicado por {interaction.user.name}")


class ContinuousBot(discord.Client):
    """Bot Discord que roda continuamente."""

    def __init__(self, channel_id: str):
        intents = discord.Intents.default()
        intents.message_content = True
        # IMPORTANTE: Habilitar intents para interações
        intents.integrations = True  # Necessário para interações de botão
        super().__init__(intents=intents)
        self.channel_id = channel_id
        self.sent_message_ids = []

    async def setup_hook(self):
        """Quando o bot esta pronto."""
        logger.info(f"Bot conectado como {self.user}")

    async def on_ready(self):
        """Quando o bot está pronto para uso - envia os cards."""
        logger.info(f"Bot pronto! Conectado como {self.user}")

        # Aguardar um momento para estabilizar
        await asyncio.sleep(2)

        # Enviar os cards de teste
        await self.send_test_cards()

        logger.info("=" * 60)
        logger.info("BOT RODANDO CONTINUAMENTE!")
        logger.info(f"Canal: {self.channel_id}")
        logger.info("Clique nos botões para testar - não deve dar erro!")
        logger.info("Ctrl+C para parar")
        logger.info("=" * 60)

    async def on_interaction_create(self, interaction):
        """
        Handler para interacoes (botoes).

        Processa cliques de botao e faz acknowledge para evitar timeout.
        """
        try:
            logger.info(f"Interação recebida! Tipo: {interaction.type}, Canal: {interaction.channel_id}")

            # Apenas interacoes de componente (botoes)
            if interaction.type != InteractionType.component:
                logger.info(f"Ignorando interação do tipo: {interaction.type}")
                return

            # Extrair custom_id do botao
            custom_id = getattr(interaction.data, 'custom_id', None)
            logger.info(f"Custom ID: {custom_id}")

            if not custom_id:
                return

            # Responder a interacao imediatamente
            try:
                logger.info(f"Respondendo interacao para: {custom_id}")
                emoji = "[OK]" if "confirm" in custom_id else "[X]"
                await interaction.response.send_message(
                    f"{emoji} **{interaction.user.name}** clicou no botao: `{custom_id}`"
                )
                logger.info(
                    f"✓ Botao clicado: {custom_id} "
                    f"por {interaction.user.name} ({interaction.user.id}) "
                    f"no canal {interaction.channel_id}"
                )

            except Exception as e:
                logger.error(f"Erro ao responder interacao: {e}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            logger.error(f"Erro no handler de interacao: {e}")
            import traceback
            traceback.print_exc()

    async def send_test_cards(self):
        """Envia os cards de teste para o canal."""
        try:
            channel = await self.fetch_channel(self.channel_id)
            logger.info(f"Enviando cards para o canal: {channel.name}")

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

            msg1 = await channel.send(embed=embed1)
            self.sent_message_ids.append(msg1.id)
            logger.info("✓ Embed de portfolio enviado!")

            # EMBED DE CONFIRMACAO DE ORDEM com botões (View SEM timeout)
            embed2 = Embed(
                title="Confirmar Ordem",
                description="Deseja confirmar esta operacao?",
                color=3447003,  # Azul
            )
            embed2.add_field(name="Ativo", value="PETR4", inline=True)
            embed2.add_field(name="Quantidade", value="100", inline=True)
            embed2.add_field(name="Preco", value="R$ 38,50", inline=True)
            embed2.add_field(name="Total", value="R$ 3.850,00", inline=False)

            # View customizada com handlers
            view = ConfirmationView()

            msg2 = await channel.send(embed=embed2, view=view)
            self.sent_message_ids.append(msg2.id)
            logger.info("✓ Botoes de confirmacao enviados (COM VIEW CUSTOMIZADA)!")

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

            msg3 = await channel.send(embed=embed3)
            self.sent_message_ids.append(msg3.id)
            logger.info("✓ Alerta de risco enviado!")

        except Exception as e:
            logger.error(f"Erro ao enviar cards: {e}")


async def main():
    """Executa o bot continuo."""
    load_dotenv()

    # Carregar configuracoes
    access = load_access()

    # Adicionar canal Discord Redesign se não existir
    from src.core.discord.presentation.dto.legacy_dto import GroupPolicy

    target_channel = "1487929503073173727"  # Discord Redesign
    if target_channel not in access.groups:
        access.groups[target_channel] = GroupPolicy(
            require_mention=False,
            allow_from=[]
        )
        from src.core.discord.access import save_access
        save_access(access)
        print(f"Canal {target_channel} adicionado ao access.json")

    channel_id = target_channel

    # Obter token
    import os
    token = os.environ.get("DISCORD_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")

    if not token:
        print("ERRO: Token nao encontrado!")
        return

    print("=" * 60)
    print("BOT CONTÍNUO - INTERAÇÕES ATIVAS")
    print("=" * 60)
    print(f"Canal: {channel_id} (Discord Redesign)")
    print(f"Token: {token[:10]}...{token[-4:]}")
    print()
    print("Iniciando bot...")
    print()

    # Criar bot
    bot = ContinuousBot(channel_id)

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("\n\nBot encerrado pelo usuário.")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
