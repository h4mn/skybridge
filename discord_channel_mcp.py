#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Claude Code Channel - Discord MCP Server (Standalone).

Este servidor MCP atua como um canal Claude Code, capturando interações
do Discord e enviando notificações em tempo real via stdio.

Versão standalone para evitar conflitos de importação do projeto.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Força UTF-8 em stdout/stderr
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from dotenv import dotenv_values

# Discord imports - lazy loading para evitar conflitos
_discord_available = False
try:
    from discord import Client, Intents, InteractionType
    from discord.ui import View, button, Button
    from discord import ButtonStyle
    _discord_available = True
except ImportError as e:
    logging.warning(f"Discord.py não disponível: {e}")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('discord_channel_mcp.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Configurações
STATE_DIR = Path.home() / ".claude/channels/discord"
CHANNEL_ID = 1487929503073173727

# MCP Server
app = Server("discord-channel")


class DiscordChannelBot(Client):
    """Bot Discord que publica eventos no MCP channel."""

    def __init__(self, mcp_server: Server):
        if not _discord_available:
            raise RuntimeError("discord.py não está instalado")
        super().__init__(intents=Intents.default())
        self.mcp_server = mcp_server
        self.channel_id = CHANNEL_ID
        self._ready = asyncio.Event()
        self._notification_handler = None

    def set_notification_handler(self, handler):
        """Define callback para enviar notificações ao cliente MCP."""
        self._notification_handler = handler

    async def on_ready(self):
        """Bot conectado - envia botões para o canal."""
        logger.info(f"[OK] Bot conectado: {self.user} (ID: {self.user.id})")

        channel = self.get_channel(self.channel_id)
        if not channel:
            logger.error(f"[ERRO] Canal {self.channel_id} não encontrado")
            return

        await channel.send(
            "**Claude Code Channel - MCP Server Ativo**\n"
            "Clique nos botões para enviar interações ao Claude Code",
            view=ChannelView(self)
        )
        logger.info(f"[OK] Botoes enviados para o canal {channel.name}")
        self._ready.set()

    async def on_interaction(self, interaction):
        """Captura interações Discord e envia para Claude Code via MCP."""
        if interaction.type != InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "unknown")
        user = interaction.user

        logger.info(f"[BUTTON] {custom_id} por {user.name}")

        # Responde ao usuário Discord
        await interaction.response.send_message(
            f"[OK] {custom_id} enviado ao Claude Code!",
            ephemeral=True
        )

        # Emite notificação MCP
        notification = {
            "method": "notifications/discord/button",
            "params": {
                "content": f"[button] {custom_id} clicado por {user.name}",
                "meta": {
                    "channel_id": str(interaction.channel.id),
                    "channel_name": interaction.channel.name,
                    "user_id": str(user.id),
                    "user_name": user.name,
                    "custom_id": custom_id,
                    "message_id": str(interaction.message.id),
                    "guild_id": str(interaction.guild.id) if interaction.guild else None,
                }
            }
        }

        if self._notification_handler:
            await self._notification_handler(notification)
        else:
            logger.warning("[WARN] Nenhum notification handler configurado")

    async def send_message_to_discord(self, content: str):
        """Envia mensagem do Claude Code para o canal Discord."""
        await self._ready.wait()

        channel = self.get_channel(self.channel_id)
        if not channel:
            logger.error(f"[ERRO] Canal {self.channel_id} não encontrado")
            return

        await channel.send(content)
        logger.info(f"[DISCORD] Mensagem enviada: {content[:50]}...")


class ChannelView(View):
    """View com botões que enviam notificações ao Claude Code."""

    def __init__(self, bot: DiscordChannelBot):
        super().__init__(timeout=None)
        self.bot = bot

    @button(label="Enviar para Claude", style=ButtonStyle.primary, custom_id="send_to_claude")
    async def send_to_claude(self, interaction, button):
        pass

    @button(label="Portfolio", style=ButtonStyle.success, custom_id="portfolio")
    async def portfolio(self, interaction, button):
        pass

    @button(label="Alerta", style=ButtonStyle.danger, custom_id="alert")
    async def alert(self, interaction, button):
        pass


# ============================================================================
# MCP Tools
# ============================================================================

_discord_bot_instance = None

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista ferramentas MCP disponíveis."""
    return [
        Tool(
            name="send_discord_message",
            description="Envia mensagem para o canal Discord conectado",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Conteúdo da mensagem a enviar"
                    }
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="get_discord_info",
            description="Retorna informações sobre a conexão Discord",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Executa ferramenta MCP chamada por Claude Code."""
    global _discord_bot_instance

    try:
        if name == "send_discord_message":
            if _discord_bot_instance:
                await _discord_bot_instance.send_message_to_discord(arguments["content"])
                return [TextContent(
                    type="text",
                    text=f"[OK] Mensagem enviada: {arguments['content'][:50]}..."
                )]
            else:
                return [TextContent(type="text", text="[ERRO] Bot Discord não disponível")]

        elif name == "get_discord_info":
            if _discord_bot_instance and _discord_bot_instance.is_ready():
                channel = _discord_bot_instance.get_channel(_discord_bot_instance.channel_id)
                info = {
                    "status": "connected",
                    "bot_name": str(_discord_bot_instance.user),
                    "bot_id": str(_discord_bot_instance.user.id) if _discord_bot_instance.user else None,
                    "channel_id": str(_discord_bot_instance.channel_id),
                    "channel_name": channel.name if channel else None,
                    "guild_id": str(channel.guild.id) if channel and channel.guild else None,
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(info, ensure_ascii=False, indent=2)
                )]
            else:
                return [TextContent(type="text", text="Bot não está pronto")]

        return [TextContent(type="text", text=f"Ferramenta desconhecida: {name}")]

    except Exception as e:
        logger.error(f"[ERRO] Tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Erro: {str(e)}")]


# ============================================================================
# Main
# ============================================================================

async def main():
    """Inicia o servidor MCP e o bot Discord."""
    global _discord_bot_instance

    # Carrega token
    config = dotenv_values(STATE_DIR / ".env")
    token = config.get("DISCORD_BOT_TOKEN")

    if not token:
        logger.error(f"[ERRO] DISCORD_BOT_TOKEN não encontrado em {STATE_DIR}/.env")
        logger.error("[DICA] Crie o arquivo com: DISCORD_BOT_TOKEN=seu_token_aqui")
        return

    if not _discord_available:
        logger.error("[ERRO] discord.py não disponível - instale com: pip install discord.py")
        return

    # Cria bot Discord
    bot = DiscordChannelBot(app)
    _discord_bot_instance = bot

    logger.info("[INIT] Iniciando Discord Channel MCP Server...")
    logger.info(f"[INIT] Estado: {STATE_DIR}")
    logger.info(f"[INIT] Canal alvo: {CHANNEL_ID}")

    # Task paralela: Discord bot
    discord_task = asyncio.create_task(bot.start(token))

    try:
        # MCP server via stdio
        async with stdio_server() as (read_stream, write_stream):
            logger.info("[OK] MCP stdio server ativo - aguardando Claude Code")

            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    except KeyboardInterrupt:
        logger.info("[STOP] Interrupção solicitada")
    except Exception as e:
        logger.error(f"[ERRO] Servidor MCP: {e}", exc_info=True)
    finally:
        logger.info("[STOP] Encerrando bot Discord...")
        discord_task.cancel()
        try:
            await discord_task
        except asyncio.CancelledError:
            pass
        logger.info("[OK] Encerrado")


if __name__ == "__main__":
    asyncio.run(main())
