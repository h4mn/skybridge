# -*- coding: utf-8 -*-
"""
Demo UI Components - Demonstração das novas Tools MCP.

Mostra as funcionalidades de send_progress e send_menu.

DOC: DDD Migration - Sandbox Demo
"""

import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import sys

import discord
from discord import Embed

# Adicionar caminho do projeto ao sys.path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.discord.access import load_access
from src.core.discord.application.services.discord_service import DiscordService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemoUIComponentsBot(discord.Client):
    """Bot demonstração de UI Components."""

    def __init__(self, channel_id: str):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.integrations = True
        super().__init__(intents=intents)
        self.channel_id = channel_id
        self.discord_service = None

    async def setup_hook(self):
        """Configura serviço Discord."""
        self.discord_service = DiscordService(client=self)

    async def on_ready(self):
        """Quando bot está pronto - envia demos."""
        logger.info(f"Bot conectado como {self.user}")
        logger.info(f"Enviando demos para o canal: {self.channel_id}")

        await self.send_progress_demo()
        await asyncio.sleep(2)
        await self.send_menu_demo()

        logger.info("=" * 60)
        logger.info("DEMO ENVIADA!")
        logger.info("Canal: %s", self.channel_id)
        logger.info("=" * 60)

    async def send_progress_demo(self):
        """Envia demonstração de progresso - mesma mensagem sendo atualizada."""
        tracking_id = "demo_progress_sandbox"  # ID único para esta sequência

        # Demo 1: Progresso 0% - cria mensagem
        await self.discord_service.send_progress(
            channel_id=self.channel_id,
            title="⏳ Processando Arquivos",
            current=0,
            total=10,
            status="Iniciando...",
            tracking_id=tracking_id
        )
        logger.info("✓ Progresso 0% - mensagem criada")

        await asyncio.sleep(2)

        # Demo 2: Progresso 30% - atualiza mesma mensagem
        await self.discord_service.send_progress(
            channel_id=self.channel_id,
            title="⏳ Processando Arquivos",
            current=3,
            total=10,
            status="Analisando...",
            tracking_id=tracking_id
        )
        logger.info("✓ Progresso 30% - mensagem atualizada")

        await asyncio.sleep(2)

        # Demo 3: Progresso 70% - atualiza mesma mensagem
        await self.discord_service.send_progress(
            channel_id=self.channel_id,
            title="⏳ Processando Arquivos",
            current=7,
            total=10,
            status="Quase terminado...",
            tracking_id=tracking_id
        )
        logger.info("✓ Progresso 70% - mensagem atualizada")

        await asyncio.sleep(2)

        # Demo 4: Progresso 100% - atualiza mesma mensagem
        await self.discord_service.send_progress(
            channel_id=self.channel_id,
            title="⏳ Processamento Concluído",
            current=10,
            total=10,
            status="Finalizado!",
            tracking_id=tracking_id
        )
        logger.info("✓ Progresso 100% - mensagem atualizada")

    async def send_menu_demo(self):
        """Envia demonstração de menu com opção de recarregar progresso."""
        channel = await self.fetch_channel(self.channel_id)

        # Cria menu
        from discord.ui import Select, View

        class DemoMenuView(View):
            def __init__(self, bot_instance):
                super().__init__(timeout=None)
                self.bot = bot_instance

            @discord.ui.select(
                placeholder="Escolha uma ação...",
                min_values=1,
                max_values=1,
                options=[
                    discord.SelectOption(
                        label="🔄 Recarregar Progresso",
                        value="reload_progress",
                        description="Executar novamente a demo de progresso",
                        emoji="🔄"
                    ),
                    discord.SelectOption(
                        label="📊 Ver Portfolio",
                        value="portfolio",
                        description="Mostrar portfólio atual",
                    ),
                    discord.SelectOption(
                        label="📈 Ver Gráficos",
                        value="graficos",
                        description="Mostrar gráficos de desempenho",
                    ),
                    discord.SelectOption(
                        label="⚙️ Configurações",
                        value="config",
                        description="Abrir configurações",
                    ),
                ],
            )
            async def select_callback(self, interaction: discord.Interaction, select: Select):
                selected = select.values[0]

                if selected == "reload_progress":
                    await interaction.response.send_message("🔄 **Recarregando demo de progresso...**")
                    await self.bot.send_progress_demo()
                else:
                    await interaction.response.send_message(f"✅ Você selecionou: **{selected}**")

        view = DemoMenuView(bot_instance=self)
        await channel.send("📋 **Menu Principal** - Escolha uma opção:", view=view)
        logger.info("✓ Menu enviado com opção de recarregar progresso")


async def main():
    """Executa a demo."""
    load_dotenv()

    # Carrega token
    import os
    token = os.environ.get("DISCORD_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")

    if not token:
        print("ERRO: Token não encontrado!")
        print("Configure DISCORD_TOKEN no .env")
        return

    # Canal alvo (Discord Redesign)
    target_channel = "1487929503073173727"

    # Adiciona canal ao access.json se necessário
    from src.core.discord.access import save_access
    from src.core.discord.presentation.dto.legacy_dto import GroupPolicy

    access = load_access()
    if target_channel not in access.groups:
        access.groups[target_channel] = GroupPolicy(
            require_mention=False,
            allow_from=[]
        )
        save_access(access)
        print(f"Canal {target_channel} adicionado ao access.json")

    # Cria e roda bot
    bot = DemoUIComponentsBot(channel_id=target_channel)

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("\nBot encerrado.")


if __name__ == "__main__":
    asyncio.run(main())
