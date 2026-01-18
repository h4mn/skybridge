# PRD015: Observabilidade e Métricas para Skybridge

**Status:** 📋 Proposta
**Data:** 2026-01-17
**Autor:** Sky
**Versão:** 1.0
**Relacionado:** Problema #5 (ANALISE_PROBLEMAS_ATUAIS.md)

---

## 📋 Resumo Executivo

Implementar sistema de **métricas e observabilidade** para permitir tomada de decisões baseada em dados, identificar gargalos de performance e justificar investimentos em infraestrutura.

### Problema
Atualmente o Skybridge **não coleta métricas agregadas**, tornando impossível responder perguntas críticas como:
- Quantos jobs por hora estamos processando?
- Qual é o tempo médio de execução dos agentes?
- Qual taxa de erro?
- Quando precisamos escalar horizontalmente?
- Quanto estamos gastando com a API do Claude?

### Solução
Implementar sistema de métricas em camadas:
1. **Camada 1:** Logs estruturados (✅ já existe)
2. **Camada 2:** Métricas agregadas (🔨 a implementar)
3. **Camada 3:** Dashboards e alertas (📅 Fase 2)
4. **Camada 4:** Rastreamento distribuído (✅ correlation_id já existe)

---

## 🎯 Objetivos

### Primários
- [ ] Coletar métricas de **throughput** (jobs/hora)
- [ ] Medir **latência** de cada fase (webhook → agent → Trello)
- [ ] Calcular **taxa de erro** por tipo de job
- [ ] Monitorar **recursos** (memória, CPU, fila)
- [ ] Rastrear **custos** da API Claude

### Secundários
- [ ] Dashboard CLI para visualização em tempo real
- [ ] Endpoint `/metrics` para integração com Prometheus
- [ ] Alertas automáticos para SLO violations
- [ ] Relatórios diários de performance

### Não-Objetivos
- ❌ Substituir logs existentes (logs continuam como está)
- ❌ Implementar tracing distribuído completo (OpenTelemetry = Fase 3)
- ❌ Dashboard web complexo (Grafana = futuro, usar CLI primeiro)

---

## 📊 Métricas Propostas

### 1. Métricas de Negócio (Business Metrics)

| Nome | Tipo | Descrição | Pergunta que Responde |
|------|------|-----------|----------------------|
| `jobs_total` | Counter | Total de jobs processados | "Quantos jobs processamos desde o início?" |
| `jobs_success` | Counter | Jobs completados com sucesso | "Quantos deram certo?" |
| `jobs_failed` | Counter | Jobs que falharam | "Quantos falharam?" |
| `jobs_by_skill{skill}` | Counter | Jobs por tipo (resolve-issue, bug-simple, etc) | "Que tipo de issues chegam?" |
| `jobs_by_source{source}` | Counter | Jobs por origem (github, discord, etc) | "De onde vêm os webhooks?" |
| `queue_size` | Gauge | Tamanho atual da fila | "Qual o backlog?" |

### 2. Métricas de Performance (Latency)

| Nome | Tipo | Unidade | Percentis |
|------|------|---------|-----------|
| `job_duration_seconds` | Histogram | segundos | p50, p95, p99 |
| `agent_duration_seconds` | Histogram | segundos | p50, p95, p99 |
| `webhook_to_queue_latency` | Histogram | segundos | p50, p95, p99 |
| `queue_to_agent_latency` | Histogram | segundos | p50, p95, p99 |
| `trello_api_duration_seconds` | Histogram | segundos | p50, p95, p99 |

### 3. Métricas de Recursos (System)

| Nome | Tipo | Unidade | Alerta |
|------|------|---------|--------|
| `worker_memory_bytes` | Gauge | bytes | > 2GB |
| `worker_cpu_percent` | Gauge | % | > 80% |
| `active_agents` | Gauge | count | > N (configurável) |
| `worktree_count` | Gauge | count | > 100 |

### 4. Métricas de Custos (Cost)

| Nome | Tipo | Unidade | Derivada de |
|------|------|---------|------------|
| `claude_api_tokens_total` | Counter | tokens | Agent execution |
| `claude_api_cost_usd` | Gauge | USD | tokens × preço |
| `jobs_per_dollar` | Gauge | jobs/USD | jobs / cost |

---

## 🏗️ Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│  Camada de Coleta (Instrumentation)                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ @measure_time decorator                                    │  │
│  │ metrics_store.increment("jobs_success")                   │  │
│  │ metrics_store.record_histogram("duration", value)         │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Camada de Armazenamento (Storage)                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ InMemoryMetricsStore                                      │  │
│  │   - counters: Dict[str, float]                           │  │
│  │   - gauges: Dict[str, float]                             │  │
│  │   - histograms: Dict[str, List[MetricPoint]]             │  │
│  └───────────────────────────────────────────────────────────┘  │
│  FUTURO: Prometheus / StatsD / Redis                           │
├─────────────────────────────────────────────────────────────────┤
│  Camada de Visualização (Visualization)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ CLI Dashboard (rich)                                      │  │
│  │ HTTP Endpoint (/metrics)                                  │  │
│  │ FUTURO: Grafana                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Camada de Alertas (Alerting)                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ AlertChecker                                               │  │
│  │   - queue_size > 50 → CRÍTICO                             │  │
│  │   - error_rate > 10% → AVISO                              │  │
│  │   - p99_duration > 15min → AVISO                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementação

