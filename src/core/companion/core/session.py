"""Gerenciamento de sessão de jogatina."""

from __future__ import annotations

from datetime import datetime

from .companion import CompanionState


class CompanionSession:
    """Ciclo de vida de uma sessão de companion."""

    def __init__(self, game: str) -> None:
        self.state = CompanionState(
            game=game,
            session_start=datetime.now(),
        )

    def start(self) -> CompanionState:
        self.state.active = True
        return self.state

    def end(self) -> CompanionState:
        self.state.active = False
        return self.state
