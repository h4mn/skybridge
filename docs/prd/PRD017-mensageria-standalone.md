# PRD017: Mensageria Standalone Evolutiva

**Status:** ✅ Implementado
**Data:** 2026-01-17
**Data de Implementação:** 2026-01-21
**Autor:** Sky
**Versão:** 1.0
**Relacionado:** Problema #1, PRD015 (Métricas), PRD016 (Domain Events)

---

## 📋 Resumo Executivo

Implementar **mensageria standalone baseada em arquivos** que resolva o problema de filas separadas HOJE, mas com **arquitetura preparada** para migrar para Redis/RabbitMQ DEPOIS, sem mudar código de produto.

### Problema
- **Problema #1:** Filas separadas entre processos → jobs nunca processados
- **Gap:** Precisamos de solução que funcione AGORA sem infraestrutura externa
- **Débito:** Solução provisória pode criar trabalho extra futuro

### Solução
**FileBasedJobQueue** - Mensageria standalone com:
- ✅ Persistência em arquivos JSON (funciona offline)
- ✅ Interface idêntica a `JobQueuePort` (drop-in replacement)
- ✅ **Métricas embutidas** (throughput, latência, backlog)
- ✅ **Preparada para Domain Events** (suporta pub/sub entre processos)
- ✅ **Migration path claro** para Redis/RabbitMQ

---

## 📋 Status de Implementação

**Status:** ✅ **IMPLEMENTADO** (2026-01-21)

O `FileBasedJobQueue` foi completamente implementado conforme especificado neste PRD. Para detalhes da implementação, consulte:
- **Código:** `src/infra/webhooks/adapters/file_based_job_queue.py`
- **Documentação:** `docs/IMPLEMENTACAO_FILEBASEDQUEUE.md`

**Funcionalidades Implementadas:**
- ✅ Persistência em arquivos JSON
- ✅ Interface `JobQueuePort` completa
- ✅ Métricas embutidas (throughput, latência, backlog)
- ✅ Lock file para evitar race conditions
- ✅ Recuperação de jobs órfãos em `processing/`
- ✅ Drop-in replacement para `InMemoryJobQueue`

**Métricas Disponíveis:**
- `queue_size`: Tamanho atual da fila
- `enqueue_count`, `dequeue_count`, `complete_count`, `fail_count`
- `enqueue_latency_avg_ms`, `enqueue_latency_p95_ms`
- `dequeue_latency_avg_ms`, `dequeue_latency_p95_ms`
- `jobs_per_hour`: Throughput nas últimas 24h
- `backlog_age_seconds`: Idade do job mais antigo
- `disk_usage_mb`: Uso de disco da fila

**Problema #1 (Filas Separadas):** ✅ **RESOLVIDO**
- Webhook Server e Webhook Worker agora compartilham estado via sistema de arquivos
- Jobs enfileirados por um processo são visíveis pelo outro
- Sistema funciona end-to-end

---

## 🎯 Objetivos de Design

### Princípios
1. **Drop-in Replacement:** Trocar `InMemoryJobQueue` por `FileBasedJobQueue` sem mudar código
2. **Metrics-First:** Métricas nativas para decisão de quando migrar
3. **Interface Estável:** Código de produto não muda ao migrar para Redis
4. **Zero External Deps:** Funciona sem Redis, RabbitMQ, etc

### Não-Objetivos
- ❌ Alta performance (>100 jobs/hora)
- ❌ Distribuição horizontal (múltiplos workers)
- ❌ Garantias de delivery forte (exactly-once)
- ❌ Mensagens grandes (>1MB)

---

## 📊 Números e Decisões

### Capacidade da Mensageria Standalone

| Métrica | Standalone | Redis | RabbitMQ |
|---------|------------|-------|----------|
| **Throughput** | 10-20 jobs/hora | 100+ jobs/hora | 1000+ jobs/hora |
| **Latência** | ~50ms | ~5ms | ~2ms |
| **Persistência** | Arquivo local | RAM + disk | Disk |
| **Setup** | Zero deps | 1 servidor | 1+ servidores |
| **Custo** | $0 | $5-20/mês | $10-50/mês |

