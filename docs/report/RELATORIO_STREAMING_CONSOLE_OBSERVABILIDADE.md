# Relatório: Streaming de Console e Observabilidade em Produção

**Data:** 25 de Janeiro de 2026
**Autor:** Sky
**Versão:** 1.0
**Repositório:** skybridge

---

## Índice

1. [Análise de Logging: Rich, Loguru e Structlog](#1-análise-de-logging)
2. [Serviços de Observabilidade](#2-serviços-de-observabilidade)
3. [Comparativo: IPC vs WebSocket](#3-comparativo-ipc-vs-websocket)
4. [Análise da Implementação Skybridge](#4-análise-da-implementação-skybridge)
5. [Recomendações e Roadmap](#5-recomendações-e-roadmap)

---

## 1. Análise de Logging

### 1.1 Rich Console Output

O [Rich](https://rich.readthedocs.io/) é uma biblioteca Python (47k+ estrelas) para renderização avançada de terminal com suporte a:

- Cores ANSI e RGB
- Tabelas e barras de progresso
- Syntax highlighting
- Markdown renderizado
- Tracebacks bonitas
- Emoji suporte nativo

#### 🎨 O Problema das Cores no Trello

**A má notícia:** O Trello **NÃO suporta cores ANSI ou HTML** em card descriptions.

Suporte oficial do Trello:
- ✅ Markdown básico (`**bold**`, `*italic*`, `` `code` ``, `## headers`)
- ✅ Code blocks com \`\`\`
- ✅ Listas, links, checkboxes
- ❌ **Cores ANSI** (sequências de escape)
- ❌ **HTML customizado** (tags como `<span>`, `<div>`)
- ❌ **CSS inline**

> Fonte: [Trello Formatting Guide](https://support.atlassian.com/trello/docs/how-to-format-your-text-in-trello/)

#### ✅ Solução: Converter ANSI para Markdown

Para usar Rich com Trello, precisamos de uma camada de adaptação:

```python
from rich.console import Console
from rich.text import Text
import re

def ansi_to_markdown(ansi_text: str) -> str:
    """
    Converte texto com códigos ANSI para Markdown compatível com Trello.

    Mapeamento:
    - Vermelho/Amarelo → ```text ... ``` (code block)
    - Verde → ✅ (emoji)
    - Bold → **texto**
    - Italic → *texto*
    """
    # Remove sequências ANSI não mapeáveis
    clean = re.sub(r'\x1b\[[0-9;]*m', '', ansi_text)

    # Detecta palavras-chave de erro para destacar
    if any(word in clean.lower() for word in ['error', 'failed', 'exception']):
        return f"```\n⚠️  {clean}\n```"

    if any(word in clean.lower() for word in ['success', 'completed', 'done']):
        return f"✅ {clean}"

    return clean

# Uso com Rich
console = Console()
with console.capture() as capture:
    console.print("[bold red]ERROR:[/bold red] Falha na conexão", style="red")

ans_output = capture.get()
markdown_for_trello = ansi_to_markdown(ans_output)
# Resultado no Trello: ```⚠️  ERROR: Falha na conexão```
```

#### 📊 Tabela de Conversão Rich → Trello

| Rich Output | Trello Markdown | Exemplo |
|-------------|-----------------|---------|
| `[bold red]ERROR[/bold red]` | ```⚠️ ERROR``` | Code block com emoji |
| `[green]SUCCESS[/green]` | ✅ SUCCESS | Emoji verde |
| `[yellow]WARN[/yellow]` | ```⚡ WARN``` | Code block |
| `[blue]INFO[/blue]` | ℹ️ INFO | Emoji azul |
| `Table(...)` | Markdown table | Conversão manual |
| `Progress(...)` | N/A | Não aplicável |

`★ Insight ─────────────────────────────────────`
O brilho do Rich no terminal local é inegável, mas para integrações como Trello, precisamos de um **adaptador ANSI→Markdown**. A alternativa elegante: usar Rich para console local E gerar Markdown limpo para Trello simultaneamente - o melhor dos dois mundos.
`─────────────────────────────────────────────────`

---

### 1.2 Loguru vs Structlog: Qual Escolher?

#### Loguru: "Logging Made Stupidly Simple" (19k+ ⭐)

**Por que TANTAS estrelas?**

1. **Zero Boilerplate** - 90% menos código que logging padrão
2. **Feature Completa** - Tudo que você precisa embutido
3. **Developer Experience (DX)** - API intuitiva e Pythonica
4. **Beautiful Defaults** - Output formatado sem configuração

```python
# Loguru: Uso básico (TÃO simples!)
from loguru import logger

logger.info("Usuário logou", user="alice", action="login")
# Saída: 2025-01-25 10:30:00 | INFO     | __main__:12 - Usuário logou user='alice' action='login'

logger.error("Erro crítico!")
# Saída: 2025-01-25 10:30:01 | ERROR    | __main__:13 - Erro crítico!
# + traceback automática bonita

# Rotation automática (UMA linha!)
logger.add("app.log", rotation="10 MB", retention="7 days")
```

**O que o Loguru resolve MELHOR:**

| Problema | Loguru Solução | Standard Logging |
|----------|----------------|------------------|
| Boilerplate | Nenhum import/config | Múltiplos imports, handlers, formatters |
| Rotation | `rotation="10 MB"` | Custom RotatingFileHandler |
| Exception trace | `logger.exception()` | `logger.error(exc_info=True)` + setup |
| Correlação | `logger.bind(ctx=value)` | Custom Filter/Adapter |
| Formatação | `"<g>{time}</g> | <level>{level}</level>"` | Formatter strings verbosas |
| Capture output | `logger.add(sys.stderr)` | Multiple handler configs |

#### Structlog: "Structured Logging for Production" (4k+ ⭐)

**Menos estrelas, mas mais especializado.**

```python
# Structlog: Foco em estrutura processável
import structlog

log = structlog.get_logger()
log.info("user_login", user_id=123, ip="192.168.1.1")
# Saída JSON: {"event": "user_login", "user_id": 123, "ip": "192.168.1.1", "timestamp": "..."}

# Processors para customização avançada
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
```

#### 📊 Comparativo Direto

| Aspecto | Loguru | Structlog | Veredito |
|---------|--------|-----------|----------|
| **Curva de aprendizado** | Plana | Íngreme | Loguru |
| **Setup inicial** | 0 configs | Requer configure() | Loguru |
| **JSON output** | Via serialize | Nativo | Structlog |
| **Context binding** | `.bind(key=val)` | `.bind(key=val)` | Empate |
| **Exception handling** | Excepcional | Bom | Loguru |
| **Distribuição** | 19k+ ⭐ | 4k+ ⭐ | Loguru |
| **Correlação de logs** | Boa | Excelente | Structlog |
| **Performance** | Excelente | Superior | Structlog |
| **Uso em produção** | Comum | Enterprise | Structlog |
| **Integração OpenTelemetry** | Manual | Nativa | Structlog |

#### 🎯 Quando usar cada um?

**Use Loguru se:**
- Você quer começar a logar AGORA sem configuração
- Cuida de um projeto pequeno/médio
- Beauty no console é importante
- Você não precisa de logs estruturados JSON

**Use Structlog se:**
- Você precisa de logs estruturados JSON
- Integração com sistemas de agregação (ELK, Loki, Datadog)
- Distribuição de tracing em microservices
- Processamento complexo de logs
- Performance crítica em alto volume

**Use AMBOS (Padrão Híbrido):**
```python
# O melhor dos dois mundos
from loguru import logger
import structlog

# Loguru para desenvolvimento local
logger.add("dev.log", level="DEBUG")

# Structlog para produção JSON
structlog.configure(processors=[structlog.processors.JSONRenderer()])
prod_log = structlog.get_logger()

# Mesma aplicação, dual output
```

`★ Insight ─────────────────────────────────────`
A popularidade do Loguru vem da **filosofia "baterias inclusas"** - ele funciona lindamente out-of-the-box. O Structlog tradeia simplicidade por flexibilidade. Para a Skybridge, recomendo: **Loguru para dev local + Structlog/JSON para produção**. Assim você tem DX e observabilidade.
`─────────────────────────────────────────────────`

---

## 2. Serviços de Observabilidade

### 2.1 OpenTelemetry

**O que é:** Padrão *de facto* para telemetria distribuída (traces, metrics, logs).

**Por que usar:**
- Vendor-agnostic (não te prende a Datadog, New Relic, etc.)
- Padrão CNCF (Cloud Native Computing Foundation)
- Correlação automática de traces ↔️ metrics ↔️ logs

#### Integração com FastAPI

```python
# requirements.txt
# opentelemetry-api
# opentelemetry-sdk
# opentelemetry-instrumentation-fastapi
# opentelemetry-instrumentation-logging
# opentelemetry-exporter-otlp

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Configuração
app = FastAPI()

provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Instrumentação automática
FastAPIInstrumentor.instrument_app(app)

# Logs correlacionados com trace ID
import structlog
structlog.configure(
    processors=[
        structlog.processors.OpenTelemetryProcessor(),
        structlog.dev.ConsoleRenderer()
    ]
)
```

**Benefícios para Skybridge:**
- Tracear requisição → webhook → agente → resposta
- Identificar gargalos de performance
- Correlacionar erros com contexto completo

---

### 2.2 Prometheus

**O que é:** Sistema de métricas time-series com linguagem de query (PromQL).

**Métricas essenciais para Skybridge:**

| Métrica | Tipo | Descrição |
|---------|------|-----------|
| `skybridge_jobs_total` | Counter | Total de jobs processados |
| `skybridge_jobs_duration_seconds` | Histogram | Duração dos jobs |
| `skybridge_webhooks_received_total` | Counter | Webhooks recebidos por tipo |
| `skybridge_agent_errors_total` | Counter | Erros de agente por tipo |
| `skybridge_websocket_connections` | Gauge | Conexões WebSocket ativas |
| `skybridge_queue_size` | Gauge | Tamanho da fila de jobs |

#### Integração com FastAPI

```python
# requirements.txt
# prometheus-fastapi-instrumentator
# prometheus-client

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

# Instrumentação automática
app = FastAPI()
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Métricas customizadas
jobs_counter = Counter(
    "skybridge_jobs_total",
    "Total de jobs processados",
    ["job_type", "status"]
)

jobs_duration = Histogram(
    "skybridge_jobs_duration_seconds",
    "Duração dos jobs",
    ["job_type"]
)

ws_connections = Gauge(
    "skybridge_websocket_connections",
    "Conexões WebSocket ativas",
    ["job_id"]
)

# Uso nos endpoints
@app.post("/webhooks/trello")
async def trello_webhook(payload: dict):
    jobs_counter.labels(job_type="trello", status="started").inc()
    with jobs_duration.labels(job_type="trello").time():
        # Processa webhook...
        jobs_counter.labels(job_type="trello", status="completed").inc()
```

---

### 2.3 Sentry

**O que é:** Error tracking com contexto rico, stack traces agrupados, performance monitoring.

**Por que usar:**
- Alertas em tempo real de erros
- Breadcrumbs (eventos que levaram ao erro)
- Release tracking (erros por versão)
- Performance monitoring gratuito incluído

#### Integração com FastAPI

```python
# requirements.txt
# sentry-sdk[fastapi]

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn="https://your-dsn@sentry.io/project-id",
    integrations=[
        FastApiIntegration(),
        RedisIntegration(),
        SqlalchemyIntegration()
    ],
    traces_sample_rate=0.1,  # 10% das requisições traceadas
    environment="production",
    release=f"skybridge@{VERSION}",
    before_send_transaction=before_transaction,
    before_send=before_error,
)

# Enriquecimento de contexto
@app.post("/agents/{agent_id}/run")
async def run_agent(agent_id: str, input_data: dict):
    # Contexto customizado
    sentry_sdk.set_context("agent", {
        "agent_id": agent_id,
        "model": "claude-3-5-sonnet",
        "autonomy_level": "high"
    })

    try:
        result = await execute_agent(agent_id, input_data)
        return result
    except Exception as e:
        # Captura contexto do erro
        sentry_sdk.capture_exception(e)
        raise
```

**Benefícios para Skybridge:**
- Rastrear exceções de agentes em produção
- Identificar padrões de erro (por modelo, por tipo de tarefa)
- Performance monitoring de endpoints críticos
- Slack/Email alerts para erros críticos

---

## 3. Comparativo: IPC vs WebSocket

### 3.1 Auto-Claude: Socket IPC

**Arquitetura:**
```
┌─────────────────────────────────────────────────────┐
│               Electron (Processo Main)              │
│  ┌──────────────┐         ┌──────────────────────┐ │
│  │   Renderer   │   IPC   │   PTY Daemon Client  │ │
│  │   (UI)       │ ←────→  │   (Socket IPC)       │ │
│  └──────────────┘         └──────────────────────┘ │
└─────────────────────────────────────────────────────┘
                                    │
                                    │ Socket IPC / Named Pipe
                                    ▼
┌─────────────────────────────────────────────────────┐
│            PTY Daemon (Processo Detached)           │
│   • Unix Socket (Linux/Mac)                          │
│   • Named Pipe (Windows)                            │
│   • JSON delimitado por \n                          │
│   • Ring buffer (100KB, 1000 chunks)                │
└─────────────────────────────────────────────────────┘
```

**Características:**
- **Protocolo:** Socket IPC (Unix socket ou Named Pipe)
- **Persistência:** Processo detached sobrevive a restarts
- **Buffering:** Ring buffer com tamanho fixo
- **Comunicação:** JSON delimitado por newlines
- **Escalabilidade:** Múltiplos PTYs simultâneos

**O que ganha:**
| ✅ Vantagem | Descrição |
|-------------|-----------|
| **Isolamento** | Crash no frontend não mata o PTY daemon |
| **Baixa latência** | IPC local é mais rápido que rede |
| **Persistência** | Sessão de terminal sobrevive a restarts |
| **Zero overhead de rede** | Sem TCP/IP stack |
| **Multiplexação** | Múltiplos terminais em um daemon |

**O que perde:**
| ❌ Desvantagem | Descrição |
|----------------|-----------|
| **Local-only** | Impossível acesso remoto |
| **Plataforma-specific** | Named Pipe Windows ≠ Unix Socket |
| **Complexidade** | Gerenciamento de processos detached |
| **Debugging difícil** | Processos separados são duros de debugar |
| **Não distribuído** | Impossível escalar horizontalmente |

---

### 3.2 Skybridge: WebSocket

**Arquitetura planejada:**
```
┌─────────────────────────────────────────────────────┐
│                   Cliente (Browser)                 │
│  ┌──────────────┐         ┌──────────────────────┐ │
│  │   WebSocket  │  WS     │   Reconnect Logic    │ │
│  │   Client     │ ←────→  │   (Exponential B.O.) │ │
│  └──────────────┘         └──────────────────────┘ │
└─────────────────────────────────────────────────────┘
                    │
                    │ TCP/IP + WebSocket Protocol
                    ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI (Production Server)             │
│   • Endpoint: /ws/console?job_id={id}               │
│   • Heartbeat: Ping/Pong frames                     │
│   • Backpressure: asyncio.Queue limitada            │
│   • Broadcast: Múltiplos clientes por job           │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│           Agent Execution Layer                      │
│   • Claude Agent SDK                                 │
│   • Structlog/Loguru                                 │
│   • OpenTelemetry tracing                            │
└─────────────────────────────────────────────────────┘
```

**O que ganha:**
| ✅ Vantagem | Descrição |
|-------------|-----------|
| **Acesso remoto** | Clientes em qualquer lugar |
| **Multi-plataforma** | WebSocket é padrão web |
| **Escalabilidade** | Horizontal via load balancers |
| **Universal** | Funciona em browser, mobile, CLI |
| **Ecosistema maduro** | libs, ferramentas, best practices |
| **Comunidade** **HUGE** | Suporte amplamente disponível |
| **Padrão web** | IETF RFC 6455 |

**O que perde:**
| ❌ Desvantagem | Descrição |
|----------------|-----------|
| **Overhead de rede** | TCP/IP stack completo |
| **Conexão transiente** | Reconexão necessária |
| **Maior complexidade** | Heartbeat, backpressure, reconexão |
| **Single point of failure** | Server cai = todos desconectam |

---

### 3.3 Tabela Comparativa Final

| Aspecto | Auto-Claude (IPC) | Skybridge (WebSocket) | Vencedor |
|---------|-------------------|----------------------|----------|
| **Latência (local)** | ~0.1ms | ~1ms | IPC |
| **Latência (remoto)** | N/A | ~10-100ms | WS |
| **Escalabilidade** | Linear (1 servidor) | Exponencial (horizontal) | WS |
| **Resiliência** | Alta (processo detached) | Média (requer reconexão) | IPC |
| **Complexidade** | Alta (gerenciamento de processos) | Média (gerenciamento de conexões) | WS |
| **Debugabilidade** | Baixa | Alta | WS |
| **Acesso remoto** | ❌ | ✅ | WS |
| **Multiplexação** | ✅ | ✅ | Empate |
| **Padrão da indústria** | ❌ (Desktop apps) | ✅ (Web apps) | WS |
| **Overhead** | Mínimo | Moderado | IPC |

---

### 3.4 Quando usar cada um?

**Use Socket IPC (auto-claude style) se:**
- Aplicação desktop local (Electron, Tauri)
- Comunicação entre processos na mesma máquina
- Precisa de persistência através de restarts
- Performance crítica de latência

**Use WebSocket (skybridge style) se:**
- Aplicação web distribuída
- Clientes remotos/múltiplas localizações
- Escalabilidade horizontal é necessária
- Padrão web e ecosistema importam

`★ Insight ─────────────────────────────────────`
O auto-claude **não está errado** - ele está otimizado para o caso de uso desktop local. A Skybridge, sendo uma **API backend distribuída**, ganha muito mais com WebSocket. A escolha não é "bom vs ruim", mas **"ferramenta certa para o trabalho certo"**. Para máxima flexibilidade, poderíamos suportar AMBOS: WS para remoto + IPC para localhost development.
`─────────────────────────────────────────────────`

---

## 4. Análise da Implementação Skybridge

### 4.1 Código Atual: `src/runtime/delivery/websocket.py`

#### ✅ Pontos Fortes

```python
# Linha 47-58: Singleton pattern simples e funcional
class WebSocketConsoleManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()  # ✅ Thread safety
```

```python
# Linha 88-105: Broadcast funciona adequadamente
async def broadcast(self, job_id: str, message: ConsoleMessage):
    async with self._lock:
        connections = self.active_connections.get(job_id, set()).copy()
    # ✅ Copia antes de enviar para não segurar o lock
```

```python
# Linha 171-245: Router bem estruturado
@router.websocket("/ws/console")
async def console_websocket(...):
    # ✅ Query parameter para job_id
    # ✅ Endpoint claro e documentado
```

#### ❌ Problemas Críticos para Produção

| Problema | Local | Impacto | Severidade |
|----------|-------|---------|------------|
| **Sem heartbeat** | 220-222 | Conexões zumbis | 🔴 Alta |
| **Sem timeout** | 220-222 | Loop infinito | 🔴 Alta |
| **Exception swallowing** | 103-105 | Impossível debugar | 🟠 Média |
| **Sem backpressure** | 102 | OOM em clientes lentos | 🟠 Média |
| **Sem reconexão** | Cliente | UX ruim | 🟠 Média |
| **Sem buffer** | - | Perde histórico | 🟡 Baixa |
| **Sem métricas** | - | Zero observabilidade | 🟡 Baixa |

```python
# PROBLEMA 1: Loop infinito sem timeout
while True:
    await websocket.receive_text()  # ❌ Trava para sempre

# PROBLEMA 2: Exception sem log
except Exception:
    await self.disconnect(connection, job_id)  # ❌ Perde o erro

# PROBLEMA 3: Send sem backpressure
await connection.send_text(message.model_dump_json())  # ❌ Enfileira infinitamente
```

---

### 4.2 Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Cliente Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   WebSocket  │  │   SSE (logs) │  │   HTTP Poll  │              │
│  │  (Realtime)  │  │  (Unidirec)  │  │   (Fallback) │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ /ws/console  │  │ /stream/logs │  │   /metrics   │              │
│  │   WebSocket  │  │     SSE      │  │  (Prometheus)│              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
         │                                        │
         ▼                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Delivery Layer (Skybridge)                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                 ProductionWebSocketManager                    │  │
│  │  • Heartbeat (30s)                                           │  │
│  │  • Backpressure (Queue 1000)                                 │  │
│  │  • Ring Buffer (10k)                                         │  │
│  │  • Reconnect support                                         │  │
│  │  • Metrics (Prometheus)                                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Observability Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Structlog   │  │ OpenTelemetry│  │   Sentry     │              │
│  │  (JSON logs) │  │   (Traces)   │  │  (Errors)    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Agent Layer                                   │
│              Claude Agent SDK + Task Logger                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Recomendações e Roadmap

### 5.1 Priorização de Melhorias

#### 🔴 Fase 1: Crítico (Semanas 1-2)

| # | Tarefa | Effort | Impacto | Dependências |
|---|--------|--------|---------|--------------|
| 1.1 | Adicionar heartbeat/ping-pong | 2d | Alta | - |
| 1.2 | Implementar backpressure com Queue | 1d | Alta | - |
| 1.3 | Melhorar tratamento de exceções | 1d | Alta | - |
| 1.4 | Timeout no loop de recebimento | 0.5d | Alta | - |

#### 🟠 Fase 2: Importante (Semanas 3-4)

| # | Tarefa | Effort | Impacto | Dependências |
|---|--------|--------|---------|--------------|
| 2.1 | Migrar para Structlog (JSON) | 1d | Alta | 1.3 |
| 2.2 | Ring buffer para histórico | 1d | Média | - |
| 2.3 | Reconexão automática (cliente) | 2d | Alta | 1.1 |
| 2.4 | Adaptador ANSI→Markdown para Trello | 1d | Média | - |

#### 🟡 Fase 3: Observabilidade (Semanas 5-6)

| # | Tarefa | Effort | Impacto | Dependências |
|---|--------|--------|---------|--------------|
| 3.1 | Integração Prometheus | 2d | Alta | 2.1 |
| 3.2 | Integração Sentry | 1d | Alta | - |
| 3.3 | OpenTelemetry traces | 3d | Alta | 3.1 |
| 3.4 | Dashboard Grafana | 2d | Média | 3.1 |

#### ⚪ Fase 4: Nice-to-have (Semanas 7-8)

| # | Tarefa | Effort | Impacto | Dependências |
|---|--------|--------|---------|--------------|
| 4.1 | Rich console para dev local | 0.5d | Baixa | - |
| 4.2 | SSE endpoint para logs unidirecionais | 2d | Média | - |
| 4.3 | WebRTC para agent voice (future) | 5d | Alta | 3.3 |

---

### 5.2 Exemplo de Implementação Production-Ready

```python
# websocket.py - Versão completa com todas as melhorias

import asyncio
import json
import structlog
from collections import deque
from datetime import datetime
from typing import Any, Dict, Set, Optional
from prometheus_client import Gauge, Counter

from fastapi import WebSocket, WebSocketDisconnect

# Metrics
ws_connections = Gauge(
    "skybridge_websocket_connections",
    "WebSocket connections active",
    ["job_id"]
)

ws_messages_sent = Counter(
    "skybridge_websocket_messages_sent_total",
    "WebSocket messages sent",
    ["job_id", "level"]
)

ws_errors = Counter(
    "skybridge_websocket_errors_total",
    "WebSocket errors",
    ["error_type"]
)

logger = structlog.get_logger(__name__)


class ProductionWebSocketManager:
    """
    Gerenciador WebSocket production-ready.

    Features:
    - Heartbeat nativo (ping/pong)
    - Backpressure com Queue limitada
    - Ring buffer para histórico
    - Observabilidade completa
    - Graceful degradation
    """

    def __init__(
        self,
        max_buffer_size: int = 1000,
        ring_buffer_size: int = 10000,
        heartbeat_interval: float = 30.0,
        message_timeout: float = 10.0,
    ):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.history: Dict[str, deque] = {}
        self._lock = asyncio.Lock()

        # Config
        self.max_buffer_size = max_buffer_size
        self.ring_buffer_size = ring_buffer_size
        self.heartbeat_interval = heartbeat_interval
        self.message_timeout = message_timeout

    async def connect(self, websocket: WebSocket, job_id: str) -> None:
        """Conecta com heartbeat e sender loop."""
        await websocket.accept()

        async with self._lock:
            if job_id not in self.active_connections:
                self.active_connections[job_id] = set()
                self.message_queues[job_id] = asyncio.Queue(
                    maxsize=self.max_buffer_size
                )
                self.history[job_id] = deque(maxlen=self.ring_buffer_size)

            self.active_connections[job_id].add(websocket)
            ws_connections.labels(job_id=job_id).inc()

        # Tarefas concorrentes
        heartbeat = asyncio.create_task(
            self._heartbeat_loop(websocket, job_id)
        )
        sender = asyncio.create_task(
            self._sender_loop(websocket, job_id)
        )

        logger.info("websocket_connected", job_id=job_id)

    async def _heartbeat_loop(self, ws: WebSocket, job_id: str):
        """Envia pings periódicos."""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                await ws.send_ping()
                logger.debug("heartbeat_sent", job_id=job_id)
        except asyncio.CancelledError:
            logger.debug("heartbeat_cancelled", job_id=job_id)
        except Exception as e:
            logger.warning("heartbeat_failed", job_id=job_id, error=str(e))
            ws_errors.labels(error_type="heartbeat").inc()
            raise

    async def _sender_loop(self, ws: WebSocket, job_id: str):
        """Loop de envio com backpressure."""
        queue = self.message_queues[job_id]

        try:
            while True:
                msg = await queue.get()  # 🔒 Backpressure!
                await ws.send_text(msg)
                ws_messages_sent.labels(job_id=job_id, level="info").inc()
                logger.debug("message_sent", job_id=job_id)
        except Exception as e:
            logger.warning("sender_failed", job_id=job_id, error=str(e))
            ws_errors.labels(error_type="sender").inc()
            raise

    async def disconnect(self, ws: WebSocket, job_id: str) -> None:
        """Disconecta com cleanup."""
        async with self._lock:
            if job_id in self.active_connections:
                self.active_connections[job_id].discard(ws)
                ws_connections.labels(job_id=job_id).dec()

                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]

        logger.info("websocket_disconnected", job_id=job_id)

    async def broadcast(
        self,
        job_id: str,
        message: dict[str, Any]
    ) -> None:
        """Broadcast com backpressure."""
        async with self._lock:
            if job_id not in self.message_queues:
                logger.warning("job_not_found", job_id=job_id)
                return

            queue = self.message_queues[job_id]
            history = self.history[job_id]

        # Adiciona ao histórico
        history.append(message)

        # Tenta enviar com backpressure
        try:
            await asyncio.wait_for(
                queue.put(json.dumps(message)),
                timeout=self.message_timeout
            )
        except asyncio.TimeoutError:
            logger.error("broadcast_timeout", job_id=job_id)
            ws_errors.labels(error_type="timeout").inc()
            # Descarta mensagens mais antigas para abrir espaço
            if queue.full():
                queue.get_nowait()

    def get_history(self, job_id: str, limit: int = 100) -> list:
        """Retorna histórico de mensagens."""
        if job_id not in self.history:
            return []
        return list(self.history[job_id])[-limit:]


# Singleton
_manager: Optional[ProductionWebSocketManager] = None


def get_ws_manager() -> ProductionWebSocketManager:
    """Retorna singleton do gerenciador."""
    global _manager
    if _manager is None:
        _manager = ProductionWebSocketManager()
    return _manager
```

---

### 5.3 Cliente WebSocket com Reconexão

```python
# client.py - Exemplo de cliente Python com reconexão

import asyncio
import websockets
import json
from typing import Optional

class ReconnectingWebSocket:
    """Cliente WebSocket com reconexão automática."""

    def __init__(
        self,
        uri: str,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
    ):
        self.uri = uri
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._retry_delay = initial_delay

    async def connect(self) -> websockets.WebSocketClientProtocol:
        """Conecta com retry com exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                self._ws = await websockets.connect(self.uri)
                self._retry_delay = self.initial_delay  # Reset no sucesso
                return self._ws
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise

                print(f"Conexão falhou, tentando em {self._retry_delay}s...")
                await asyncio.sleep(self._retry_delay)
                self._retry_delay = min(
                    self._retry_delay * 2,  # Exponential backoff
                    self.max_delay
                )
        raise ConnectionError("Max retries exceeded")

    async def listen(self):
        """Escuta mensagens com auto-reconnect."""
        while True:
            try:
                ws = await self.connect()
                async for message in ws:
                    data = json.loads(message)
                    print(f"[{data['level']}] {data['message']}")
            except Exception as e:
                print(f"Conexão perdida: {e}")
                print("Reconectando...")


# Uso
async def main():
    client = ReconnectingWebSocket("ws://localhost:8000/ws/console?job_id=test")
    await client.listen()

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 5.4 Adaptador Rich → Markdown para Trello

```python
# trello_formatter.py - Converte Rich/ANSI para Markdown Trello

import re
from rich.console import Console
from rich.text import Text

def ansi_to_trello_markdown(text: str) -> str:
    """
    Converte texto ANSI/Rich para Markdown compatível com Trello.

    Trello suporta:
    - **bold**, *italic*, `code`
    - ## Headers
    - - Lists
    - ```code blocks```
    - [Links](url)

    NÃO suporta:
    - Cores ANSI
    - HTML customizado
    - CSS inline
    """
    # Remove sequências ANSI
    clean = re.sub(r'\x1b\[[0-9;]*m', '', text)

    # Detecta padrões de erro para destacar
    error_keywords = ['error', 'exception', 'failed', 'critical']
    warning_keywords = ['warning', 'warn', 'deprecated']
    success_keywords = ['success', 'completed', 'done', 'finished']
    info_keywords = ['info', 'debug', 'trace']

    lower_text = clean.lower()

    if any(kw in lower_text for kw in error_keywords):
        return f"```\n🔴 {clean.strip()}\n```"

    if any(kw in lower_text for kw in warning_keywords):
        return f"```\n⚡ {clean.strip()}\n```"

    if any(kw in lower_text for kw in success_keywords):
        return f"✅ {clean.strip()}"

    if any(kw in lower_text for kw in info_keywords):
        return f"ℹ️ {clean.strip()}"

    return clean.strip()


def format_log_for_trello(
    level: str,
    message: str,
    context: dict | None = None
) -> str:
    """Formata log estruturado para Trello card."""
    parts = [f"**{level.upper()}**: {message}"]

    if context:
        parts.append("\n**Context:**")
        for key, value in context.items():
            parts.append(f"- `{key}`: {value}")

    return "\n".join(parts)


# Uso
from loguru import logger

def log_to_trello(card_id: str, message: str, level: str = "info"):
    """Envia log para card Trello via API."""
    from trello import TrelloClient

    markdown = format_log_for_trello(level, message)

    client = TrelloClient(
        api_key=os.getenv("TRELLO_API_KEY"),
        api_secret=os.getenv("TRELLO_API_SECRET"),
        token=os.getenv("TRELLO_TOKEN")
    )

    card = client.get_card(card_id)
    card.comment(markdown)  # Adiciona como comentário
```

---

## 6. Conclusão

### Resumo Executivo

| Aspecto | Estado Atual | Recomendação | Prioridade |
|---------|--------------|--------------|------------|
| **Logging** | Basic stdout | Loguru (dev) + Structlog (prod) | 🔴 Alta |
| **Streaming** | WebSocket básico | Com heartbeat + backpressure | 🔴 Alta |
| **Observabilidade** | Nenhuma | Prometheus + Sentry + OTel | 🟠 Média |
| **Rich Console** | Não implementado | Adicionar para dev local | 🟡 Baixa |
| **Trello Formatting** | Markdown básico | Adaptador ANSI→MD | 🟡 Baixa |
| **Arquitetura** | Monolito | Layers separadas | 🟠 Média |

### Próximos Passos Imediatos

1. ✅ Implementar heartbeat no WebSocket (2 dias)
2. ✅ Adicionar backpressure com Queue (1 dia)
3. ✅ Migrar logging para Loguru/Structlog (1 dia)
4. ✅ Integração Prometheus (2 dias)
5. ✅ Integração Sentry (1 dia)

### Metrics de Sucesso

| Metrica | Target | Medição |
|---------|--------|---------|
| Latência de streaming | <100ms (p95) | Prometheus histogram |
| Conexões simultâneas | >1000 | Load testing |
| Uptime WebSocket | >99.9% | Sentry uptime |
| Taxa de erro | <0.1% | Sentry error rate |
| Tempo de reconexão | <5s (p95) | Client metrics |

---

## Referências

### Artigos e Documentação

- [Rich Console Output](https://rich.readthedocs.io/)
- [Loguru Documentation](https://github.com/Delgan/loguru)
- [Structlog Documentation](https://www.structlog.org/)
- [Trello Markdown Support](https://support.atlassian.com/trello/docs/how-to-format-your-text-in-trello/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Sentry FastAPI Integration](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [WebSockets vs SSE Comparison](https://ably.com/blog/websockets-vs-sse)
- [WebSocket Architecture Best Practices](https://ably.com/topic/websocket-architecture-best-practices)
- [AsyncIO Backpressure Patterns](https://medium.com/@connect.hashblock/7-asyncio-patterns-for-concurrency-friendly-python-685abeb2a534)
- [FastRTC Real-Time Communication](https://fastrtc.org/)
- [Production Logging with Loguru](https://www.dash0.com/guides/python-logging-with-loguru)
- [Structured Logging with Structlog](https://newrelic.com/blog/log/python-structured-logging)

### Libraries Python

```txt
# requirements.txt - Versões recomendadas

# Logging
loguru==0.7.2
structlog==25.5.0
rich==13.9.4

# Real-time
websockets==16.0
aiohttp==3.11.11
fastrtc==0.2.0  # Opcional para WebRTC

# Observabilidade
opentelemetry-api==1.30.0
opentelemetry-sdk==1.30.0
opentelemetry-instrumentation-fastapi==0.51b0
opentelemetry-instrumentation-logging==0.51b0
opentelemetry-exporter-otlp==1.30.0

prometheus-client==1.0.0
prometheus-fastapi-instrumentator==7.0.0

sentry-sdk[fastapi]==2.19.2

# Utils
python-dotenv==1.0.1
pydantic==2.10.4
pydantic-settings==2.7.1
```

---

## Apêndice A: Quick Start - Logging Híbrido

```python
# logging_config.py - Configuração completa de logging híbrido

import sys
import logging
from loguru import logger as loguru
import structlog

# 1. Loguru para desenvolvimento local
loguru.remove()  # Remove handler padrão
loguru.add(
    sys.stderr,
    format="<g>{time:YYYY-MM-DD HH:mm:ss}</g> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

loguru.add(
    "logs/skybridge_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    level="INFO",
)

# 2. Structlog para produção JSON
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

# 3. Bridge stdlib logging → structlog
class LoggingInterceptor(logging.Handler):
    """Intercepta stdlib logging e envia para structlog."""

    def emit(self, record):
        structlog = structlog.get_logger()
        structlog.log(
            record.levelno,
            record.getMessage(),
            name=record.name,
            function=record.funcName,
            line=record.lineno,
        )

# Aplica interceptor
logging.basicConfig(handlers=[LoggingInterceptor()], level=logging.INFO)

# Uso
if __name__ == "__main__":
    # Loguru (dev local)
    loguru.info("Iniciando aplicação", version="1.0.0")

    # Structlog (produção JSON)
    logger = structlog.get_logger()
    logger.info("app_started", version="1.0.0", environment="production")

    # Stdlib logging também funciona
    logging.info("Stdlib log também é interceptado!")
```

---

## Apêndice B: Cheatsheet de Formatação Trello

| Markdown | Renderização no Trello | Uso |
|----------|------------------------|-----|
| `**texto**` | **texto** | Negrito para ênfase |
| `*texto*` | *texto* | Itálico |
| `` `texto` `` | `texto` | Inline code |
| `## Título` | ## Título | Heading |
| `- Item` | • Item | Bullet list |
| ````bloco```` | Code block | Código/multiline |
| `[link](url)` | [link](url) | Hiperlink |
| `✅` | ✅ | Sucesso |
| `❌` | ❌ | Erro |
| `⚠️` | ⚠️ | Aviso |
| `ℹ️` | ℹ️ | Informação |

---

> "A observabilidade não é um luxo, é um requisito de produção. Não conserte o que você não pode ver." – Made by Sky 🚀

---

**Fim do Relatório**

*Gerado em 25 de Janeiro de 2026*
*Versão 1.0 - Confidencial e Proprietário*
