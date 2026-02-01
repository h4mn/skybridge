# PRD016: Domain Events para Skybridge

**Status:** 🔄 Em Implementação
**Data:** 2026-01-17
**Última atualização:** 2026-01-21
**Autor:** Sky
**Versão:** 1.1
**Relacionado:** Problema #6 (ANALISE_PROBLEMAS_ATUAIS.md)
**Padrão:** Domain-Driven Design (Evans)
**Implementação:** PRD018 Fase 0 (Completa)

---

## Status de Implementação

✅ **Fase 0 do PRD018 COMPLETA** (2026-01-21)

### Componentes Implementados

| Componente | Arquivo | Status |
|------------|---------|--------|
| DomainEvent base class | `src/core/domain_events/domain_event.py` | ✅ |
| EventBus interface | `src/core/domain_events/event_bus.py` | ✅ |
| InMemoryEventBus | `src/infra/domain_events/in_memory_event_bus.py` | ✅ |
| Job Events (7 eventos) | `src/core/domain_events/job_events.py` | ✅ |
| Issue Events (5 eventos) | `src/core/domain_events/issue_events.py` | ✅ |
| Trello Events (5 eventos) | `src/core/domain_events/trello_events.py` | ✅ |
| TrelloEventListener | `src/core/webhooks/infrastructure/listeners/trello_event_listener.py` | ✅ |
| NotificationEventListener | `src/core/webhooks/infrastructure/listeners/notification_event_listener.py` | ✅ |
| MetricsEventListener | `src/core/webhooks/infrastructure/listeners/metrics_event_listener.py` | ✅ |

### Componentes Migrados

| Componente | Alteração | Status |
|------------|-----------|--------|
| WebhookProcessor | Emite `IssueReceivedEvent` | ✅ |
| JobOrchestrator | Emite `JobStartedEvent`, `JobCompletedEvent`, `JobFailedEvent` | ✅ |

### Arquitetura Atual

```
WebhookProcessor → emit(IssueReceivedEvent) → EventBus
                                                        ↓
JobOrchestrator → emit(JobStartedEvent) ─────────→ [TrelloEventListener]
                                                        ↓
                                              [NotificationEventListener]
                                                        ↓
                                               [MetricsEventListener]
```

---

---

## 📋 Resumo Executivo

Implementar **Domain Events** para desacoplar componentes via comunicação assíncrona baseada em eventos, permitindo que múltiplos listeners reajam a mudanças de domínio sem acoplamento direto.

### Problema
Atualmente componentes se comunicam via **chamadas diretas**, criando acoplamento alto:

```python
# WebhookProcessor conhece TrelloIntegrationService
trello_card_id = await self.trello_service.create_card_from_github_issue(...)

# JobOrchestrator conhece TrelloIntegrationService
await self.trello_service.update_card_progress(...)
```

**Problemas desta abordagem:**
- 🔗 **Acoplamento forte**: Mudar Trello exige mudar WebhookProcessor
- ❌ **Difícil adicionar listeners**: Para notificar Discord, precisa mudar código existente
- ❌ **Impossível replay**: Eventos passados não podem ser reprocessados
- ❌ **Difícil testar**: Testes unitários precisam mockar dependências diretas

### Solução
Implementar **Domain Events** following Martin Fowler's pattern:

```
Componente A → Domain Event → Event Bus → [Listener 1, Listener 2, Listener 3]
```

**Benefícios:**
- ✅ **Desacoplamento**: Componentes não se conhecem diretamente
- ✅ **Extensibilidade**: Adicionar novos listeners sem mudar código existente
- ✅ **Replay**: Eventos podem ser persistidos e reprocessados
- ✅ **Testabilidade**: Testes unitários podem verificar eventos emitidos

---

## 🎯 Objetivos

### Primários
- [ ] Implementar `DomainEvent` base class
- [ ] Criar `EventBus` em memória para MVP
- [ ] Migrar `WebhookProcessor` para emitir eventos
- [ ] Migrar `TrelloIntegrationService` para listener
- [ ] Adicionar listener de notificação (Discord/email)

### Secundários
- [ ] Persistir eventos em log/DB
- [ ] Implementar replay de eventos
- [ ] Adicionar métricas de eventos
- [ ] Documentar catálogo de eventos

