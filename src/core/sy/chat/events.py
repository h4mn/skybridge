# coding: utf-8
"""
Eventos de Domínio - Chat + TTS.

DOC: openspec/changes/refactor-chat-event-driven/specs/

Eventos que representam o ciclo de vida de um turno de chat e a interação
com o serviço TTS.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Any


class BaseEvent:
    """Classe base para todos os eventos (não-dataclass)."""

    def __init__(self, timestamp: datetime | None = None, metadata: dict[str, Any] | None = None):
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(timestamp={self.timestamp.isoformat()})"


# ============================================================================
# Eventos de Chat / Stream
# ============================================================================

@dataclass
class StreamChunkEvent(BaseEvent):
    """Evento representando um chunk do stream de resposta do Claude."""

    turn_id: str
    content: str
    event_type: Literal["TEXT", "THOUGHT", "TOOL_START", "TOOL_RESULT", "ERROR"]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"StreamChunkEvent(turn={self.turn_id}, type={self.event_type}, content='{self.content[:30]}...')"


@dataclass
class TurnStartedEvent(BaseEvent):
    """Evento disparado no início do processamento de um turno."""

    turn_id: str
    user_message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"TurnStartedEvent(turn={self.turn_id}, message='{self.user_message[:30]}...')"


@dataclass
class TurnCompletedEvent(BaseEvent):
    """Evento disparado quando o turno é completado."""

    turn_id: str
    final_text: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"TurnCompletedEvent(turn={self.turn_id}, duration={self.duration_ms:.0f}ms, text='{self.final_text[:30]}...')"


# ============================================================================
# Eventos de TTS
# ============================================================================

@dataclass
class TTSStartedEvent(BaseEvent):
    """Evento disparado quando o TTS começa a falar."""

    turn_id: str
    text: str
    mode: Literal["NORMAL", "THINKING"]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"TTSStartedEvent(turn={self.turn_id}, mode={self.mode}, text='{self.text[:30]}...')"


@dataclass
class TTSCompletedEvent(BaseEvent):
    """Evento disparado quando o TTS termina de falar."""

    turn_id: str
    text: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"TTSCompletedEvent(turn={self.turn_id}, duration={self.duration_ms:.0f}ms, text='{self.text[:30]}...')"
