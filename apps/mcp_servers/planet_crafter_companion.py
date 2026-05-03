#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Planet Crafter Companion — MCP Server.

Fluxo direto: mod POSTa eventos → MCP server notifica Claude Code imediatamente.
Sem polling. Sem throttle. Sem cursor.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx
from aiohttp import web
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import JSONRPCMessage, JSONRPCNotification, TextContent, Tool

logger = logging.getLogger(__name__)

VALID_ANIMATIONS = ("idle", "thinking", "speaking")
DEFAULT_MOD_URL = "http://localhost:17234"
MCP_LISTEN_PORT = 17235


# ============================================================================
# Session Management
# ============================================================================

@dataclass
class Session:
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str | None = None
    active: bool = True
    events: list[dict] = field(default_factory=list)


class CompanionSessionManager:
    """Gerencia o ciclo de vida da sessão de jogatina."""

    def __init__(self):
        self.session: Session | None = None

    @property
    def is_active(self) -> bool:
        return self.session is not None and self.session.active

    def start_if_needed(self) -> None:
        if self.session is None:
            self.session = Session()

    def log_event(self, event_type: str, description: str) -> None:
        self.start_if_needed()
        self.session.events.append({
            "type": event_type,
            "description": description,
            "timestamp": datetime.now().isoformat(),
        })

    def add_note(self, text: str) -> None:
        self.log_event("note", text)

    def get_summary(self) -> dict:
        if not self.session:
            return {"active": False, "message": "Nenhuma sessão ativa"}

        now = datetime.now()
        start = datetime.fromisoformat(self.session.start_time)
        duration = (now - start).total_seconds()

        counts: dict[str, int] = {}
        for e in self.session.events:
            counts[e["type"]] = counts.get(e["type"], 0) + 1

        return {
            "active": self.session.active,
            "duration_seconds": duration,
            "events": self.session.events,
            "event_counts": counts,
            "total_events": len(self.session.events),
            "milestones": [e for e in self.session.events if e["type"] == "milestone"],
            "notes": [e for e in self.session.events if e["type"] == "note"],
        }


# ============================================================================
# Direct Push: mod POSTa evento → MCP notifica Claude Code imediatamente
# ============================================================================

async def send_channel_notification(write_stream: Any, content: str, source: str = "planet-crafter") -> None:
    """Envia JSONRPCNotification diretamente via write_stream."""
    notif = JSONRPCNotification(
        jsonrpc="2.0",
        method="notifications/claude/channel",
        params={"content": content, "meta": {"source": source}},
    )
    try:
        await write_stream.send(JSONRPCMessage(notif))
        logger.info(f"[CHANNEL] Notificação enviada: {content[:80]}")
    except Exception as e:
        logger.error(f"[CHANNEL] Erro: {type(e).__name__}: {e}")


def create_push_handler(write_stream: Any, session_manager: CompanionSessionManager):
    """Cria handler HTTP que recebe POST direto do mod."""
    async def handle_incoming(request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"status": "error", "message": "JSON inválido"}, status=400)

        event_type = data.get("type", "unknown")
        description = data.get("description", "")
        text = data.get("text", "")

        # Compatibilidade: aceita {type: "skychat", description: "..."} e {type: "show_message", text: "..."}
        content = description or text or str(data)

        # Registra na sessão
        session_manager.log_event(event_type, content)

        # Envia notificação imediata ao Claude Code
        message = f"[{event_type}] {content}"
        await send_channel_notification(write_stream, message)

        return web.json_response({"status": "ok"})

    return handle_incoming


# ============================================================================
# MCP Server & Tools
# ============================================================================

def create_server() -> Server:
    return Server(
        "planet-crafter-channel",
        instructions=(
            "Eventos do Planet Crafter chegam como <channel source=\"planet-crafter\" ...>. "
            "Tipos: milestone (terraformação), skychat (mensagem do jogador), death, note. "
            "Para responder ao jogador, use send_companion_message(text). "
            "Para contexto do jogo, use get_game_state(). "
            "Responda sempre em português brasileiro."
        ),
    )


def create_initialization_options() -> Any:
    server = create_server()
    return server.create_initialization_options(
        experimental_capabilities={"claude/channel": {}}
    )