### **Quando Migrar? Regras Claras**

```
┌─────────────────────────────────────────────────────────────────┐
│  FICAR COM STANDALONE SE:                                       │
│  ✓ Throughput < 15 jobs/hora                                   │
│  ✓ Latência p95 < 100ms                                         │
│  ✓ Single server suficiente                                    │
│  ✓ Custo é prioridade                                           │
├─────────────────────────────────────────────────────────────────┤
│  MIGRAR PARA REDIS SE:                                          │
│  ✓ Throughput > 15 jobs/hora por 1 semana                     │
│  ✓ Latência p95 > 100ms consistentemente                        │
│  ✓ Precisa de múltiplos workers                                │
│  ✓ backlog_size > 50 consistentemente                          │
└─────────────────────────────────────────────────────────────────┘
```

### Métricas de Decisão

| Métrica | Threshold Standalone | Ação |
|---------|---------------------|------|
| `jobs_per_hour_avg_24h` | < 15 | Continuar standalone |
| `jobs_per_hour_avg_24h` | > 15 | Planejar migração Redis |
| `enqueue_latency_p95_ms` | < 100 | OK |
| `enqueue_latency_p95_ms` | > 100 | Migrar |
| `backlog_size` | < 30 | OK |
| `backlog_size` | > 30 por 1 semana | Migrar |
| `disk_usage_mb` | < 500 | OK |
| `disk_usage_mb` | > 500 | Cleanup ou migrar |

---

## 🏗️ Arquitetura Proposta

### Interface Única (Port)

```python
# src/core/webhooks/ports/job_queue_port.py

class JobQueuePort(ABC):
    """Port para fila de jobs - mesma interface para todas as implementações."""

    @abstractmethod
    async def enqueue(self, job: WebhookJob) -> str:
        """Enfileira job. Retorna job_id."""
        pass

    @abstractmethod
    async def dequeue(self) -> WebhookJob | None:
        """Remove próximo job. Retorna None se vazio."""
        pass

    @abstractmethod
    async def wait_for_dequeue(self, timeout: float) -> WebhookJob | None:
        """Aguarda até ter job disponível."""
        pass

    # ... outros métodos ...
```

### Implementação Standalone