### Não-Objetivos
- ❌ Message broker externo (RabbitMQ, Kafka) = Fase 3
- ❌ Event Sourcing completo = Apenas Domain Events
- ❌ CQRS (Command Query Responsibility Segregation) = Futuro

---

## 📐 Convenções de Nomenclatura

Domain Events seguem padrão **Past Tense** (algo que aconteceu):

| Evento | Significado |
|--------|-------------|
| `JobCreatedEvent` | Um job foi criado e enfileirado |
| `JobStartedEvent` | Um job começou a ser processado |
| `JobCompletedEvent` | Um job completou com sucesso |
| `JobFailedEvent` | Um job falhou |
| `IssueReceivedEvent` | Webhook de issue foi recebido |
| `TrelloCardCreatedEvent` | Card foi criado no Trello |
| `TrelloCardUpdatedEvent` | Card foi atualizado no Trello |
| `AgentSpawnedEvent` | Agente foi spawnado |
| `AgentCompletedEvent` | Agente completou execução |

---

## 🏗️ Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│  Event Emitter (Quem Emite)                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ WebhookProcessor.process_github_issue()                   │  │
│  │   → emit(IssueReceivedEvent)                             │  │
│  │                                                            │  │
│  │ JobOrchestrator.execute_job()                            │  │
│  │   → emit(JobStartedEvent)                                │  │
│  │   → emit(JobCompletedEvent)                              │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Event Bus (Middleware)                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ InMemoryEventBus                                          │  │
│  │   - subscribe(event_type, handler)                       │  │
│  │   - publish(domain_event)                                │  │
│  │   - unsubscribe(event_type, handler)                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│  FUTURO: Redis Pub/Sub, RabbitMQ, Kafka                        │
├─────────────────────────────────────────────────────────────────┤
│  Event Listeners (Quem Consome)                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ TrelloEventListener                                       │  │
│  │   on(IssueReceivedEvent) → create_card()                 │  │
│  │   on(JobCompletedEvent) → mark_complete()                │  │
│  │                                                            │  │
│  │ NotificationEventListener                                 │  │
│  │   on(JobFailedEvent) → send_alert()                      │  │
│  │                                                            │  │
│  │ MetricsEventListener                                      │  │
│  │   on(JobCompletedEvent) → record_metrics()               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementação

### Fase 1: Core (3-4 dias)

#### 1.1 DomainEvent Base Class

```python
# src/core/domain_events/domain_event.py

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

@dataclass
class DomainEvent:
    """Evento de domínio base."""

    event_id: str
    occurred_at: datetime
    aggregate_id: str  # ID da entidade que gerou o evento
    aggregate_type: str  # Tipo da entidade (Job, Issue, TrelloCard)
    event_type: str  # Tipo do evento (JobCreated, etc)
    payload: Dict[str, Any]  # Dados do evento

    def __init__(
        self,
        aggregate_id: str,
        aggregate_type: str,
        event_type: str,
        payload: Dict[str, Any],
    ):
        self.event_id = str(uuid4())
        self.occurred_at = datetime.utcnow()
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.event_type = event_type
        self.payload = payload

    def to_dict(self) -> Dict:
        """Serializa para dict."""
        return {
            "event_id": self.event_id,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "event_type": self.event_type,
            "payload": self.payload,
        }
```

#### 1.2 EventBus Interface

```python
# src/core/domain_events/event_bus.py

from abc import ABC, abstractmethod
from typing import Callable, List, Type
from core.domain_events.domain_event import DomainEvent

class EventBus(ABC):
    """Interface para bus de eventos."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publica evento no bus."""
        pass

    @abstractmethod
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], None]
    ) -> None:
        """Inscreve handler para tipo de evento."""
        pass

    @abstractmethod
    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], None]
    ) -> None:
        """Desinscreve handler."""
        pass
```

#### 1.3 InMemoryEventBus Implementation