### Fase 1: Core (2-3 dias)

#### 1.1 InMemoryMetricsStore

```python
# src/runtime/observability/metrics.py

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
import threading

@dataclass
class MetricPoint:
    timestamp: datetime
    value: float
    tags: Dict[str, str]

class InMemoryMetricsStore:
    """Armazenamento em memória de métricas."""

    def __init__(self):
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._lock = threading.Lock()

    def increment(self, name: str, value: float = 1.0, tags: Dict = None):
        """Incrementa contador."""
        key = self._make_key(name, tags)
        with self._lock:
            self._counters[key] += value

    def set_gauge(self, name: str, value: float, tags: Dict = None):
        """Define gauge."""
        key = self._make_key(name, tags)
        with self._lock:
            self._gauges[key] = value

    def record_histogram(self, name: str, value: float, tags: Dict = None):
        """Registra valor no histograma."""
        key = self._make_key(name, tags)
        with self._lock:
            self._histograms[key].append(MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                tags=tags or {}
            ))
            # Mantém últimos 1000 pontos
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]

    def get_summary(self) -> Dict:
        """Retorna resumo agregado."""
        # ... implementa cálculo de avg, min, max, percentis
```

#### 1.2 Decorator @measure_time

```python
def measure_time(metric_name: str, tags: Dict = None):
    """Decorator para medir tempo de execução."""
    def decorator(func):
        async def wrapped(*args, **kwargs):
            start = datetime.utcnow()
            try:
                result = await func(*args, **kwargs)
                get_metrics_store().increment(f"{metric_name}_success", tags=tags)
                return result
            except Exception:
                get_metrics_store().increment(f"{metric_name}_failed", tags=tags)
                raise
            finally:
                duration = (datetime.utcnow() - start).total_seconds()
                get_metrics_store().record_histogram(
                    f"{metric_name}_duration_seconds",
                    duration,
                    tags=tags
                )
        return wrapped
    return decorator
```

#### 1.3 Integração no Worker

```python
# src/runtime/background/webhook_worker.py

from runtime.observability.metrics import get_metrics_store, measure_time

class WebhookWorker:
    async def start(self):
        while self._running:
            # Registra tamanho da fila
            get_metrics_store().set_gauge("queue_size", self.job_queue.size())

            job = await self.job_queue.wait_for_dequeue(timeout=1.0)

            if job:
                result = await self._execute_job_with_metrics(job)

                # Atualiza gauge após processamento
                get_metrics_store().set_gauge("queue_size", self.job_queue.size())

    @measure_time("job_execution")
    async def _execute_job_with_metrics(self, job):
        tags = {
            "skill": self._get_skill_from_job(job),
            "source": job.event.source.value
        }

        result = await self.orchestrator.execute_job(job.job_id)

        if result.is_ok:
            get_metrics_store().increment("jobs_success", tags=tags)
        else:
            get_metrics_store().increment("jobs_failed", tags=tags)

        return result
```

### Fase 2: Visualização (2-3 dias)

#### 2.1 Endpoint /metrics

```python
# src/runtime/delivery/routes.py

@app.get("/metrics")
async def get_metrics():
    """Retorna métricas em formato Prometheus."""
    metrics = get_metrics_store().get_summary()

    lines = []

    # Contadores
    for name, value in metrics["counters"].items():
        lines.append(f"# HELP {name} Total count")
        lines.append(f"# TYPE {name} counter")
        lines.append(f"{name} {value}")

    # Gauges
    for name, value in metrics["gauges"].items():
        lines.append(f"# HELP {name} Current value")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")

    # Histogramas (Prometheus format)
    for name, stats in metrics["histograms"].items():
        lines.append(f"# HELP {name} Duration in seconds")
        lines.append(f"# TYPE {name} histogram")
        lines.append(f"{name}_count {stats['count']}")
        lines.append(f"{name}_sum {stats['avg'] * stats['count']}")
        # _bucket com percentis

    return Response(content="\n".join(lines), media_type="text/plain")
```

#### 2.2 Dashboard CLI

```python
# src/runtime/observability/dashboard.py

from rich.console import Console
from rich.table import Table

def show_metrics_dashboard():
    """Mostra dashboard no terminal."""
    console = Console()
    metrics = get_metrics_store().get_summary()

    # Tabela de contadores
    counters = Table(title="📊 Contadores")
    counters.add_column("Métrica")
    counters.add_column("Valor")

    for name, value in sorted(metrics["counters"].items()):
        counters.add_row(name, f"{value:,.0f}")

    # Tabela de latência
    latency = Table(title="⏱️ Latência (segundos)")
    latency.add_column("Métrica")
    latency.add_column("Avg")
    latency.add_column("P95")
    latency.add_column("P99")

    for name, stats in metrics["histograms"].items():
        if "duration" in name:
            latency.add_row(
                name,
                f"{stats['avg']:.1f}",
                f"{stats['p95']:.1f}",
                f"{stats['p99']:.1f}"
            )

    console.print(counters)
    console.print(latency)
```