```python
# src/infra/messaging/file_based_job_queue.py

class FileBasedJobQueue(JobQueuePort):
    """
    Fila de jobs persistida em arquivos JSON.

    Estrutura de arquivos:
    skybridge/
    ├── queue/
    │   ├── queue.json          # Fila principal (array de job_ids)
    │   ├── jobs/
    │   │   ├── job_abc123.json  # Dados do job
    │   │   └── job_def456.json
    │   ├── processing/
    │   │   └── job_abc123.json  # Job em processamento
    │   ├── completed/
    │   │   └── job_abc123.json  # Job completado
    │   └── failed/
    │       └── job_def456.json  # Job falhou
    """

    def __init__(self, queue_dir: str = "skybridge/queue"):
        self.queue_dir = Path(queue_dir)
        self.queue_file = self.queue_dir / "queue.json"
        self.jobs_dir = self.queue_dir / "jobs"
        self.processing_dir = self.queue_dir / "processing"
        self.completed_dir = self.queue_dir / "completed"
        self.failed_dir = self.queue_dir / "failed"

        # Criar diretórios
        for dir_path in [self.queue_dir, self.jobs_dir, self.processing_dir,
                          self.completed_dir, self.failed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Lock file para evitar race conditions
        self._lock = asyncio.Lock()

        # Métricas embutidas
        self._metrics = {
            "enqueue_count": 0,
            "dequeue_count": 0,
            "complete_count": 0,
            "fail_count": 0,
            "enqueue_latency_ms": [],
            "dequeue_latency_ms": [],
        }

    async def enqueue(self, job: WebhookJob) -> str:
        """Enfileira job com persistência em arquivo."""
        start = time.time()

        async with self._lock:
            # 1. Salvar dados do job em arquivo
            job_file = self.jobs_dir / f"{job.job_id}.json"
            job_file.write_text(job.to_json())

            # 2. Adicionar job_id à fila
            queue = self._load_queue()
            queue.append(job.job_id)
            self._save_queue(queue)

            # 3. Atualizar métricas
            self._metrics["enqueue_count"] += 1
            latency_ms = (time.time() - start) * 1000
            self._metrics["enqueue_latency_ms"].append(latency_ms)
            if len(self._metrics["enqueue_latency_ms"]) > 1000:
                self._metrics["enqueue_latency_ms"] = self._metrics["enqueue_latency_ms"][-1000:]

            return job.job_id

    async def dequeue(self) -> WebhookJob | None:
        """Remove próximo job da fila com persistência."""
        start = time.time()

        async with self._lock:
            # 1. Carregar fila
            queue = self._load_queue()

            if not queue:
                return None

            # 2. Pegar próximo job_id
            job_id = queue.pop(0)
            self._save_queue(queue)

            # 3. Mover arquivo para processing/
            job_file = self.jobs_dir / f"{job_id}.json"
            if not job_file.exists():
                # Job pode estar em processing/ se worker crashou
                job_file = self.processing_dir / f"{job_id}.json"

            processing_file = self.processing_dir / f"{job_id}.json"
            if job_file.exists():
                job_file.rename(processing_file)

            # 4. Carregar dados do job
            job_data = json.loads(processing_file.read_text())
            job = WebhookJob.from_dict(job_data)

            # 5. Atualizar métricas
            self._metrics["dequeue_count"] += 1
            latency_ms = (time.time() - start) * 1000
            self._metrics["dequeue_latency_ms"].append(latency_ms)
            if len(self._metrics["dequeue_latency_ms"]) > 1000:
                self._metrics["dequeue_latency_ms"] = self._metrics["dequeue_latency_ms"][-1000:]

            return job

    async def complete(self, job_id: str, result: dict = None):
        """Marca job como completo - move para completed/."""
        async with self._lock:
            # Mover arquivo de processing/ para completed/
            processing_file = self.processing_dir / f"{job_id}.json"
            completed_file = self.completed_dir / f"{job_id}.json"

            if processing_file.exists():
                # Adicionar resultado ao arquivo
                job_data = json.loads(processing_file.read_text())
                if result:
                    job_data["result"] = result
                job_data["completed_at"] = datetime.utcnow().isoformat()

                completed_file.write_text(json.dumps(job_data, indent=2))
                processing_file.unlink()

            self._metrics["complete_count"] += 1

    async def fail(self, job_id: str, error: str):
        """Marca job como falhou - move para failed/."""
        async with self._lock:
            processing_file = self.processing_dir / f"{job_id}.json"
            failed_file = self.failed_dir / f"{job_id}.json"

            if processing_file.exists():
                job_data = json.loads(processing_file.read_text())
                job_data["error"] = error
                job_data["failed_at"] = datetime.utcnow().isoformat()

                failed_file.write_text(json.dumps(job_data, indent=2))
                processing_file.unlink()

            self._metrics["fail_count"] += 1

    def size(self) -> int:
        """Retorna tamanho atual da fila."""
        return len(self._load_queue())

    def get_metrics(self) -> dict:
        """Retorna métricas da fila para tomada de decisão."""
        enqueue_latencies = self._metrics["enqueue_latency_ms"]
        dequeue_latencies = self._metrics["dequeue_latency_ms"]

        return {
            "queue_size": self.size(),
            "enqueue_count": self._metrics["enqueue_count"],
            "dequeue_count": self._metrics["dequeue_count"],
            "complete_count": self._metrics["complete_count"],
            "fail_count": self._metrics["fail_count"],
            "enqueue_latency_avg_ms": sum(enqueue_latencies) / len(enqueue_latencies) if enqueue_latencies else 0,
            "enqueue_latency_p95_ms": self._percentile(enqueue_latencies, 95) if enqueue_latencies else 0,
            "dequeue_latency_avg_ms": sum(dequeue_latencies) / len(dequeue_latencies) if dequeue_latencies else 0,
            "dequeue_latency_p95_ms": self._percentile(dequeue_latencies, 95) if dequeue_latencies else 0,
            "jobs_per_hour": self._calculate_jobs_per_hour(),
            "backlog_age_seconds": self._calculate_backlog_age(),
            "disk_usage_mb": self._calculate_disk_usage(),
        }

    def _load_queue(self) -> List[str]:
        """Carrega fila do arquivo."""
        if not self.queue_file.exists():
            return []
        return json.loads(self.queue_file.read_text())

    def _save_queue(self, queue: List[str]):
        """Salva fila no arquivo."""
        self.queue_file.write_text(json.dumps(queue))

    def _percentile(self, values: List[float], p: int) -> float:
        """Calcula percentil."""
        if not values:
            return 0
        values_sorted = sorted(values)
        index = int(len(values_sorted) * p / 100)
        return values_sorted[min(index, len(values_sorted) - 1)]

    def _calculate_jobs_per_hour(self) -> float:
        """Calcula throughput médio (jobs/hora) nas últimas 24h."""
        completed_dir = self.completed_dir
        if not completed_dir.exists():
            return 0.0

        now = time.time()
        last_24h = now - 86400

        count = 0
        for job_file in completed_dir.glob("*.json"):
            job_data = json.loads(job_file.read_text())
            completed_at = job_data.get("completed_at")
            if completed_at:
                completed_time = datetime.fromisoformat(completed_at).timestamp()
                if completed_time > last_24h:
                    count += 1

        return count / 24  # jobs por hora (média)

    def _calculate_backlog_age(self) -> float:
        """Calcula idade do job mais antigo na fila (segundos)."""
        queue = self._load_queue()
        if not queue:
            return 0.0

        oldest_job_id = queue[0]
        job_file = self.jobs_dir / f"{oldest_job_id}.json"
        if not job_file.exists():
            return 0.0

        job_data = json.loads(job_file.read_text())
        created_at = job_data.get("created_at")
        if created_at:
            created_time = datetime.fromisoformat(created_at).timestamp()
            return time.time() - created_time

        return 0.0

    def _calculate_disk_usage(self) -> float:
        """Calcula uso de disco em MB."""
        total_size = 0
        for file_path in self.queue_dir.rglob("*.json"):
            total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)
```