```python
# src/infrastructure/domain_events/in_memory_event_bus.py

import asyncio
from typing import Callable, Dict, List
from core.domain_events.event_bus import EventBus
from core.domain_events.domain_event import DomainEvent

class InMemoryEventBus(EventBus):
    """Implementação em memória do event bus."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, event: DomainEvent) -> None:
        """Publica evento e notifica todos os handlers inscritos."""
        handlers = self._handlers.get(event.event_type, [])

        # Executa handlers em paralelo
        tasks = [
            self._safe_execute(handler, event)
            for handler in handlers
        ]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], None]
    ) -> None:
        """Inscreve handler."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], None]
    ) -> None:
        """Desinscreve handler."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def _safe_execute(
        self,
        handler: Callable[[DomainEvent], None],
        event: DomainEvent
    ) -> None:
        """Executa handler capturando exceções."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            # Log mas não falha publicação
            logger = logging.getLogger(__name__)
            logger.error(
                f"Handler falhou para evento {event.event_type}: {e}",
                exc_info=True
            )
```

### Fase 2: Migrar Componentes (3-4 dias)

#### 2.1 Eventos Específicos

```python
# src/core/domain_events/events.py

from core.domain_events.domain_event import DomainEvent

class JobCreatedEvent(DomainEvent):
    """Job foi criado e enfileirado."""

    def __init__(self, job_id: str, issue_number: int):
        super().__init__(
            aggregate_id=job_id,
            aggregate_type="Job",
            event_type="JobCreated",
            payload={
                "job_id": job_id,
                "issue_number": issue_number,
            }
        )

class JobStartedEvent(DomainEvent):
    """Job começou a ser processado."""

    def __init__(self, job_id: str, skill: str):
        super().__init__(
            aggregate_id=job_id,
            aggregate_type="Job",
            event_type="JobStarted",
            payload={
                "job_id": job_id,
                "skill": skill,
            }
        )

class JobCompletedEvent(DomainEvent):
    """Job completou com sucesso."""

    def __init__(self, job_id: str, summary: str, changes: List[str]):
        super().__init__(
            aggregate_id=job_id,
            aggregate_type="Job",
            event_type="JobCompleted",
            payload={
                "job_id": job_id,
                "summary": summary,
                "changes": changes,
            }
        )

class JobFailedEvent(DomainEvent):
    """Job falhou."""

    def __init__(self, job_id: str, error: str):
        super().__init__(
            aggregate_id=job_id,
            aggregate_type="Job",
            event_type="JobFailed",
            payload={
                "job_id": job_id,
                "error": error,
            }
        )

class IssueReceivedEvent(DomainEvent):
    """Webhook de issue foi recebido."""

    def __init__(self, issue_number: int, title: str, action: str):
        super().__init__(
            aggregate_id=str(issue_number),
            aggregate_type="Issue",
            event_type="IssueReceived",
            payload={
                "issue_number": issue_number,
                "title": title,
                "action": action,
            }
        )
```

#### 2.2 Migrar WebhookProcessor

```python
# src/core/webhooks/application/webhook_processor.py

class WebhookProcessor:
    def __init__(
        self,
        job_queue: "JobQueuePort",
        trello_service: "TrelloIntegrationService" = None,
        event_bus: "EventBus" = None,  # NOVO
    ):
        self.job_queue = job_queue
        self.trello_service = trello_service
        self.event_bus = event_bus or InMemoryEventBus()  # NOVO

    async def process_github_issue(
        self, payload: dict, event_type: str, ...
    ) -> Result[str, str]:
        # ... validações ...

        # ANTES: criava card diretamente
        # trello_card_id = await self._create_trello_card(...)

        # DEPOIS: emite evento
        await self.event_bus.publish(IssueReceivedEvent(
            issue_number=issue_number,
            title=issue_data.get("title"),
            action=payload.get("action", "opened")
        ))

        # Cria job
        job = WebhookJob.create(event)
        await self.job_queue.enqueue(job)

        # Emite evento de job criado
        await self.event_bus.publish(JobCreatedEvent(
            job_id=job.job_id,
            issue_number=issue_number
        ))

        return Result.ok(job.job_id)
```

#### 2.3 TrelloEventListener