async def handle_tool_call(
    name: str,
    arguments: dict,
    http_client: httpx.AsyncClient | None = None,
    base_url: str = DEFAULT_MOD_URL,
    session_manager: CompanionSessionManager | None = None,
) -> str:
    client = http_client or httpx.AsyncClient()

    try:
        if name == "send_companion_message":
            try:
                await client.post(
                    f"{base_url}/action",
                    json={"type": "show_message", "text": arguments["text"]},
                )
                return f"Mensagem enviada: {arguments['text'][:50]}"
            except (httpx.ConnectError, ConnectionRefusedError, OSError):
                return "Companion não está disponível — verifique se o jogo está aberto com o mod carregado"

        elif name == "move_companion_to":
            strategy = arguments["strategy"]
            body: dict[str, Any] = {"type": "move", "strategy": strategy}
            if strategy == "goto_coords":
                for coord in ("x", "y", "z"):
                    if coord in arguments:
                        body[coord] = arguments[coord]
            elif strategy == "goto_named":
                if "name" in arguments:
                    body["name"] = arguments["name"]
            try:
                await client.post(f"{base_url}/action", json=body)
                return f"Movimento executado: {strategy}"
            except (httpx.ConnectError, ConnectionRefusedError, OSError):
                return "Companion não está disponível — verifique se o jogo está aberto com o mod carregado"

        elif name == "set_companion_animation":
            animation = arguments.get("animation", "")
            if animation not in VALID_ANIMATIONS:
                return f"Animação inválida '{animation}'. Válidas: {', '.join(VALID_ANIMATIONS)}"
            try:
                await client.post(
                    f"{base_url}/action",
                    json={"type": "set_animation", "animation": animation},
                )
                return f"Animação alterada para: {animation}"
            except (httpx.ConnectError, ConnectionRefusedError, OSError):
                return "Companion não está disponível — verifique se o jogo está aberto com o mod carregado"

        elif name == "get_game_state":
            try:
                resp = await client.get(f"{base_url}/state")
                state = resp.json()
                return json.dumps(state, ensure_ascii=False)
            except (httpx.ConnectError, ConnectionRefusedError, OSError):
                return "Jogo não está disponível"

        elif name == "add_session_note":
            if session_manager:
                session_manager.add_note(arguments["text"])
                return f"Nota adicionada: {arguments['text'][:50]}"
            return "Nenhuma sessão ativa"

        elif name == "get_session_summary":
            if session_manager:
                summary = session_manager.get_summary()
                return json.dumps(summary, ensure_ascii=False, indent=2)
            return "Nenhuma sessão ativa"

        return f"Ferramenta desconhecida: {name}"

    except Exception as e:
        logger.error(f"Erro na tool {name}: {e}")
        return f"Erro: {e}"


# ============================================================================
# Main
# ============================================================================

async def main():
    logging.basicConfig(level=logging.INFO)

    server = create_server()
    session_manager = CompanionSessionManager()
    base_url = DEFAULT_MOD_URL

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="send_companion_message",
                description="Envia mensagem para exibir como balão sobre o companion no jogo",
                inputSchema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            ),
            Tool(
                name="move_companion_to",
                description=(
                    "Move o companion (borboleta Sky) no mundo do jogo. "
                    "Estratégias: "
                    "follow_player = segue o jogador mantendo distância (~3 unidades); "
                    "goto_coords = vai para coordenadas específicas (requer x, y, z); "
                    "goto_named = vai para local nomeado cadastrado (requer name, ex: 'base'); "
                    "stay = para no local atual."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "strategy": {
                            "type": "string",
                            "enum": ["follow_player", "goto_coords", "goto_named", "stay"],
                            "description": "Estratégia de movimentação do companion",
                        },
                        "x": {"type": "number", "description": "Coordenada X (apenas para goto_coords)"},
                        "y": {"type": "number", "description": "Coordenada Y / altura (apenas para goto_coords)"},
                        "z": {"type": "number", "description": "Coordenada Z (apenas para goto_coords)"},
                        "name": {"type": "string", "description": "Nome do local cadastrado (apenas para goto_named, ex: 'base', 'cave')"},
                    },
                    "required": ["strategy"],
                },
            ),
            Tool(
                name="set_companion_animation",
                description="Muda animação do companion: idle, thinking, speaking",
                inputSchema={
                    "type": "object",
                    "properties": {"animation": {"type": "string", "enum": list(VALID_ANIMATIONS)}},
                    "required": ["animation"],
                },
            ),
            Tool(
                name="get_game_state",
                description="Retorna estado atual do jogo (terraform, jogador, inventário)",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="add_session_note",
                description="Adiciona nota à sessão de jogatina atual",
                inputSchema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            ),
            Tool(
                name="get_session_summary",
                description="Retorna resumo da sessão de jogatina",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="test_channel_push",
                description="DIAGNÓSTICO: testa se notificação push chega ao Claude Code",
                inputSchema={"type": "object", "properties": {"text": {"type": "string"}}, "required": []},
            ),
        ]

    _write_stream = None

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        nonlocal _write_stream

        if name == "test_channel_push":
            if _write_stream is None:
                return [TextContent(type="text", text="write_stream não disponível")]
            await send_channel_notification(
                _write_stream,
                arguments.get("text", "teste de push"),
                source="diagnostic",
            )
            return [TextContent(type="text", text=f"Notificação enviada: {arguments.get('text', 'teste')}")]

        async with httpx.AsyncClient() as client:
            result = await handle_tool_call(
                name, arguments,
                http_client=client,
                base_url=base_url,
                session_manager=session_manager,
            )
            return [TextContent(type="text", text=result)]

    async with stdio_server() as (read_stream, write_stream):
        _write_stream = write_stream

        # HTTP server direto — mod POSTa eventos aqui
        app = web.Application()
        app.router.add_post("/incoming", create_push_handler(write_stream, session_manager))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", MCP_LISTEN_PORT)
        await site.start()
        logger.info(f"[PUSH] HTTP server ouvindo em localhost:{MCP_LISTEN_PORT}")

        opts = server.create_initialization_options(
            experimental_capabilities={"claude/channel": {}}
        )
        await server.run(read_stream, write_stream, opts)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