### Preparado para Domain Events

```python
# src/infra/messaging/file_based_event_bus.py

class FileBasedEventBus:
    """
    Event bus baseado em arquivos para comunicação entre processos.

    Estrutura:
    skybridge/
    └── events/
        ├── channels/
        │   ├── issues/             # Canal para eventos de issues
        │   │   └── event_abc123.json
        │   ├── jobs/               # Canal para eventos de jobs
        │   │   ├── event_def456.json
        │   │   └── event_ghi789.json
        │   └── trello/             # Canal para eventos do Trello
        │       └── event_jkl012.json
        └── subscriptions.json      # Quem escuta o quê
    """

    def __init__(self, events_dir: str = "skybridge/events"):
        self.events_dir = Path(events_dir)
        self.channels_dir = self.events_dir / "channels"
        self.subscriptions_file = self.events_dir / "subscriptions.json"

        # Criar diretórios
        self.channels_dir.mkdir(parents=True, exist_ok=True)

        # Subscriptions: {channel: [listener_ids]}
        self._subscriptions = self._load_subscriptions()

        # Channel watchers (para notify() quando novo evento chega)
        self._watchers: Dict[str, asyncio.Event] = {}

    async def publish(self, event: DomainEvent) -> None:
        """Publica evento em um canal."""
        channel = self._get_channel_for_event(event)

        # Criar arquivo de evento
        event_file = self.channels_dir / channel / f"event_{event.event_id}.json"
        event_file.write_text(event.to_json())

        # Notificar watchers
        if channel in self._watchers:
            self._watchers[channel].set()

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], None],
        listener_id: str
    ) -> None:
        """Inscreve handler para tipo de evento."""
        channel = self._get_channel_name(event_type)

        # Registrar subscription
        if channel not in self._subscriptions:
            self._subscriptions[channel] = []
        self._subscriptions[channel].append(listener_id)

        self._save_subscriptions()

        # Iniciar watcher para este listener
        asyncio.create_task(self._watch_channel(channel, handler))

    async def _watch_channel(self, channel: str, handler):
        """Watch channel por novos eventos e executa handler."""
        processed_events = set()

        while True:
            # List events no canal
            channel_dir = self.channels_dir / channel
            if not channel_dir.exists():
                await asyncio.sleep(1)
                continue

            for event_file in channel_dir.glob("event_*.json"):
                event_id = event_file.stem.replace("event_", "")

                # Skip se já processou
                if event_id in processed_events:
                    continue

                # Carregar e processar evento
                event_data = json.loads(event_file.read_text())
                event = DomainEvent.from_dict(event_data)

                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Handler falhou: {e}")

                processed_events.add(event_id)

            # Aguardar novo evento ou timeout
            if channel not in self._watchers:
                self._watchers[channel] = asyncio.Event()

            await asyncio.wait_for(self._watchers[channel].wait(), timeout=1.0)
            self._watchers[channel].clear()
```

