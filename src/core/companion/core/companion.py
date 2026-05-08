"""Companion principal — state e memória de sessão de jogatina."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GameEvent:
    """Evento ocorrido durante a sessão de jogo."""
    timestamp: datetime
    event_type: str  # "discovery", "death", "craft", "build", "combat", "chat"
    description: str
    metadata: dict = field(default_factory=dict)


@dataclass
class CompanionState:
    """Estado da companheira durante a sessão."""
    game: str
    session_start: datetime
    events: list[GameEvent] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    active: bool = True

    def add_event(self, event_type: str, description: str, **meta) -> GameEvent:
        event = GameEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            description=description,
            metadata=meta,
        )
        self.events.append(event)
        return event

    def add_note(self, note: str) -> None:
        self.notes.append(note)

    def summary(self) -> str:
        duration = datetime.now() - self.session_start
        lines = [
            f"Sessão {self.game} — {duration.seconds // 60}min",
            f"Eventos: {len(self.events)} | Notas: {len(self.notes)}",
        ]
        if self.events:
            lines.append("Últimos eventos:")
            for e in self.events[-5:]:
                lines.append(f"  [{e.event_type}] {e.description}")
        return "\n".join(lines)