### Fase 3: Alertas (1-2 dias)

```python
# src/runtime/observability/alerts.py

class AlertChecker:
    THRESHOLDS = {
        "queue_size_critical": 50,
        "queue_size_warning": 20,
        "job_duration_p99": 900,
        "error_rate_percent": 10,
    }

    def check_alerts(self) -> List[str]:
        """Verifica condições de alerta."""
        metrics = get_metrics_store().get_summary()
        alerts = []

        queue_size = metrics["gauges"].get("queue_size", 0)
        if queue_size > self.THRESHOLDS["queue_size_critical"]:
            alerts.append(f"🚨 CRÍTICO: Fila com {queue_size} jobs")

        # ... mais verificações

        return alerts
```

---

## ✅ Critérios de Sucesso

### Mínimo Viável (MVP)
- [ ] `InMemoryMetricsStore` implementado
- [ ] Decorator `@measure_time` funcionando
- [ ] Worker coletando métricas de jobs
- [ ] Endpoint `/metrics` retornando dados
- [ ] Dashboard CLI mostrando contadores e latência

### Completo
- [ ] Todas as métricas propostas coletadas
- [ ] Histogramas calculando percentis (p50, p95, p99)
- [ ] Alert checker funcionando
- [ ] Testes cobrindo camada de métricas
- [ ] Documentação de como adicionar novas métricas

### Stretch (Futuro)
- [ ] Integração com Prometheus
- [ ] Dashboard Grafana
- [ ] Alertas via PagerDuty/Slack
- [] Tracing distribuído com OpenTelemetry

---

## 🧪 Testes

```python
# tests/runtime/test_metrics.py

def test_counter_increment():
    store = InMemoryMetricsStore()
    store.increment("jobs_total")
    store.increment("jobs_total", value=5)

    summary = store.get_summary()
    assert summary["counters"]["jobs_total"] == 6

def test_histogram_percentiles():
    store = InMemoryMetricsStore()

    # Registra 100 medições
    for i in range(100):
        store.record_histogram("test", i)

    summary = store.get_summary()
    stats = summary["histograms"]["test"]

    assert stats["count"] == 100
    assert stats["min"] == 0
    assert stats["max"] == 99
    assert 45 <= stats["avg"] <= 55  # ~50

@pytest.mark.asyncio
async def test_measure_time_decorator():
    store = InMemoryMetricsStore()

    @measure_time("test_operation")
    async def operation():
        await asyncio.sleep(0.1)
        return "ok"

    result = await operation()

    summary = store.get_summary()
    assert "test_operation_success" in summary["counters"]
    assert "test_operation_duration_seconds" in summary["histograms"]
```

---

## 📅 Roadmap

| Sprint | Dias | Entrega |
|--------|------|---------|
| **Sprint 1** | 2-3 | InMemoryMetricsStore + decorator + integração worker |
| **Sprint 2** | 2-3 | Endpoint /metrics + dashboard CLI |
| **Sprint 3** | 1-2 | Alert checker + testes |
| **Total** | **5-8 dias** | Sistema de métricas completo |

---

## 🔄 Relacionamento com Outros PRDs

| PRD | Relação | Descrição |
|-----|---------|-----------|
| **PRD013** | Depende | Agentes (PRD013) serão instrumentados com métricas |
| **PRD016** | Independente | Domain Events (PRD016) futuramente também terão métricas |
| **PRD014** | Complementa | WebUI Dashboard pode consumir /metrics |

---

## 💭 Perguntas Frequentes

**Q: Por que não Prometheus desde o início?**
A: `InMemoryMetricsStore` é suficiente para MVP e simplifica setup. Prometheus pode ser adicionado depois sem mudar código de instrumentação.

**Q: Métricas vão degradar performance?**
A: Impacto mínimo (< 1%). Operações são O(1) com lock threading. Memória: ~1-2MB para 1000 pontos de histograma.

**Q: Como calcular percentis?**
A: Para MVP: ordenar valores e pegar índice. Para produção: usar t-digest ou Prometheus.

**Q: O que acontece quando reinicia o servidor?**
A: Métricas em memória são perdidas. Para persistência, adicionar Prometheus push gateway ou Redis.

---

## 📊 Valor de Negócio

### Antes
> "Acho que estamos processando uns 10 jobs por hora... não sei ao certo."

### Depois
> "Processamos **47 jobs/hora** nas últimas 24h, com **p95 de 8.3min** por job. Taxa de erro de **2.1%**. Precisamos escalar quando fila > 20."

**Benefícios:**
- ✅ Decisões baseadas em dados
- ✅ Detecção precoce de regressões
- ✅ Justificativa clara para investimentos
- ✅ SLA definido e monitorado

---

> "O que não é medido não pode ser melhorado" – made by Sky 📊