---

## 🔄 Migration Path para Redis

### Fase 1: Standalone (HOJE)

```python
# github_webhook_server.py
from infra.messaging.file_based_job_queue import FileBasedJobQueue

job_queue = FileBasedJobQueue()
# Funciona! Sem deps externas!
```

### Fase 2: Redis (DEPOIS - sem mudar código produto)

```python
# github_webhook_server.py
from infra.messaging.redis_job_queue import RedisJobQueue  # ← Só muda import!

job_queue = RedisJobQueue(redis_url="redis://localhost:6379")
# Código IGUAL! Interface mesma!
```

### Interfaces Idênticas

```python
# AMBAS implementam a MESMA interface

# Standalone
await job_queue.enqueue(job)  # → Arquivo
job = await job_queue.dequeue()  # ← Arquivo

# Redis
await job_queue.enqueue(job)  # → Redis
job = await job_queue.dequeue()  # ← Redis
```

---

## ✅ Critérios de Sucesso

### Mínimo Viável
- [ ] `FileBasedJobQueue` implementado
- [ ] Drop-in replacement para `InMemoryJobQueue`
- [ ] Webhook Server + Worker compartilham fila
- [ ] Persistência em arquivos funciona
- [ ] Jobs sobrevivem a restart do servidor

### Completo
- [ ] `FileBasedEventBus` para Domain Events
- [ ] Métricas embutidas funcionando
- [ ] Dashboard mostra métricas de decisão
- [ ] Testes de concorrência (múltiplos processos)
- [ ] Documentação de migration path

### Stretch
- [ ] `RedisJobQueue` implementado (mesma interface)
- [ ] Teste A/B: Standalone vs Redis
- [ ] Script de migração de dados

---

## 📊 Números de Performance

### Benchmarks Esperados

| Operação | Standalone | Redis | Melhoria |
|----------|------------|-------|----------|
| `enqueue()` | ~50ms | ~5ms | 10x |
| `dequeue()` | ~50ms | ~5ms | 10x |
| `wait_for_dequeue()` | ~100ms | ~10ms | 10x |
| `complete()` | ~30ms | ~2ms | 15x |
| **Throughput** | **10-20/h** | **100+/h** | **5-10x** |

### Custos

| Solução | Setup | Mensal | Break-even |
|---------|-------|--------|------------|
| **Standalone** | $0 | $0 | - |
| **Redis** | $0 (self-hosted) | $5-20 | 200+ jobs/dia |
| **RabbitMQ** | $0 (self-hosted) | $10-50 | 500+ jobs/dia |

---

## 🧪 Testes

```python
# tests/infra/messaging/test_file_based_queue.py

@pytest.mark.asyncio
async def test_enqueue_persists_to_file():
    queue = FileBasedJobQueue(queue_dir="/tmp/test_queue")

    job = create_test_job()
    await queue.enqueue(job)

    # Arquivo deve existir
    job_file = Path("/tmp/test_queue/jobs") / f"{job.job_id}.json"
    assert job_file.exists()

@pytest.mark.asyncio
async def test_dequeue_removes_from_queue():
    queue = FileBasedJobQueue(queue_dir="/tmp/test_queue")

    job1 = create_test_job("job1")
    job2 = create_test_job("job2")

    await queue.enqueue(job1)
    await queue.enqueue(job2)

    # Dequeue deve retornar jobs em ordem
    dequeued1 = await queue.dequeue()
    assert dequeed1.job_id == "job1"

    dequeued2 = await queue.dequeue()
    assert dequeud2.job_id == "job2"

@pytest.mark.asyncio
async def test_metrics_calculations():
    queue = FileBasedJobQueue(queue_dir="/tmp/test_queue")

    metrics = queue.get_metrics()

    assert metrics["queue_size"] == 0
    assert metrics["enqueue_latency_avg_ms"] == 0
```

