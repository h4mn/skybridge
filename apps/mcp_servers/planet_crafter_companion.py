#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Planet Crafter Companion — MCP Server.

MCP server que:
- Faz polling de eventos significativos do mod via HTTP
- Envia notificações em tempo real via JSONRPCNotification (claude/channel)
- Expõe tools para Claude Code interagir com o jogo
- Gerencia sessão de jogatina
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import JSONRPCMessage, JSONRPCNotification, TextContent, Tool

logger = logging.getLogger(__name__)

VALID_ANIMATIONS = ("idle", "thinking", "speaking")
DEFAULT_BASE_URL = "http://localhost:17234"
DEFAULT_POLL_INTERVAL = 10
DEFAULT_THROTTLE_SECONDS = 30
DEFAULT_TIMEOUT_FAILURES = 6  # ~60s a 10s por poll


# ============================================================================
# Session Management (Tasks 8.1-8.5)
# ============================================================================

@dataclass
class SessionEvent:
    type: str
    description: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Session:
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str | None = None
    active: bool = True
    events: list[dict] = field(default_factory=list)


class CompanionSessionManager:
    """Gerencia o ciclo de vida da sessão de jogatina."""

    def __init__(self, timeout_failures: int = DEFAULT_TIMEOUT_FAILURES):
        self.session: Session | None = None
        self._consecutive_failures = 0
        self._timeout_failures = timeout_failures

    @property
    def is_active(self) -> bool:
        return self.session is not None and self.session.active

    def on_poll_success(self) -> None:
        if self.session is None:
            self.session = Session()
        self._consecutive_failures = 0

    def on_poll_failure(self) -> None:
        if self.session is None:
            return
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._timeout_failures:
            self._end_session()

    def _end_session(self) -> None:
        if self.session:
            self.session.active = False
            self.session.end_time = datetime.now().isoformat()

    def log_event(self, event_type: str, description: str) -> None:
        if self.session:
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
# Event Poller (Tasks 7.3-7.5)
# ============================================================================

class EventPoller:
    """Faz polling de GET /events e envia notificações via MCP channel."""

    def __init__(
        self,
        base_url: str,
        write_stream: Any,
        http_client: httpx.AsyncClient | None = None,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        throttle_seconds: int = DEFAULT_THROTTLE_SECONDS,
    ):
        self.base_url = base_url
        self.write_stream = write_stream
        self.http_client = http_client or httpx.AsyncClient()
        self.poll_interval = poll_interval
        self.throttle_seconds = throttle_seconds
        self._last_notification_time: float = 0
        self._pending_events: list[dict] = []

    async def poll_once(self) -> None:
        try:
            resp = await self.http_client.get(f"{self.base_url}/events")
            resp.raise_for_status()
            events = resp.json()
        except (httpx.ConnectError, ConnectionRefusedError, OSError):
            logger.info("Mod indisponível, tentando novamente no próximo ciclo")
            return

        if not events:
            return

        now = time.monotonic()
        elapsed = now - self._last_notification_time

        if elapsed >= self.throttle_seconds:
            await self._send_notification(events)
            self._last_notification_time = now
        else:
            self._pending_events.extend(events)
            logger.debug(f"Throttled — {len(self._pending_events)} eventos pendentes")

    async def _send_notification(self, events: list[dict]) -> None:
        all_events = self._pending_events + events
        self._pending_events = []

        descriptions = "; ".join(
            f"[{e.get('type', 'unknown')}] {e.get('description', '')}"
            for e in all_events
        )

        notif = JSONRPCNotification(
            jsonrpc="2.0",
            method="notifications/claude/channel",
            params={"content": descriptions, "meta": {"event_count": len(all_events)}},
        )

        await self.write_stream.send(JSONRPCMessage(notif))
        logger.info(f"Notificação enviada: {len(all_events)} eventos")


# ============================================================================
# MCP Server & Tools (Tasks 7.1, 7.2, 7.6-7.9)
# ============================================================================

def create_server() -> Server:
    return Server("planet-crafter-channel")


def create_initialization_options() -> Any:
    server = create_server()
    opts = server.create_initialization_options()
    opts.capabilities.experimental = {"claude/channel": {}}
    return opts


async def handle_tool_call(
    name: str,
    arguments: dict,
    http_client: httpx.AsyncClient | None = None,
    base_url: str = DEFAULT_BASE_URL,
    session_manager: CompanionSessionManager | None = None,
) -> str:
    client = http_client or httpx.AsyncClient()

    try:
        if name == "send_companion_message":
            try:
                resp = await client.post(
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
            await client.post(f"{base_url}/action", json=body)
            return f"Movimento executado: {strategy}"

        elif name == "set_companion_animation":
            animation = arguments.get("animation", "")
            if animation not in VALID_ANIMATIONS:
                return f"Animação inválida '{animation}'. Válidas: {', '.join(VALID_ANIMATIONS)}"
            await client.post(
                f"{base_url}/action",
                json={"type": "set_animation", "animation": animation},
            )
            return f"Animação alterada para: {animation}"

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
# Main (para execução standalone)
# ============================================================================

async def main():
    logging.basicConfig(level=logging.INFO)

    server = create_server()
    session_manager = CompanionSessionManager()
    base_url = DEFAULT_BASE_URL

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
                        "x": {
                            "type": "number",
                            "description": "Coordenada X (apenas para goto_coords)",
                        },
                        "y": {
                            "type": "number",
                            "description": "Coordenada Y / altura (apenas para goto_coords)",
                        },
                        "z": {
                            "type": "number",
                            "description": "Coordenada Z (apenas para goto_coords)",
                        },
                        "name": {
                            "type": "string",
                            "description": "Nome do local cadastrado (apenas para goto_named, ex: 'base', 'cave')",
                        },
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
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        async with httpx.AsyncClient() as client:
            result = await handle_tool_call(
                name, arguments,
                http_client=client,
                base_url=base_url,
                session_manager=session_manager,
            )
            return [TextContent(type="text", text=result)]

    async with stdio_server() as (read_stream, write_stream):
        poller = EventPoller(base_url=base_url, write_stream=write_stream)

        async def poll_loop():
            while True:
                await poller.poll_once()
                await asyncio.sleep(DEFAULT_POLL_INTERVAL)

        asyncio.create_task(poll_loop())

        opts = server.create_initialization_options()
        opts.capabilities.experimental = {"claude/channel": {}}
        await server.run(read_stream, write_stream, opts)


if __name__ == "__main__":
    asyncio.run(main())
