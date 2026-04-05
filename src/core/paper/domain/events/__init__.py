"""
Eventos de Domínio - Paper Trading.

Eventos de domínio representam fatos ocorridos no sistema
que podem disparar reações em outros componentes.

## Eventos Disponíveis

### Ordem (OrdemEvents)
- **OrdemCriada**: Nova ordem registrada (usuário cria ordem)
- **OrdemExecutada**: Ordem executada (broker confirma)
- **OrdemCancelada**: Ordem cancelada (usuário ou sistema)

### Risco/Posição (RiscoEvents)
- **StopLossAcionado**: Stop loss disparado (preço atinge nível)
- **PosicaoAtualizada**: Posição modificada (execução altera posição)

## EventBus

Sistema publish/subscribe para comunicação entre componentes:

```python
from src.core.paper.domain.events import get_event_bus, OrdemCriada, Lado

# Inscrever handler
bus = get_event_bus()
bus.subscribe(OrdemCriada, lambda e: print(f"Ordem {e.ordem_id} criada"))

# Publicar evento
event = OrdemCriada(
    ordem_id="ordem-001",
    ticker="PETR4",
    lado=Lado.COMPRA,
    quantidade=100
)
bus.publish(event)
```

## Base DomainEvent

Todos os eventos herdam de `DomainEvent` e contêm:
- `occurred_at`: Timestamp de quando ocorreu
- `event_type`: Tipo do evento (nome da classe)
- `metadata`: Dados adicionais opcionais

## Serialização

Eventos podem ser serializados/deserializados:

```python
# Para dict
event_dict = event.to_dict()

# De dict
novo_event = OrdemCriada.from_dict(event_dict)
```
"""

from .base_event import DomainEvent
from .event_bus import EventBus, get_event_bus, reset_event_bus
from .ordem_events import OrdemCriada, OrdemExecutada, OrdemCancelada, Lado
from .risco_events import StopLossAcionado, PosicaoAtualizada

__all__ = [
    # Base
    "DomainEvent",
    # EventBus
    "EventBus",
    "get_event_bus",
    "reset_event_bus",
    # Ordem Events
    "OrdemCriada",
    "OrdemExecutada",
    "OrdemCancelada",
    "Lado",
    # Risco Events
    "StopLossAcionado",
    "PosicaoAtualizada",
]
