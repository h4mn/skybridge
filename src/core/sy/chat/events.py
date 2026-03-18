# coding: utf-8
"""
Eventos de Domínio - Chat + TTS.

DOC: openspec/changes/refactor-chat-event-driven/specs/

Eventos que representam o ciclo de vida de um turno de chat e a interação
com o serviço TTS. Todos os eventos herdam de BaseEvent e incluem timestamp.

## Fluxo de Eventos Típicos

1. TurnStartedEvent (início do processamento)
2. StreamChunkEvent (chunks de texto chegando)
3. TTSStartedEvent / TTSCompletedEvent (ciclos de fala)
4. TurnCompletedEvent (fim do processamento)

## Exemplo

```python
# Início do turno
await bus.publish(TurnStartedEvent(
    turn_id="turn-123",
    user_message="Olá"
))

# Chunk de texto
await bus.publish(StreamChunkEvent(
    turn_id="turn-123",
    content="Olá! ",
    event_type="TEXT"
))

# Fim do turno
await bus.publish(TurnCompletedEvent(
    turn_id="turn-123",
    final_text="Olá! Como posso ajudar?",
    duration_ms=150
))
```
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from core.sy.events.event_bus import BaseEvent


# ============================================================================
# Eventos de Chat / Stream
# ============================================================================

@dataclass
class StreamChunkEvent(BaseEvent):
    """
    Evento representando um chunk do stream de resposta do Claude.

    Disparado para cada chunk recebido do Claude Agent SDK durante
    stream_response(). Pode ser TEXT, THOUGHT, TOOL_START, etc.

    Attributes:
        turn_id: Identificador único do turno
        content: Conteúdo do chunk (texto ou descrição)
        event_type: Tipo de stream event (TEXT, THOUGHT, TOOL_START, TOOL_RESULT, ERROR)
        metadata: Dados adicionais do stream (tool name, exit code, etc)
    """

    turn_id: str
    content: str
    event_type: Literal["TEXT", "THOUGHT", "TOOL_START", "TOOL_RESULT", "ERROR"]
    metadata: dict[str, any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"StreamChunkEvent(turn={self.turn_id}, type={self.event_type}, content='{self.content[:30]}...')"


@dataclass
class TurnStartedEvent(BaseEvent):
    """
    Evento disparado no início do processamento de um turno.

    Marca o momento em que o usuário envia uma mensagem e o chat
    começa a processar. Antes de qualquer stream ou TTS.

    Attributes:
        turn_id: Identificador único do turno
        user_message: Mensagem enviada pelo usuário
        metadata: Dados adicionais (model, temperature, etc)
    """

    turn_id: str
    user_message: str
    metadata: dict[str, any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"TurnStartedEvent(turn={self.turn_id}, message='{self.user_message[:30]}...')"


@dataclass
class TurnCompletedEvent(BaseEvent):
    """
    Evento disparado quando o turno é completado.

    Marca o fim do processamento, após todos os chunks serem consumidos
    e o TTS terminar (se habilitado).

    Attributes:
        turn_id: Identificador único do turno
        final_text: Texto final completo do turno
        duration_ms: Duração total do processamento em ms
        metadata: Métricas (tokens in/out, latency, etc)
    """

    turn_id: str
    final_text: str
    duration_ms: float
    metadata: dict[str, any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"TurnCompletedEvent(turn={self.turn_id}, duration={self.duration_ms:.0f}ms, text='{self.final_text[:30]}...')"


# ============================================================================
# Eventos de TTS
# ============================================================================

@dataclass
class TTSStartedEvent(BaseEvent):
    """
    Evento disparado quando o TTS começa a falar.

    Indica que o serviço TTS iniciou a reprodução de áudio.
    Usado para controle de waveform/indicators visuais.

    Attributes:
        turn_id: Identificador único do turno
        text: Texto sendo falado
        mode: Modo de voz (NORMAL, THINKING)
        metadata: Dados adicionais (duration previsto, etc)
    """

    turn_id: str
    text: str
    mode: Literal["NORMAL", "THINKING"]
    metadata: dict[str, any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"TTSStartedEvent(turn={self.turn_id}, mode={self.mode}, text='{self.text[:30]}...')"


@dataclass
class TTSCompletedEvent(BaseEvent):
    """
    Evento disparado quando o TTS termina de falar.

    Indica que a reprodução de áudio foi concluída. Usado para
    parar waveform/indicators visuais.

    Attributes:
        turn_id: Identificador único do turno
        text: Texto que foi falado
        duration_ms: Duração da fala em ms
        metadata: Dados adicionais (interrupted, error, etc)
    """

    turn_id: str
    text: str
    duration_ms: float
    metadata: dict[str, any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"TTSCompletedEvent(turn={self.turn_id}, duration={self.duration_ms:.0f}ms, text='{self.text[:30]}...')"
