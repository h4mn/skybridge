#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Channel Bot MCP - Standalone."""
import os, sys, io, asyncio
from pathlib import Path

# UTF-8
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# .env
state_dir = Path(os.environ.get("DISCORD_STATE_DIR", Path.home() / ".claude" / "channels" / "discord"))
env_file = state_dir / ".env"

if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            if key.strip() and key.strip() not in os.environ:
                os.environ[key.strip()] = value.strip()

token = os.environ.get("DISCORD_BOT_TOKEN")
if not token:
    print(f"[ERRO] DISCORD_BOT_TOKEN não encontrado em {env_file}")
    sys.exit(1)

print(f"[INFO] Iniciando Channel Bot MCP...")

from discord import Client, Intents, InteractionType, ButtonStyle
from discord.ui import View, button
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, JSONRPCNotification, JSONRPCMessage

CHANNEL_ID = 1487929503073173727
app = Server("channel-bot")
_write_stream = None


class Bot(Client):
    def __init__(self):
        super().__init__(intents=Intents.default())

    async def on_ready(self):
        print(f"[OK] {self.user}", file=sys.stderr, flush=True)
        ch = self.get_channel(CHANNEL_ID)
        await ch.send("Claude Code MCP", view=ChannelView())

    async def on_interaction_create(self, i):
        if i.type != InteractionType.component:
            return
        await i.response.defer()
        if _write_stream:
            notif = JSONRPCNotification(jsonrpc="2.0", method="notifications/claude/channel", params={
                "content": f"[{i.data.get('custom_id')}] por {i.user.name}",
                "meta": {"user": i.user.name, "chat_id": str(i.channel_id)}
            })
            await _write_stream.send(JSONRPCMessage(notif))


class ChannelView(View):
    @button(label="Enviar Claude", style=ButtonStyle.primary, custom_id="send")
    async def btn(self, i, b): pass


@app.call_tool()
async def call_tool(name, args):
    return [TextContent(type="text", text="OK")]


@app.list_tools()
async def list_tools():
    return [Tool(name="ping", inputSchema={"type": "object"})]


async def main():
    global _write_stream
    bot = Bot()

    async with stdio_server() as (r, w):
        _write_stream = w
        discord_task = asyncio.create_task(bot.start(token))

        try:
            await asyncio.wait_for(bot.wait_until_ready(), timeout=30.0)
        except asyncio.TimeoutError:
            print("[WARN] Discord timeout", file=sys.stderr, flush=True)

        await app.run(r, w, app.create_initialization_options(experimental_capabilities={"claude/channel": {}}))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Interrompido")
