# -*- coding: utf-8 -*-
"""
Demo Completo DDD - Demonstração completa da migração Discord DDD.

Mostra todas as camadas da arquitetura DDD implementadas:
- Domain: Entities, Value Objects, Services
- Application: Commands, Queries, Handlers, Services
- Infrastructure: Adapters, Repositories
- Presentation: Tools MCP, DTOs, Prompts
- Integration: Projections, Handlers

DOC: DDD Migration - Complete Demo
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

from src.core.discord.access import load_access, save_access
from src.core.discord.application.services.discord_service import DiscordService
from src.core.discord.presentation.dto.tool_schemas import (
    SendEmbedInput,
    CreateThreadInput,
)
from src.core.integrations.discord_paper.projections.portfolio_projection import (
    PortfolioProjection,
)
from src.core.integrations.discord_paper.projections.ordem_projection import (
    OrdemProjection,
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemoCompletoDDD(discord.Client):
    """Demo completa de todos os componentes DDD."""

    def __init__(self, channel_id: str):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.channel_id = channel_id
        self.discord_service = None

    async def setup_hook(self):
        """Configura serviço Discord."""
        self.discord_service = DiscordService(client=self)

    async def on_ready(self):
        """Quando bot está pronto - executa demos completas."""
        logger.info(f"Bot conectado como {self.user}")
        logger.info(f"Canal alvo: {self.channel_id}")

        # === 1. DOMAIN LAYER ===
        await self.demo_domain_layer()

        await asyncio.sleep(2)

        # === 2. APPLICATION LAYER ===
        await self.demo_application_layer()

        await asyncio.sleep(2)

        # === 3. PRESENTATION LAYER ===
        await self.demo_presentation_layer()

        await asyncio.sleep(2)

        # === 4. INTEGRATION LAYER ===
        await self.demo_integration_layer()

        logger.info("=" * 60)
        logger.info("DEMO COMPLETA DDD FINALIZADA!")
        logger.info("Todas as 4 camadas testadas com sucesso!")
        logger.info("=" * 60)

    async def demo_domain_layer(self):
        """Demo: Domain Layer - Entities e Value Objects."""
        logger.info("📦 DOMAIN LAYER")

        from src.core.discord.domain.value_objects import ChannelId, MessageId, MessageContent

        # Value Objects
        channel_id = ChannelId("123456")
        message_id = MessageId("789012")
        content = MessageContent("Teste de conteúdo")

        await self.discord_service.send_message(
            channel_id=self.channel_id,
            content=f"**Domain Layer** ✅\n"
                    f"ChannelId: {channel_id}\n"
                    f"MessageId: {message_id}\n"
                    f"Content length: {len(content.text)}"
        )
        logger.info("✓ Value Objects validados")

    async def demo_application_layer(self):
        """Demo: Application Layer - Commands e Services."""
        logger.info("🔧 APPLICATION LAYER")

        # DiscordService (Fachada)
        await self.discord_service.send_embed(
            channel_id=self.channel_id,
            title="Application Layer",
            description="DiscordService é a fachada da Application Layer",
            color=3447003,
            fields=[
                {"name": "Commands", "value": "CQRS", "inline": True},
                {"name": "Handlers", "value": "Validação", "inline": True},
                {"name": "Services", "value": "Orquestração", "inline": True}
            ]
        )
        logger.info("✓ DiscordService executado")

    async def demo_presentation_layer(self):
        """Demo: Presentation Layer - Tools MCP e DTOs."""
        logger.info("🎨 PRESENTATION LAYER")

        # Pydantic DTOs
        dto = SendEmbedInput(
            chat_id=self.channel_id,
            title="Presentation Layer",
            description="Validação via Pydantic DTOs",
            fields=[
                {"name": "14 Tools MCP", "value": "Registradas", "inline": True},
                {"name": "Pydantic Schemas", "value": "Validação", "inline": True},
                {"name": "Prompts", "value": "Sistema completo", "inline": True}
            ]
        )

        await self.discord_service.send_embed(
            channel_id=self.channel_id,
            title=dto.title,
            description=dto.description,
            fields=[
                {"name": f.name, "value": f.value, "inline": f.inline}
                for f in dto.fields
            ]
        )
        logger.info("✓ DTOs validados")

        # Demo send_progress com tracking_id
        tracking_id = "demo_tracking_complete"
        for i in range(0, 101, 25):
            await self.discord_service.send_progress(
                channel_id=self.channel_id,
                title="Presentation Layer Progress",
                current=i,
                total=100,
                status=f"Processando... {i}%",
                tracking_id=tracking_id
            )
            await asyncio.sleep(0.5)
        logger.info("✓ Progress tracking funcionando")

    async def demo_integration_layer(self):
        """Demo: Integration Layer - Projections."""
        logger.info("🔗 INTEGRATION LAYER")

        # Portfolio Projection
        portfolio_proj = PortfolioProjection()
        portfolio_embed = portfolio_proj.project_embed(
            balance_btc=2.5,
            balance_usd=125000,
            positions=[
                {"symbol": "BTC", "side": "long", "pnl_percent": 15.5},
                {"symbol": "ETH", "side": "long", "pnl_percent": 8.3}
            ],
            pnl_percent=12.5
        )

        embed_dict = portfolio_embed.to_embed_dict()

        await self.discord_service.send_embed(
            channel_id=self.channel_id,
            title=embed_dict["title"],
            description=embed_dict["description"],
            color=embed_dict["color"],
            fields=embed_dict["fields"]
        )
        logger.info("✓ Portfolio Projection executada")

        # Ordem Projection
        ordem_proj = OrdemProjection()
        ordem_embed, buttons = ordem_proj.project_ordem_confirmacao(
            symbol="BTCUSD",
            side="buy",
            quantity=1.0,
            price=50000,
            order_id="demo_ordem_123"
        )

        # Converte para DiscordService format
        from src.core.discord.application.services.discord_service import ButtonConfig
        button_configs = [
            ButtonConfig(label=btn["label"], style=btn["style"], custom_id=btn["custom_id"])
            for btn in buttons.buttons
        ]

        await self.discord_service.send_buttons(
            channel_id=self.channel_id,
            title=ordem_embed.title,
            buttons=button_configs,
            embed_data={"color": ordem_embed.color, "fields": ordem_embed.to_embed_dict()["fields"]}
        )
        logger.info("✓ Ordem Projection executada")

        # Menu com Prompts
        await self.discord_service.send_message(
            channel_id=self.channel_id,
            content="**Sistema de Prompts** 📝\n"
                    "Identidade, Contexto, Tools Guide e Segurança implementados!"
        )
        logger.info("✓ Prompts integrados")


async def main():
    """Executa a demo completa."""
    load_dotenv()

    # Carrega token
    import os
    token = os.environ.get("DISCORD_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")

    if not token:
        print("ERRO: Token não encontrado!")
        print("Configure DISCORD_TOKEN no .env")
        return

    # Canal alvo
    target_channel = "1487929503073173727"

    # Adiciona canal ao access.json se necessário
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
    bot = DemoCompletoDDD(channel_id=target_channel)

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("\nBot encerrado.")


if __name__ == "__main__":
    asyncio.run(main())
