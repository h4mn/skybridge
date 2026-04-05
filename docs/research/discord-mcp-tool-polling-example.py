#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Discord MCP Server com Tool Polling - ALTERNATIVA VIÁVEL a SSE.

Esta implementação usa MCP Tools (suportado nativamente) para permitir
que Claude Code Desktop "pulle" notificações do Discord, contornando
a limitação de notificações push não funcionarem via MCP.

Por que isso funciona quando SSE não?
- stdio é suportado por Claude Code
- Tools são parte oficial do protocolo MCP
- Cliente controla quando chamar tool (polling sob demanda)
- Sem infraestrutura HTTP adicional
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Força UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from dotenv import dotenv_values

# Discord imports
try:
    from discord import Client, Intents, InteractionType
    from discord.ui import View, button, Button
    from discord import ButtonStyle
    _discord_available = True
except ImportError as e:
    logging.warning(f"discord.py não disponível: {e}")
    _discord_available = False

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('discord_polling_mcp.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Configurações
STATE_DIR = Path.home() / ".claude/channels/discord"
CHANNEL_ID = 1487929503073173727

# Fila de notificações (em memória, pode ser persistida em arquivo)
_notifications = []  # List[dict]


# ============================================================================
# Discord Bot
# ============================================================================

class DiscordPollingBot(Client):
    """Bot Discord que captura interações para polling via MCP tool."""

    def __init__(self, mcp_server: Server):
        if not _discord_available:
            raise RuntimeError("discord.py não está instalado")
        super().__init__(intents=Intents.default())
        self.mcp_server = mcp_server
        self.channel_id = CHANNEL_ID
        self._ready = asyncio.Event()

    async def on_ready(self):
        """Bot conectado."""
        logger.info(f"[OK] Bot conectado: {self.user} (ID: {self.user.id})")

        channel = self.get_channel(self.channel_id)
        if not channel:
            logger.error(f"[ERRO] Canal {self.channel_id} não encontrado")
            return

        await channel.send(
            "**Claude Code Channel - MCP Polling Server Ativo**\n"
            "Notificações são capturadas e podem ser consultadas via tool "
            "`get_discord_notifications` no Claude Code.",
            view=ChannelView(self)
        )
        logger.info(f"[OK] Botões enviados para {channel.name}")
        self._ready.set()

    async def on_interaction(self, interaction):
        """Captura interações Discord e armazena para polling."""
        if interaction.type != InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "unknown")
        user = interaction.user

        logger.info(f"[BUTTON] {custom_id} por {user.name}")

        # Armazena notificação
        notification = {
            "id": f"{datetime.now().timestamp()}",
            "type": "button_click",
            "content": f"[button] {custom_id} clicado por {user.name}",
            "meta": {
                "channel_id": str(interaction.channel.id),
                "channel_name": interaction.channel.name,
                "user_id": str(user.id),
                "user_name": user.name,
                "custom_id": custom_id,
                "message_id": str(interaction.message.id),
                "guild_id": str(interaction.guild.id) if interaction.guild else None,
                "timestamp": datetime.now().isoformat(),
            }
        }
        _notifications.append(notification)

        # Responde ao usuário Discord
        await interaction.response.send_message(
            f"[OK] {custom_id} capturado! Use `get_discord_notifications` no Claude Code.",
            ephemeral=True
        )

        logger.info(f"[CAPTURED] Notificação armazenada: {custom_id}")


class ChannelView(View):
    """View com botões que geram notificações."""

    def __init__(self, bot: DiscordPollingBot):
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
# MCP Server
# ============================================================================

app = Server("discord-polling")
_discord_bot_instance = None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista ferramentas MCP disponíveis."""
    return [
        Tool(
            name="get_discord_notifications",
            description="""
Retorna notificações pendentes do Discord capturadas pelo bot.

Esta ferramenta implementa POLLING de notificações como alternativa
a notificações push (que não funcionam em MCP).

Uso recomendado em Claude Code:
- Chame periodicamente para verificar novas notificações
- Notificações são retornadas e removidas da fila (consume-once)

Exemplo de prompt para Claude Code:
"Verifica se há novas notificações Discord e me resume o que precisa ser feito."
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Número máximo de notificações a retornar (default: todas)",
                        "default": 0
                    },
                    "clear": {
                        "type": "boolean",
                        "description": "Se True, limpa notificações após retornar (default: True)",
                        "default": True
                    }
                }
            }
        ),
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
        ),
        Tool(
            name="discord_notification_stats",
            description="Retorna estatísticas sobre notificações capturadas",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Executa ferramenta MCP chamada por Claude Code."""
    global _notifications, _discord_bot_instance

    try:
        if name == "get_discord_notifications":
            # Retorna notificações pendentes
            limit = arguments.get("limit", 0)
            clear = arguments.get("clear", True)

            if not _notifications:
                return [TextContent(
                    type="text",
                    text="Nenhuma notificação pendente no Discord."
                )]

            # Filtra por limit se especificado
            to_return = _notifications[:limit] if limit > 0 else _notifications.copy()

            # Formata output
            result = {
                "count": len(to_return),
                "notifications": to_return,
                "summary": summarize_notifications(to_return)
            }

            # Limpa se solicitado
            if clear:
                _notifications.clear()

            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]

        elif name == "send_discord_message":
            # Envia mensagem para Discord
            if _discord_bot_instance:
                await _discord_bot_instance.send_message_to_discord(arguments["content"])
                return [TextContent(
                    type="text",
                    text=f"[OK] Mensagem enviada: {arguments['content'][:50]}..."
                )]
            else:
                return [TextContent(type="text", text="[ERRO] Bot Discord não disponível")]

        elif name == "get_discord_info":
            # Info sobre conexão Discord
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

        elif name == "discord_notification_stats":
            # Estatísticas
            return [TextContent(
                type="text",
                text=json.dumps({
                    "pending_count": len(_notifications),
                    "bot_connected": _discord_bot_instance.is_ready() if _discord_bot_instance else False,
                    "polling_mode": "active",
                    "last_notification": _notifications[-1]["timestamp"] if _notifications else None
                }, ensure_ascii=False, indent=2)
            )]

        return [TextContent(type="text", text=f"Ferramenta desconhecida: {name}")]

    except Exception as e:
        logger.error(f"[ERRO] Tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Erro: {str(e)}")]


# ============================================================================
# Utilitários
# ============================================================================

def summarize_notifications(notifications: list[dict]) -> str:
    """Cria resumo legível das notificações."""
    if not notifications:
        return "Nenhuma notificação."

    by_type = {}
    for n in notifications:
        t = n.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    parts = [f"{count} {t}(s)" for t, count in by_type.items()]
    return f"📊 {len(notifications)} notificações: {', '.join(parts)}"


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
    bot = DiscordPollingBot(app)
    _discord_bot_instance = bot

    logger.info("[INIT] Iniciando Discord Polling MCP Server...")
    logger.info(f"[INIT] Estado: {STATE_DIR}")
    logger.info(f"[INIT] Canal alvo: {CHANNEL_ID}")
    logger.info("[INFO] Modo: POLLING (use get_discord_notifications tool)")

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