```python
# src/infrastructure/trello/trello_event_listener.py

class TrelloEventListener:
    """Listener para criar/atualizar cards no Trello."""

    def __init__(self, trello_service: "TrelloIntegrationService"):
        self.trello_service = trello_service

    async def on_issue_received(self, event: IssueReceivedEvent):
        """Cria card no Trello quando issue é recebida."""
        if event.payload["action"] == "opened":
            # Busca dados da issue do payload ou armazena no evento
            result = await self.trello_service.create_card_from_github_issue(
                issue_number=event.payload["issue_number"],
                # ... outros parâmetros ...
            )

            if result.is_ok:
                card_id = result.unwrap()
                # Emite evento de card criado
                await self.event_bus.publish(TrelloCardCreatedEvent(
                    card_id=card_id,
                    issue_number=event.payload["issue_number"]
                ))

    async def on_job_completed(self, event: JobCompletedEvent):
        """Atualiza card quando job completa."""
        # Busca card_id do metadata do job
        # await self.trello_service.mark_card_complete(...)
        pass

    def register(self, event_bus: "EventBus"):
        """Registra handlers no event bus."""
        event_bus.subscribe("IssueReceived", self.on_issue_received)
        event_bus.subscribe("JobCompleted", self.on_job_completed)
```

### Fase 3: Novos Listeners (2-3 dias)

#### 3.1 NotificationEventListener

```python
# src/infrastructure/notifications/notification_event_listener.py

class NotificationEventListener:
    """Envia notificações baseadas em eventos."""

    async def on_job_failed(self, event: JobFailedEvent):
        """Envia alerta quando job falha."""
        message = f"❌ Job {event.payload['job_id']} falhou: {event.payload['error']}"

        # Envia para Discord
        await self._send_discord_message(message)

        # OU envia email
        # await self._send_email(message)

    async def on_job_completed(self, event: JobCompletedEvent):
        """Envia notificação quando job completa."""
        message = (
            f"✅ Job {event.payload['job_id']} completado!\n"
            f"Resumo: {event.payload['summary']}"
        )
        await self._send_discord_message(message)
```

#### 3.2 MetricsEventListener

```python
# src/infrastructure/metrics/metrics_event_listener.py

class MetricsEventListener:
    """Registra métricas baseadas em eventos."""

    def __init__(self, metrics_store: "MetricsStore"):
        self.metrics = metrics_store

    async def on_job_created(self, event: JobCreatedEvent):
        """Registra contador de jobs criados."""
        self.metrics.increment("jobs_created")

    async def on_job_completed(self, event: JobCompletedEvent):
        """Registra jobs completados."""
        self.metrics.increment("jobs_completed")

    async def on_job_failed(self, event: JobFailedEvent):
        """Registra jobs falhados."""
        self.metrics.increment("jobs_failed")
```

---

## ✅ Critérios de Sucesso

### Mínimo Viável (MVP)
- [ ] `DomainEvent` base class implementada
- [ ] `InMemoryEventBus` funcionando
- [ ] `WebhookProcessor` emitindo eventos
- [ ] `TrelloEventListener` criando cards
- [ ] 1 novo listener (notificação ou métricas)

### Completo
- [ ] Todos os componentes principais migrados
- [ ] 3+ listeners implementados
- [ ] Testes cobrindo fluxo completo
- [ ] Documentação de catálogo de eventos

### Stretch (Futuro)
- [ ] Event persistence em Redis/DB
- [ ] Replay de eventos
- [ ] Dead letter queue para eventos falhados
- [ ] Message broker externo (RabbitMQ)

---

## 🧪 Testes

```python
# tests/core/domain_events/test_event_bus.py

@pytest.mark.asyncio
async def test_event_bus_publish():
    bus = InMemoryEventBus()

    received = []

    def handler(event):
        received.append(event)

    bus.subscribe("TestEvent", handler)

    await bus.publish(DomainEvent(
        aggregate_id="123",
        aggregate_type="Test",
        event_type="TestEvent",
        payload={}
    ))

    assert len(received) == 1
    assert received[0].event_type == "TestEvent"

@pytest.mark.asyncio
async def test_multiple_listeners():
    bus = InMemoryEventBus()

    listener1_calls = []
    listener2_calls = []

    def listener1(event):
        listener1_calls.append(event)

    def listener2(event):
        listener2_calls.append(event)

    bus.subscribe("TestEvent", listener1)
    bus.subscribe("TestEvent", listener2)

    await bus.publish(DomainEvent(...))

    assert len(listener1_calls) == 1
    assert len(listener2_calls) == 1
```

---

## 📊 Antes vs Depois