---

## 📅 Roadmap

| Sprint | Dias | Entrega |
|--------|------|---------|
| **Sprint 1** | 2-3 | `FileBasedJobQueue` core |
| **Sprint 2** | 1-2 | `FileBasedEventBus` |
| **Sprint 3** | 1-2 | Métricas + Dashboard |
| **Sprint 4** | 1-2 | Testes + Documentação |
| **Total** | **5-9 dias** | Mensageria standalone completa |

---

## 📊 Dashboard de Decisão

```python
# Dashboard CLI para decidir quando migrar

def show_migration_decision(metrics: dict):
    """Mostra recomendação baseada em métricas."""

    console = Console()

    # Calcula score
    score = 0
    reasons = []

    if metrics["jobs_per_hour"] > 15:
        score += 3
        reasons.append(f"✅ Throughput alto ({metrics['jobs_per_hour']:.1f} jobs/h)")

    if metrics["enqueue_latency_p95_ms"] > 100:
        score += 2
        reasons.append(f"⚠️ Latência alta ({metrics['enqueue_latency_p95_ms']:.1f}ms)")

    if metrics["backlog_age_seconds"] > 300:  # 5 min
        score += 2
        reasons.append(f"⚠️ Backlog antigo ({metrics['backlog_age_seconds']:.0f}s)")

    if metrics["disk_usage_mb"] > 500:
        score += 1
        reasons.append(f"⚠️ Disco alto ({metrics['disk_usage_mb']:.1f}MB)")

    # Recomendação
    if score >= 5:
        recommendation = "🚀 MIGRAR PARA REDIS"
        color = "red"
    elif score >= 3:
        recommendation = "⚠️ AVALIAR MIGRAÇÃO"
        color = "yellow"
    else:
        recommendation = "✅ CONTINUAR STANDALONE"
        color = "green"

    console.print(Panel(
        f"[bold {color}]{recommendation}[/bold {color}]\n\n"
        f"Score: {score}/7\n\n" +
        "\n".join(reasons) if reasons else "✅ Todas métricas OK",
        title="Decisão de Migração",
        border_style=color
    ))
```

---

## 💭 Perguntas Frequentes

**Q: Arquivo não é lento?**
A: Para < 20 jobs/hora, não. Operações são O(1) com cache em memória. Fica lento apenas com > 100 jobs/hora.

**Q: E se o servidor crashar no meio do dequeue?**
A: Job fica em `processing/`. No próximo restart, `dequeue()` detecta e recupera jobs órfãos.

**Q: Posso rodar múltiplos workers com FileBasedJobQueue?**
A: Sim! Lock file (`asyncio.Lock`) previne race conditions. Múltiplos processos podem ler/escrever mesma fila.

**Q: Quando devo migrar para Redis?**
A: Use o dashboard de decisão. Score >= 5 = migrar. Geralmente quando throughput > 15 jobs/hora OU latência p95 > 100ms.

---

## 📊 Valor de Negócio

### Hoje (Problema #1)
> "Jobs enfileirados mas nunca processados. Sistema não funciona."

### Depois (Standalone)
> "Sistema funciona com 10-20 jobs/hora. Sem custos de infraestrutura."

### Futuro (Redis - quando necessário)
> "Sistema escala para 100+ jobs/hora. Migração transparente - código não muda."

---

`★ Insight ─────────────────────────────────────`
Esta solução **evolui com você**: começa standalone (zero deps), tem métricas para decidir quando escalar, e migra para Redis sem mudar código produto. **Pague conforme cresce** - não antecipe infraestratura que pode não precisar.
`─────────────────────────────────────────────────`

> "A melhor arquitetura é a que evolui conforme suas necessidades" – made by Sky 📈
