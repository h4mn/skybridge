# Structlog Deep Dive: JSON, Telemetria e Hibridização

**Data:** 25 de Janeiro de 2026
**Autor:** Sky
**Versão:** 1.0

---

## Índice

1. [Conceitos Fundamentais do Structlog](#1-conceitos-fundamentais)
2. [JSON Renderer e Processors](#2-json-renderer-e-processors)
3. [Telemetria com OpenTelemetry](#3-telemetria-com-opentelemetry)
4. [Hibridização: Loguru + Structlog](#4-hibridização-loguru--structlog)
5. [ContextVars e Correlation IDs](#5-contextvars-e-correlation-ids)
6. [Implementação Produção-Ready](#6-implementação-produção-ready)

---

## 1. Conceitos Fundamentais do Structlog

### 1.1 Arquitetura baseada em Processors

O Structlog usa um **pipeline de processors** que transformam o log evento:

```python
# O fluxo de dados no Structlog
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Log Call   │ -> │ Processor 1 │ -> │ Processor 2 │ -> │ Processor N │
│ logger.info │    │ (add data)  │    │ (transform) │    │ (render)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   {"level": "INFO"}  {"timestamp": "..."}  {"event": "..."}
```

**Cada processor:**
1. Recebe um dicionário (o log event)
2. Adiciona/modifica campos
3. Passa para o próximo processor
4. O último processor é sempre um **Renderer**

```python
import structlog

# Exemplo simples do pipeline
processors = [
    # 1. Adiciona timestamp
    structlog.processors.TimeStamper(fmt="iso"),

    # 2. Adiciona log level
    structlog.processors.add_log_level,

    # 3. Adiciona nome da função
    structlog.processors.CallsiteParameterAdder(
        [structlog.processors.CallsiteParameter.FUNC_NAME]
    ),

    # 4. Renderer final (JSON ou Console)
    structlog.dev.ConsoleRenderer()  # ou structlog.processors.JSONRenderer()
]

structlog.configure(processors=processors)
```

### 1.2 Event Dictionary - O Coração do Structlog

```python
# O que acontece por baixo dos panos
log = structlog.get_logger()

# Quando você chama:
log.info("user_login", user_id=123, ip="192.168.1.1")

# O structlog constrói este dicionário:
event_dict = {
    "event": "user_login",           # A mensagem principal
    "user_id": 123,                  # Contexto customizado
    "ip": "192.168.1.1",             # Contexto customizado
    "level": "info",                 # Adicionado por add_log_level
    "timestamp": "2026-01-25T10:30:00",  # Adicionado por TimeStamper
    "function": "login_user",        # Adicionado por CallsiteParameterAdder
}

# E passa por todos os processors
```

---

## 2. JSON Renderer e Processors

### 2.1 JSONRenderer - O Que Exatamente Faz

```python
from structlog.processors import JSONRenderer

# O JSONRenderer simplesmente converte o dicionário final para JSON
import json

class JSONRenderer:
    """Renderiza log events como JSON."""

    def __call__(self, logger, name, event_dict):
        # event_dict é o dicionário com todos os campos
        return json.dumps(event_dict) + "\n"  # ← Note o \n para JSONL
```

**Sim, é um "jsonify" automático!**

```python
# Exemplo prático
import structlog
from structlog.processors import JSONRenderer

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        JSONRenderer()  # ← Isso é o "jsonify"
    ]
)

log = structlog.get_logger()
log.info("user_login", user_id=123, ip="192.168.1.1")

# Saída (JSON válido, uma linha por log):
# {"event": "user_login", "user_id": 123, "ip": "192.168.1.1", "level": "info", "timestamp": "2026-01-25T10:30:00Z"}
```

### 2.2 Processors Essenciais

| Processor | Oque Faz | Quando Usar |
|-----------|----------|-------------|
| `TimeStamper` | Adiciona campo `timestamp` | Sempre |
| `add_log_level` | Adiciona campo `level` | Sempre |
| `JSONRenderer` | Converte para JSON string | Produção |
| `ConsoleRenderer` | Formata para terminal bonito | Desenvolvimento |
| `CallsiteParameterAdder` | Adiciona module, function, lineno | Debug |
| `StackInfoRenderer` | Adiciona stack trace | Debug avançado |
| `format_exc_info` | Formata exceções com traceback | Error handling |
| `UnicodeDecoder` | Decodifica bytes para strings | Quando necessário |
| `EventRenamer` | Renomeia o campo `event` | Integração com stdlib |

### 2.3 Custom Processors

```python
# Criando seu próprio processor
def add_app_info(logger, name, event_dict):
    """Adiciona info da aplicação em todos os logs."""
    event_dict["app"] = "skybridge"
    event_dict["version"] = "1.0.0"
    event_dict["environment"] = os.getenv("ENV", "development")
    return event_dict

def mask_sensitive_data(logger, name, event_dict):
    """Mascara dados sensíveis."""
    sensitive_keys = ["password", "token", "api_key", "secret"]

    for key in sensitive_keys:
        if key in event_dict:
            event_dict[key] = "***REDACTED***"

    return event_dict

# Uso
structlog.configure(
    processors=[
        add_app_info,          # ← Custom processor
        mask_sensitive_data,   # ← Custom processor
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

log.info("api_call", endpoint="/users", token="super-secret")
# Saída: {"app": "skybridge", "version": "1.0.0", "environment": "development",
#         "endpoint": "/users", "token": "***REDACTED***", ...}
```

---

## 3. Telemetria com OpenTelemetry

### 3.1 Integração Nativa Structlog + OpenTelemetry

```python
# requirements.txt
# opentelemetry-api
# opentelemetry-sdk
# opentelemetry-instrumentation-logging
# structlog
```

```python
import structlog
from structlog.types import EventDict, Processor
from opentelemetry import trace

# Processor que injeta trace_id e span_id do OpenTelemetry
def add_trace_id(logger, name, event_dict: EventDict) -> EventDict:
    """
    Adiciona trace_id e span_id do OpenTelemetry ao log event.

    Isso permite correlacionar logs com traces no Jaeger/Tempo/Grafana.
    """
    current_span = trace.get_current_span()

    if current_span is not None:
        span_context = current_span.get_span_context()
        event_dict["trace_id"] = format(span_context.trace_id, "032x")
        event_dict["span_id"] = format(span_context.span_id, "016x")
        event_dict["trace_flags"] = span_context.trace_flags

    return event_dict


# Configuração com OpenTelemetry
structlog.configure(
    processors=[
        # 1. Telemetria primeiro
        add_trace_id,

        # 2. Contexto padrão
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,

        # 3. Processor oficial do OpenTelemetry para structlog
        structlog.processors.OpenTelemetryProcessor(),

        # 4. Renderer final
        structlog.processors.JSONRenderer()
    ]
)
```

### 3.2 Exemplo Prático: Request → Webhook → Agent → Log

```python
from fastapi import FastAPI, Request
from opentelemetry import trace
import structlog

app = FastAPI()
tracer = trace.get_tracer(__name__)
log = structlog.get_logger()

@app.post("/webhooks/trello")
async def trello_webhook(request: Request):
    # Cria um span do OpenTelemetry
    with tracer.start_as_current_span("process_trello_webhook") as span:
        # O trace_id já está no context
        log.info("webhook_received", webhook_type="trello")

        # Adiciona atributos ao span
        span.set_attribute("webhook.type", "trello")
        span.set_attribute("webhook.id", request.headers.get("X-Trello-Webhook"))

        # Processa o webhook...
        result = await process_webhook(await request.json())

        # Log com o MESMO trace_id
        log.info("webhook_processed", result="success")

        return result

# Logs correlacionados automaticamente:
# {"event": "webhook_received", "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
#  "span_id": "00f067aa0ba902b7", ...}
#
# {"event": "webhook_processed", "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
#  "span_id": "00f067aa0ba902b7", ...}
#
# Mesmo trace_id = mesma request!
```

### 3.3 OpenTelemetryProcessor Built-in

```python
# Structlog tem um processor oficial!
from structlog.processors import OpenTelemetryProcessor

structlog.configure(
    processors=[
        # O processor oficial faz TUDO automaticamente:
        # - Adiciona trace_id
        # - Adiciona span_id
        # - Adiciona service_name
        # - Adiciona outros atributos do OTel
        OpenTelemetryProcessor(),

        structlog.processors.JSONRenderer()
    ]
)
```

**O que o OpenTelemetryProcessor adiciona:**

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `trace_id` | ID do trace distribuído | `"4bf92f3577b34da6a3ce929d0e0e4736"` |
| `span_id` | ID do span atual | `"00f067aa0ba902b7"` |
| `trace_flags` | Flags do trace | `"01"` |
| `service_name` | Nome do serviço (config OTel) | `"skybridge-api"` |

---

## 4. Hibridização: Loguru + Structlog

### 4.1 Por que Hibridizar?

| Lib | Pontos Fortes | Pontos Fracos |
|-----|----------------|---------------|
| **Loguru** | • Zero boilerplate<br>• Bonito no terminal<br>• Exception handling excelente | • JSON requer configuração manual<br>• Menos flexível para processors custom |
| **Structlog** | • JSON nativo<br>• Processors flexíveis<br>• OpenTelemetry nativo | • Requer configuração<br>• Console output menos bonito |

**Hibridização = Melhor dos dois mundos:**
- Loguru para **desenvolvimento local** (console bonito)
- Structlog para **produção** (JSON estruturado + OTel)

### 4.2 Padrão 1: Dual Loggers (Simples)

```python
# logging_config.py - Dual loggers simples
import logging
import sys
from loguru import logger as loguru
import structlog

# Loguru: Console local
loguru.remove()
loguru.add(
    sys.stderr,
    format="<g>{time:YYYY-MM-DD HH:mm:ss}</g> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

# Structlog: Produção JSON
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

struct_logger = structlog.get_logger()

# Uso no código
def process_webhook(payload: dict):
    # Dev local: Loguru
    loguru.info("Processing webhook", webhook_type=payload.get("type"))

    # Produção: Structlog
    struct_logger.info("webhook_processing", webhook_type=payload.get("type"))
```

**Problema:** Dupla chamada em todo log. Verboso.

### 4.3 Padrão 2: Interceptador Stdlib (Recomendado)

```python
# logging_config.py - Padrão interceptador
import logging
import sys
from loguru import logger as loguru
import structlog

# 1. Configura Loguru
loguru.remove()
loguru.add(
    sys.stderr,
    format="<g>{time:HH:mm:ss}</g> | <level>{level: <8}</level> | <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)
loguru.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
)

# 2. Configura Structlog para JSON (produção)
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.BytesLoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
)

# 3. Intercepta stdlib logging → Structlog
class StdlibToStructlogHandler(logging.Handler):
    """
    Intercepta logs do stdlib e envia para structlog.

    Assim, loguru e qualquer outra lib que use stdlib logging
    automaticamente vão para Structlog JSON também.
    """
    def __init__(self):
        super().__init__()
        self.struct_logger = structlog.get_logger()

    def emit(self, record: logging.LogRecord) -> None:
        # Converte LogRecord para dict
        log_dict = {
            "event": record.getMessage(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Adiciona exceção se presente
        if record.exc_info:
            log_dict["exception"] = self.formatter.formatException(record.exc_info)

        # Envia para structlog
        self.struct_logger.log(record.levelno, "", **log_dict)


# 4. Aplica interceptador
logging.basicConfig(
    handlers=[StdlibToStructlogHandler()],
    level=logging.INFO,
)

# Uso: AGORA UMA SÓ CHAMADA!
def process_webhook(payload: dict):
    # Vai para Loguru (console) E Structlog (JSON) automaticamente
    logging.info("Processing webhook", extra={"webhook_type": payload.get("type")})
```

**Problema:** O `extra=` do stdlib é verboso.

### 4.4 Padrão 3: Structlog com Dual Output (PERFEITO)

```python
# logging_config.py - Configuração perfeita para Skybridge
import logging
import sys
from typing import Any
from loguru import logger as loguru
import structlog

# Custom processor que loga em ambos
class DualOutputProcessor:
    """
    Processor que envia log para Loguru (console) E retorna para Structlog.

    Assim você tem UMA chamada de log que vai para os dois lugares.
    """
    def __init__(self, console_level: str = "DEBUG"):
        self.console_level = console_level

    def __call__(self, logger, name, event_dict: dict[str, Any]) -> dict[str, Any]:
        # Envia cópia para Loguru console
        log_level = event_dict.get("level", "info").upper()
        message = event_dict.get("event", "")
        context = {k: v for k, v in event_dict.items() if k not in {"event", "level"}}

        # Loguru recebe
        getattr(loguru, log_level.lower())(message, **context)

        # Retorna o event_dict para continuar o pipeline do Structlog
        return event_dict


# Configuração Structlog com dual output
def configure_logging(environment: str = "development"):
    """Configura logging baseado no ambiente."""

    if environment == "production":
        # Produção: Apenas JSON (sem console colorido)
        processors = [
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Desenvolvimento: Dual output
        processors = [
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            DualOutputProcessor(console_level="DEBUG"),  # ← O segredo!
            structlog.processors.JSONRenderer()
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
    )


# Uso: UMA CHAMADA, DOIS OUTPUTS!
configure_logging(environment="development")

log = structlog.get_logger()

@app.post("/webhooks/trello")
async def trello_webhook(payload: dict):
    log.info("webhook_received", webhook_type="trello", payload_size=len(str(payload)))

    # Console (Loguru):
    # 10:30:00 | INFO     | webhook_received webhook_type='trello' payload_size=1234
    #
    # Arquivo/Stdout (Structlog JSON):
    # {"event": "webhook_received", "webhook_type": "trello", "payload_size": 1234,
    #  "level": "info", "timestamp": "2026-01-25T10:30:00Z"}
```

`★ Insight ─────────────────────────────────────`
O segredo da hibridização perfeita é o **DualOutputProcessor**: ele injeta o Loguru no pipeline do Structlog. Assim você mantém a API simples do Structlog (`log.info("msg", key=val)`) mas tem output bonito no console E JSON em produção. Um log, dois destinos.
`─────────────────────────────────────────────────`

---

## 5. ContextVars e Correlation IDs

### 5.1 O Problema do Contexto Distribuído

```python
# Sem contextvars: você tem que passar contexto manualmente
def process_webhook(webhook_id: str, user_id: str, payload: dict):
    # Tedioso: repetir contexto em toda chamada de log
    log.info("processing", webhook_id=webhook_id, user_id=user_id)
    validate_payload(payload, webhook_id=webhook_id, user_id=user_id)
    call_agent(payload, webhook_id=webhook_id, user_id=user_id)
```

### 5.2 Solução: ContextVars

```python
import structlog
from contextvars import ContextVar

# ContextVar global para requestId
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")

# Middleware que seta o contexto
@app.middleware("http")
async def add_request_context(request: Request, call_next):
    # Gera/Extrai request_id
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    user_id = request.headers.get("X-User-ID", "anonymous")

    # Seta no context (automático para async!)
    request_id_var.set(request_id)
    user_id_var.set(user_id)

    # Processa request
    response = await call_next(request)

    # Adiciona ao response
    response.headers["X-Request-ID"] = request_id
    return response


# Processor que lê contextvars
def add_context_from_vars(logger, name, event_dict):
    """Adiciona request_id e user_id do context ao log."""
    if request_id_var.get():
        event_dict["request_id"] = request_id_var.get()
    if user_id_var.get():
        event_dict["user_id"] = user_id_var.get()
    return event_dict


# Configura
structlog.configure(
    processors=[
        add_context_from_vars,  # ← Lê do context automaticamente
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)


# AGORA SIM: código limpo!
def process_webhook(payload: dict):
    # Não precisa passar request_id/user_id!
    log.info("processing_webhook")
    validate_payload(payload)
    call_agent(payload)

    # Todos os logs terão request_id e user_id automaticamente:
    # {"event": "processing_webhook", "request_id": "abc-123", "user_id": "user@ex.com", ...}
```

### 5.3 ContextVars + OpenTelemetry = Correlation Perfeita

```python
import structlog
from opentelemetry import trace
from contextvars import ContextVar

# ContextVars
request_id_var: ContextVar[str] = ContextVar("request_id")

# Processor combinado
def add_full_correlation(logger, name, event_dict):
    """Adiciona correlation ID + OpenTelemetry trace."""
    # 1. Request ID (nosso)
    if request_id_var.get():
        event_dict["request_id"] = request_id_var.get()

    # 2. Trace ID (OpenTelemetry)
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        span_context = current_span.get_span_context()
        event_dict["trace_id"] = format(span_context.trace_id, "032x")
        event_dict["span_id"] = format(span_context.span_id, "016x")

    return event_dict


# Logs com correlação completa
@app.post("/webhooks/trello")
async def trello_webhook(request: Request):
    request_id = str(uuid4())
    request_id_var.set(request_id)

    with tracer.start_as_current_span("process_webhook"):
        log.info("webhook_received")

        # Resultado:
        # {
        #   "event": "webhook_received",
        #   "request_id": "abc-123-def-456",      # ← Nosso correlation
        #   "trace_id": "4bf92f3577b34da6...",     # ← OTel correlation
        #   "span_id": "00f067aa0ba902b7",        # ← OTel correlation
        #   "timestamp": "2026-01-25T10:30:00Z"
        # }
```

---

## 6. Implementação Produção-Ready

### 6.1 Configuração Completa para Skybridge

```python
# src/runtime/logging_config.py
"""
Configuração de logging production-ready para Skybridge.

Features:
- Hibridização Loguru (dev) + Structlog (prod)
- OpenTelemetry integration
- ContextVars para correlation
- Dual output (console + JSON)
- Masking de dados sensíveis
"""

import os
import sys
import logging
from typing import Any
from contextvars import ContextVar
from uuid import uuid4

from loguru import logger as loguru
import structlog
from structlog.types import EventDict, Processor
from opentelemetry import trace


# ContextVars globais
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


# ┌─────────────────────────────────────────────────────────────┐
# │ CUSTOM PROCESSORS                                             │
# └─────────────────────────────────────────────────────────────┘

def add_app_info(logger, name, event_dict: EventDict) -> EventDict:
    """Adiciona info da aplicação."""
    event_dict.update({
        "service": "skybridge",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("ENV", "development"),
    })
    return event_dict


def add_correlation(logger, name, event_dict: EventDict) -> EventDict:
    """Adiciona request_id, correlation_id e OpenTelemetry trace."""
    # Request ID (nosso)
    if request_id_var.get():
        event_dict["request_id"] = request_id_var.get()

    # Correlation ID (pode vir de upstream)
    if correlation_id_var.get():
        event_dict["correlation_id"] = correlation_id_var.get()

    # OpenTelemetry trace
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        span_context = current_span.get_span_context()
        event_dict["trace_id"] = format(span_context.trace_id, "032x")
        event_dict["span_id"] = format(span_context.span_id, "016x")

    return event_dict


def mask_sensitive_data(logger, name, event_dict: EventDict) -> EventDict:
    """Mascara dados sensíveis."""
    sensitive_keys = {
        "password", "token", "api_key", "secret", "api_secret",
        "access_token", "refresh_token", "private_key", "webhook_secret"
    }

    for key in sensitive_keys:
        if key in event_dict:
            value = str(event_dict[key])
            # Mostra primeiros 4 e últimos 4 caracteres
            if len(value) > 8:
                event_dict[key] = f"{value[:4]}...{value[-4:]}"
            else:
                event_dict[key] = "***REDACTED***"

    return event_dict


class DualOutputProcessor:
    """Processor que loga para Loguru E retorna para Structlog."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def __call__(self, logger, name, event_dict: EventDict) -> EventDict:
        if not self.enabled:
            return event_dict

        # Extrai campos
        level = event_dict.get("level", "info").upper()
        message = event_dict.get("event", "")

        # Contexto para Loguru (remove campos internos)
        context = {
            k: v for k, v in event_dict.items()
            if k not in {"event", "level", "timestamp", "service", "version"}
        }

        # Envia para Loguru
        try:
            getattr(loguru, level.lower())(message, **context)
        except AttributeError:
            loguru.log(level, message, **context)

        return event_dict


# ┌─────────────────────────────────────────────────────────────┐
# │ CONFIGURAÇÃO                                                 │
# └─────────────────────────────────────────────────────────────┘

def configure_logging(
    environment: str = "development",
    log_level: str = "INFO",
    enable_console: bool = True,
) -> None:
    """
    Configura logging para Skybridge.

    Args:
        environment: "development" ou "production"
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        enable_console: Se True, habilita output colorido no console
    """
    # 1. Configura Loguru (sempre)
    loguru.remove()
    loguru.add(
        sys.stderr,
        format=(
            "<g>{time:HH:mm:ss}</g> | "
            "<level>{level: <8}</level> | "
            "<c>{request_id}</c> | "
            "<level>{message}</level>"
        ),
        level=log_level,
        colorize=True,
        filter=lambda record: enable_console,  # Só se habilitado
    )
    loguru.add(
        "logs/skybridge_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        level="INFO",
        enqueue=True,  # Thread-safe
    )

    # 2. Configura Structlog
    base_processors = [
        # Processors de telemetria
        add_app_info,
        add_correlation,

        # Processor padrão
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,

        # Segurança
        mask_sensitive_data,
    ]

    # Production: adiciona OpenTelemetry
    if environment == "production":
        base_processors.append(structlog.processors.OpenTelemetryProcessor())

    # Development: adiciona dual output
    if environment == "development" and enable_console:
        base_processors.append(DualOutputProcessor(enabled=True))

    # Renderer final
    base_processors.append(structlog.processors.JSONRenderer())

    # Configura
    structlog.configure(
        processors=base_processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level)),
        cache_logger_on_first_use=True,
    )

    loguru.info(
        "Logging configured",
        environment=environment,
        log_level=log_level,
        console_enabled=enable_console,
    )


# ┌─────────────────────────────────────────────────────────────┐
# │ FASTAPI INTEGRATION                                          │
# └─────────────────────────────────────────────────────────────┘

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware que adiciona contexto de request aos logs."""

    async def dispatch(self, request: Request, call_next):
        # Extrai ou gera request_id
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        correlation_id = request.headers.get("X-Correlation-ID", "")

        # Seta no context
        request_id_var.set(request_id)
        if correlation_id:
            correlation_id_var.set(correlation_id)

        # Log request
        log = structlog.get_logger()
        log.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )

        # Processa request
        try:
            response = await call_next(request)
            log.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            )
            return response

        except Exception as e:
            log.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise


# ┌─────────────────────────────────────────────────────────────┐
# │ EXPORTS                                                       │
# └─────────────────────────────────────────────────────────────┘

__all__ = [
    "configure_logging",
    "LoggingMiddleware",
    "request_id_var",
    "correlation_id_var",
    "loguru",
]
```

### 6.2 Exemplo de Uso Completo

```python
# main.py - FastAPI app com logging completo
from fastapi import FastAPI
from opentelemetry import trace
from src.runtime.logging_config import (
    configure_logging,
    LoggingMiddleware,
    request_id_var,
)
import structlog

# 1. Configura logging
configure_logging(
    environment=os.getenv("ENV", "development"),
    log_level="INFO",
    enable_console=True,
)

# 2. Cria app
app = FastAPI(title="Skybridge API")

# 3. Adiciona middleware de logging
app.add_middleware(LoggingMiddleware)

# 4. Importa logger
log = structlog.get_logger()
tracer = trace.get_tracer(__name__)


@app.post("/webhooks/trello")
async def trello_webhook(request: Request, payload: dict):
    """
    Endpoint para webhooks do Trello.

    Todos os logs terão automaticamente:
    - request_id (único por request)
    - correlation_id (se fornecido)
    - trace_id e span_id (do OpenTelemetry)
    """
    with tracer.start_as_current_span("process_trello_webhook") as span:
        span.set_attribute("webhook.type", "trello")

        # Log com contexto automático!
        log.info("webhook_received", webhook_id=payload.get("id"))

        # Processa...
        result = await process_webhook(payload)

        log.info("webhook_processed", result="success")
        return result


@app.post("/agents/{agent_id}/run")
async def run_agent(agent_id: str, input_data: dict):
    """Executa um agente."""
    log = structlog.get_logger().bind(agent_id=agent_id)

    with tracer.start_as_current_span("agent_execution") as span:
        span.set_attribute("agent.id", agent_id)

        log.info("agent_execution_started")

        try:
            result = await execute_agent(agent_id, input_data)
            log.info("agent_execution_completed", result=result)
            return result

        except Exception as e:
            log.error("agent_execution_failed", error=str(e))
            raise
```

### 6.3 Exemplo de Log Output

```json
// Desenvolvimento (console + arquivo JSON)
// Console (Loguru - bonito):
10:30:00 | INFO     | abc-123-def-456 | webhook_received webhook_id='12345' webhook_type='trello'

// Arquivo (Structlog JSON):
{
  "service": "skybridge",
  "version": "1.0.0",
  "environment": "development",
  "request_id": "abc-123-def-456",
  "correlation_id": "upstream-correlation-789",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "event": "webhook_received",
  "webhook_id": "12345",
  "webhook_type": "trello",
  "level": "info",
  "timestamp": "2026-01-25T10:30:00.123456Z"
}
```

---

## 7. Referências Rápidas

### 7.1 Cheatsheet de Processors

```python
# Processors essenciais
processors = [
    # Timestamp
    structlog.processors.TimeStamper(fmt="iso"),  # ou "unix" ou fmt custom

    # Level
    structlog.processors.add_log_level,  # Adiciona campo "level"

    # Callsite info
    structlog.processors.CallsiteParameterAdder([
        structlog.processors.CallsiteParameter.MODULE_NAME,
        structlog.processors.CallsiteParameter.FUNC_NAME,
        structlog.processors.CallsiteParameter.LINENO,
    ]),

    # Exception
    structlog.processors.format_exc_info,  # Formata exception

    # OpenTelemetry
    structlog.processors.OpenTelemetryProcessor(),

    # Renderer (SEMPRE o último!)
    structlog.processors.JSONRenderer(),  # JSON
    # ou
    structlog.dev.ConsoleRenderer(),  # Console bonito
]
```

### 7.2 Cheatsheet de ContextVars

```python
import structlog
from contextvars import ContextVar

# Define
request_id_var: ContextVar[str] = ContextVar("request_id")

# Seta
request_id_var.set("abc-123")

# Lê
value = request_id_var.get()  # "abc-123"

# No processor
def add_context(logger, name, event_dict):
    if request_id_var.get():
        event_dict["request_id"] = request_id_var.get()
    return event_dict
```

### 7.3 Cheatsheet de OpenTelemetry

```python
from opentelemetry import trace
import structlog

# Configura OTel
structlog.configure(
    processors=[
        structlog.processors.OpenTelemetryProcessor(),  # ← Adiciona trace_id/span_id
        structlog.processors.JSONRenderer()
    ]
)

# No código
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("operation_name") as span:
    span.set_attribute("key", "value")
    log.info("doing_something")

    # Log automaticamente tem trace_id e span_id
```

---

> "Estrutura é a liberdade de escalar." – made by Sky 🚀