### Antes (Acoplado)

```python
# WebhookProcessor depende diretamente de TrelloIntegrationService
class WebhookProcessor:
    def __init__(self, trello_service: TrelloIntegrationService):
        self.trello_service = trello_service

    async def process_github_issue(self, ...):
        # CHAMADA DIRETA
        trello_card_id = await self.trello_service.create_card(...)
```

**Problemas:**
- Para adicionar notificação Discord, precisa mudar `WebhookProcessor`
- Para testar, precisa mockar `TrelloIntegrationService`
- Acoplamento forte entre componentes

### Depois (Desacoplado)

```python
# WebhookProcessor apenas emite eventos
class WebhookProcessor:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def process_github_issue(self, ...):
        # EMITE EVENTO
        await self.event_bus.publish(IssueReceivedEvent(...))

# Listener separado
class TrelloEventListener:
    async def on_issue_received(self, event):
        await self.trello_service.create_card(...)

# Novo listener sem mudar código existente
class DiscordEventListener:
    async def on_issue_received(self, event):
        await self.discord.notify(...)
```

**Benefícios:**
- Adicionar `DiscordEventListener` **não exige mudar** `WebhookProcessor`
- Testes podem verificar eventos emitidos sem mockar dependências
- Componentes são independentes

---

## 📅 Roadmap

| Sprint | Dias | Entrega |
|--------|------|---------|
| **Sprint 1** | 3-4 | Core (DomainEvent, EventBus, InMemoryEventBus) |
| **Sprint 2** | 3-4 | Migrar WebhookProcessor + TrelloEventListener |
| **Sprint 3** | 2-3 | Novos listeners (Notificação, Métricas) |
| **Total** | **8-11 dias** | Sistema de Domain Events completo |

---

## 🔄 Relacionamento com Outros PRDs

| PRD | Relação | Descrição |
|-----|---------|-----------|
| **PRD013** | Evolui | Agentes (PRD013) emitirão eventos |
| **PRD015** | Complementa | Métricas (PRD015) podem coletar via MetricsEventListener |
| **PRD014** | Alimenta | WebUI Dashboard pode consumir eventos via WebSocket |

---

## 💭 Perguntas Frequentes

**Q: Por que não RabbitMQ/Kafka desde o início?**
A: `InMemoryEventBus` é suficiente para MVP e simplifica setup. Message brokers podem ser adicionados depois trocando apenas a implementação do EventBus (mesma interface).

**Q: Eventos são síncronos ou assíncronos?**
A: Assíncronos por padrão. `publish()` retorna imediatamente, handlers executam em background. Para síncrono, use `await` no publish.

**Q: O que acontece se um listener falhar?**
A: Exceção é logada mas não afeta outros listeners. Implementação atual usa `return_exceptions=True` no `gather()`.

**Q: Como garantir ordem de eventos?**
A: Para MVP, eventos são processados na ordem que chegam. Para ordenação estrita, use número de sequência ou particionamento por aggregate_id.

---

## 📊 Valor de Negócio

### Antes
> "Para adicionar notificação no Discord, preciso mudar `WebhookProcessor`, `JobOrchestrator` e testar tudo de novo..."

### Depois
> "Para adicionar notificação no Discord, crio `DiscordEventListener` e registro no EventBus. Não mudo código existente."

**Benefícios:**
- ✅ **Extensibilidade**: Adicionar features sem mudar código existente
- ✅ **Manutenibilidade**: Componentes independentes são mais fáceis de entender
- ✅ **Testabilidade**: Testes unitários mais simples
- ✅ **Flexibilidade**: Fácil adicionar/reordenar lógica

---

## 🎯 Quando Implementar?

### Recomendado: Depois de Métricas (PRD015)

**Ordem sugerida:**
1. **PRD015** (Métricas) - 5-8 dias
2. Correção de **Problema #1** (filas separadas) - 2-4h
3. **PRD016** (Domain Events) - 8-11 dias

**Justificativa:**
- Métricas primeiro permitem observar o sistema atual
- Domain Events mudam arquitetura significativamente
- Melhor fazer mudanças arquiteturais quando sistema está estável e observável

---

> "Desacoplamento é a chave para sistemas que evoluem" – made by Sky 🔗
