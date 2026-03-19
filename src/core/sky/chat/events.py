# coding: utf-8
"""
Eventos de domínio para o Chat.

DOC: openspec/changes/refactor-chat-event-driven/design.md

Eventos usados para comunicação entre ChatOrchestrator, TTSService e UI
via EventBus (pub/sub loose-coupled).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.sky.events import BaseEvent


@dataclass
class TurnStartedEvent(BaseEvent):
    """
    Evento emitido quando um turno de chat começa.

    Attributes:
        turn_id: ID único do turno
        user_message: Mensagem do usuário que iniciou o turno
        timestamp: Quando o turno iniciou
        metadata: Dados adicionais opcionais
    """
    turn_id: str
    user_message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChunkEvent(BaseEvent):
    """
    Evento emitido para cada chunk do stream de resposta.

    Attributes:
        turn_id: ID do turno ao qual este chunk pertence
        content: Conteúdo do chunk (texto, thought, etc.)
        event_type: Tipo de evento ("TEXT", "THOUGHT", "TOOL_START", "TOOL_RESULT", "ERROR")
        timestamp: Quando o chunk foi recebido
        metadata: Dados adicionais (tool name, input, etc.)
    """
    turn_id: str
    content: str
    event_type: str  # "TEXT", "THOUGHT", "TOOL_START", "TOOL_RESULT", "ERROR"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TurnCompletedEvent(BaseEvent):
    """
    Evento emitido quando um turno de chat termina.

    Attributes:
        turn_id: ID do turno que completou
        final_text: Texto final completo da resposta
        duration_ms: Duração do turno em milissegundos
        timestamp: Quando o turno completou
        metadata: Dados adicionais (métricas, etc.)
    """
    turn_id: str
    final_text: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TTSStartedEvent(BaseEvent):
    """
    Evento emitido quando TTS começa a falar.

    Attributes:
        turn_id: ID do turno ao qual este TTS pertence
        text: Texto que está sendo falado
        mode: Modo de voz ("normal", "thinking")
        timestamp: Quando o TTS iniciou
        metadata: Dados adicionais
    """
    turn_id: str
    text: str
    mode: str  # "normal", "thinking"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TTSCompletedEvent(BaseEvent):
    """
    Evento emitido quando TTS termina de falar.

    Attributes:
        turn_id: ID do turno ao qual este TTS pertence
        text: Texto que foi falado
        duration_ms: Duração da fala em milissegundos
        timestamp: Quando o TTS completou
        metadata: Dados adicionais (interrupted, etc.)
    """
    turn_id: str
    text: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
