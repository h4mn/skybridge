"""Mock HTTP server que simula o mod C# do Planet Crafter.

Usado em testes E2E para validar a pipeline MCP completa sem o jogo real.

Endpoints:
- GET /state    → estado do jogo (terraform, jogador, inventário)
- GET /events   → fila de eventos (suporta ?since=timestamp)
- POST /action  → comandos (show_message, set_animation, move)
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse, parse_qs


class MockModHandler(BaseHTTPRequestHandler):
    """Handler HTTP que simula as rotas do mod."""

    # Compartilhado entre threads — acessado via server.state/events/actions
    def log_message(self, format, *args):
        pass  # Silencia logs do HTTP server

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/state":
            self._send_json(self.server.game_state)

        elif parsed.path == "/events":
            qs = parse_qs(parsed.query)
            since = int(qs.get("since", [0])[0])
            events = [
                e for e in self.server.events if e.get("timestamp", 0) > since
            ]
            self._send_json(events)

        else:
            self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/action":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            action = json.loads(body) if body else {}
            self.server.actions.append(action)

            # Executar ação no estado interno
            action_type = action.get("type", "")
            if action_type == "show_message":
                self.server.last_message = action.get("text", "")
            elif action_type == "set_animation":
                self.server.last_animation = action.get("animation", "")
            elif action_type == "move":
                self.server.last_move = action.get("strategy", "")

            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "not found"}, status=404)

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class MockModServer:
    """Servidor mock do mod Planet Crafter para testes E2E.

    Uso:
        async with MockModServer() as mock:
            mock.add_event("milestone", "Primeira chuva!")
            # ... testar pipeline MCP contra mock.base_url
    """

    def __init__(self, port: int = 0):
        self._port = port
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

        # Estado do "jogo"
        self.game_state: dict = {
            "Terraform": {
                "Terraformation": 0.0,
                "Heat": 0.0,
                "Oxygen": 0.0,
                "Pressure": 0.0,
                "Plants": 0.0,
                "Insects": 0.0,
            },
            "Player": {"Position": [0.0, 0.0, 0.0]},
            "Inventory": [],
            "RecentEvents": [],
        }
        self.events: list[dict] = []
        self.actions: list[dict] = []
        self.last_message: str | None = None
        self.last_animation: str | None = None
        self.last_move: str | None = None

    @property
    def base_url(self) -> str:
        return f"http://localhost:{self._server.server_address[1]}"

    @property
    def port(self) -> int:
        return self._server.server_address[1]

    def start(self):
        self._server = HTTPServer(("localhost", self._port), MockModHandler)
        self._server.game_state = self.game_state
        self._server.events = self.events
        self._server.actions = self.actions
        self._server.last_message = self.last_message
        self._server.last_animation = self.last_animation
        self._server.last_move = self.last_move

        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server = None

    def add_event(self, event_type: str, description: str, timestamp: int | None = None):
        import time as _time
        event = {
            "type": event_type,
            "description": description,
            "timestamp": timestamp or int(_time.time()),
        }
        self.events.append(event)
        # Sincronizar com o server (thread-safe via GIL)
        if self._server:
            self._server.events = self.events

    def set_game_state(self, **kwargs):
        """Atualiza estado do jogo (ex: set_game_state(Oxygen=45.2))"""
        if "Oxygen" in kwargs:
            self.game_state["Terraform"]["Oxygen"] = kwargs["Oxygen"]
        if "Insects" in kwargs:
            self.game_state["Terraform"]["Insects"] = kwargs["Insects"]
        if "Position" in kwargs:
            self.game_state["Player"]["Position"] = kwargs["Position"]
        if self._server:
            self._server.game_state = self.game_state

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
