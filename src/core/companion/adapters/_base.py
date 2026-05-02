"""Interface abstrata do adapter de jogo."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GameContext:
    """Snapshot do estado atual do jogo."""
    game: str
    player: str = ""
    position: dict[str, float] = field(default_factory=dict)
    health: float = 0.0
    inventory: list[dict[str, Any]] = field(default_factory=list)
    nearby_entities: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


class CompanionAdapter(ABC):
    """Interface que cada adapter de jogo deve implementar.

    Fluxo de dados:
    - IN (game state): recebido via Channel MCP (notificações em tempo real)
    - OUT (comandos): enviado via MCP tools (ações no jogo)
    """

    @abstractmethod
    async def connect(self) -> None:
        """Conecta ao jogo/plataforma."""

    @abstractmethod
    async def get_context(self) -> GameContext:
        """Retorna snapshot do estado atual do jogo."""

    @abstractmethod
    async def send_message(self, text: str) -> None:
        """Envia mensagem (chat/feedback) no contexto do jogo."""

    @abstractmethod
    async def execute_action(self, action: str, **params: Any) -> Any:
        """Executa uma ação no jogo (mover, craftar, atacar, etc)."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Desconecta do jogo graciosamente."""
