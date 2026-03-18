# PRD022: Servidor Unificado Skybridge

**Status:** 📋 Proposta
**Data:** 2026-01-26
**Autor:** Sky
**Prioridade:** P0 (Crítica)
**Complexidade:** Média
**Relacionado:** PoCs LOG-001, LOG-002, LOG-003, LOG-004

---

## 1. Contexto e Problema

### 1.1 Contexto Atual

O Skybridge atualmente opera com múltiplos pontos de entrada e estratégias de logging fragmentadas:

```
Estrutura ATUAL (fragmentada):

apps/server/main.py           ← API FastAPI (porta 8000)
apps/webui/main.py         ← WebUI (porta 3000, se rodar separado)
Logging inconsistente:
  - Uvicorn access_log (formato fixo)
  - Logging manual (sem padrão)
  - Sem correlation_id propagado
  - Sem métricas de performance
```

### 1.2 Problemas Identificados

| Problema | Impacto | Severidade |
|----------|---------|------------|
| **Múltiplos entrypoints** | Complexidade operacional | Alta |
| **Logging fragmentado** | Dificulta debug e observabilidade | Alta |
| **Sem métricas de request** | Impossível medir performance | Alta |
| **Logs sem cores** | Experiência do dev pobre | Média |
| **Ngrok duplicado** | Custo e overhead desnecessário | Média |

### 1.3 Justificativa

Quatro PoCs de logging (LOG-001 a LOG-004) foram implementados e validaram uma **estratégia híbrida** que resolve todos os problemas acima. Este PRD consolida os aprendizados em uma implementação production-ready.

---

## 2. Objetivo

Criar um **servidor unificado** `apps.server.main` que combine:
- API FastAPI (backend)
- WebUI estático (frontend)
- Logging unificado (estratégia híbrida LOG-001 + LOG-002)
- Ngrok integration (túnel único)

**Comando de inicialização:**
```bash
python -m apps.server.main
```

---

## 3. Escopo

### 3.1 Dentro do Escopo

| Componente | Descrição |
|------------|-----------|
| **Logging Híbrido** | LOG-001 (Uvicorn Config) + LOG-002 (Middleware) |
| **Request Logging** | Access logs com duration_ms, status_code, correlation_id |
| **ColorFormatter** | Logs coloridos por nível e status code |
| **WebUI Estática** | Servida via `/web/` com SPA fallback |
| **Ngrok Unificado** | Túnel único para API + WebUI |
| **Arquivo de Log** | Rotação diária em `workspace/skybridge/logs/{date}.log` |

### 3.2 Fora do Escopo

- ❌ Métricas Prometheus (ver PRD015)
- ❌ Tracing distribuído OpenTelemetry
- ❌ Dashboard Grafana
- ❌ Autenticação/autorização

---

## 4. Requisitos Funcionais

### RF001 — Servidor Unificado
**Prioridade:** P0

Single command que inicia todos os componentes:
```bash
python -m apps.server.main
```

**Critérios:**
- [ ] Configuração centralizada via `.env`
- [ ] Graceful shutdown de todos os componentes
- [ ] Health check em `/api/health`
- [ ] Startup logs informativos

### RF002 — Logging Híbrido
**Prioridade:** P0

**Estratégia:** LOG-001 + LOG-002

| Responsabilidade | Implementação |
|------------------|---------------|
| Startup logs | LOG-001: ColorFormatter via Uvicorn |
| Error logs | LOG-001: FileHandler + Console |
| Access logs | LOG-002: RequestLoggingMiddleware |

**Critérios:**
- [ ] Logs coloridos por nível (INFO, WARNING, ERROR)
- [ ] Status codes com cores dinâmicas (2xx verde, 4xx amarelo, 5xx vermelho)
- [ ] Duration em ms calculado pelo middleware
- [ ] Correlation ID propagado em todos os logs
- [ ] Arquivo rotativo diário em `workspace/skybridge/logs/{date}.log`
- [ ] `access_log=False` no uvicorn.run() (middleware cuida)

#### RF002.1 — Detecção Automática de Log Level (NOVO)
**Prioridade:** P1

Detecção automática do log level baseada na branch Git atual:

| Branch | Log Level | Justificativa |
|--------|-----------|---------------|
| `dev`, `development` | DEBUG | Desenvolvimento detalhado |
| `feature/*`, `poc/*`, `hotfix/*` | DEBUG | Feature development |
| `main`, `release/*` | INFO | Produção/Pré-produção |
| (outras) | DEBUG | Assumindo dev por padrão |

**Critérios:**
- [ ] Detecção automática via `git rev-parse --abbrev-ref HEAD`
- [ ] Override manual via `SKYBRIDGE_LOG_LEVEL` (sempre tem prioridade)
- [ ] Log informativo no startup: `[CONFIG] Branch detected: {branch} → Log level: {level}`

### RF003 — WebUI Estática
**Prioridade:** P1

**⚠️ Importante:** A barra no final (`/web/`) é crítica para SPAs com assets relativos:

| URL | Comportamento | Assets |
|-----|---------------|--------|
| `/web` (sem barra) | ❌ Quebra assets relativos | Resolvem para `/app.js` |
| `/web/` (com barra) | ✅ Funciona corretamente | Resolvem para `/web/app.js` |

**Critérios:**
- [ ] WebUI servida em `/web/` (com barra)
- [ ] Assets estáticos em `/web/assets/`
- [ ] SPA fallback para rotas não encontradas
- [ ] Redirect de `/` para `/web/`
- [ ] Redirect de `/web` para `/web/` (normalização)
- [ ] Configuração Vite com `base: '/web/'`

### RF004 — Integração Ngrok
**Prioridade:** P1

**Critérios:**
- [ ] Túnel único para API + WebUI
- [ ] Suporte a domínio reservado (`NGROK_DOMAIN`)
- [ ] Autenticação via `NGROK_AUTH_TOKEN`
- [ ] Habilitado/desabilitado via `NGROK_ENABLED`
- [ ] Graceful degradation (falha no Ngrok não quebra startup)

---

## 5. Requisitos Não-Funcionais

### NFR001 — Performance
| Métrica | Target | Justificativa |
|---------|--------|---------------|
| Overhead de logging | < 2.1ms | Validado nos PoCs |
| Startup time | < 5s | Experiência do dev |
| Memory footprint | < 150MB | Recursos limitados |

### NFR002 — Observabilidade
**Métricas obrigatórias por request:**
- `status_code`: HTTP status
- `duration_ms`: Tempo de processamento
- `correlation_id`: ID de correlação
- `timestamp`: ISO 8601

### NFR003 — Confiabilidade
- [ ] Logs nunca devem quebrar o servidor
- [ ] Falha no Ngrok não deve impedir startup
- [ ] Arquivo de log com auto-rotação diária

### NFR004 — Usabilidade
- [ ] Logs legíveis em modo DEV
- [ ] Logs estruturados em modo PROD
- [ ] Cores ANSI funcionam em terminais compatíveis

---

## 6. Arquitetura Técnica

### 6.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    apps.server.main                         │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │                 SkybridgeServer                     │    │
│  │                                                     │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │            FastAPI App                        │  │    │
│  │  │                                              │  │    │
│  │  │  Middlewares (ORDEM CRÍTICA):                │  │    │
│  │  │  ┌─────────────────────────────────────────┐ │  │    │
│  │  │  │ 1. CorrelationMiddleware                │ │  │    │
│  │  │  │    └─> x-correlation-id header         │ │  │    │
│  │  │  ├─────────────────────────────────────────┤ │  │    │
│  │  │  │ 2. RequestLoggingMiddleware             │ │  │    │
│  │  │  │    └─> duration, status, correlation    │ │  │    │
│  │  │  ├─────────────────────────────────────────┤ │  │    │
│  │  │  │ 3. CORSMiddleware                       │ │  │    │
│  │  │  └─────────────────────────────────────────┘ │  │    │
│  │  │                                              │  │    │
│  │  │  Routes:                                     │  │    │
│  │  │  ├─ /api/*          → FastAPI endpoints     │  │    │
│  │  │  ├─ /web/assets/*   → Static files          │  │    │
│  │  │  ├─ /web/{path:path} → SPA fallback         │  │    │
│  │  │  └─ /               → Redirect /web/        │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Logging:                                                    │
│  ├─ ColorFormatter (console + arquivo)                       │
│  ├─ uvicorn.run(access_log=False)  ← middleware cuida       │
│  └─ workspace/skybridge/logs/{date}.log                      │
│                                                              │
│  Ngrok:                                                      │
│  └─ pyngrok.connect(port) → túnel único                      │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Estrutura de Arquivos

```
apps/server/
├── __init__.py
└── main.py              ← Servidor unificado (NOVO)

src/runtime/
├── bootstrap/
│   └── app.py           ← Atualizar: adicionar RequestLoggingMiddleware
├── delivery/
│   └── middleware/
│       ├── __init__.py
│       ├── correlation.py   ← Já existe
│       └── request_log.py   ← NOVO
└── observability/
    └── logger.py         ← Atualizar: ColorFormatter com campos estruturados
```

---

## 7. Detalhes de Implementação

### 7.1 Fase 1: Logging (LOG-001 base)

#### 7.1.0 Detecção Automática de Log Level (NOVO)

**Arquivo:** `src/runtime/config/config.py`

**Mapeamento de branch → log level:**
```
dev              → DEBUG (desenvolvimento detalhado)
feature/*        → DEBUG (feature development)
poc/*            → DEBUG (proof of concept)
hotfix/*         → DEBUG (hot fix urgente)
main             → INFO  (produção)
release/*        → INFO  (pré-produção)
(outras)         → DEBUG (assumindo dev por padrão)
```

**Implementação:**
```python
import subprocess
from pathlib import Path

def _detect_current_branch() -> str | None:
    """Detecta automaticamente a branch atual via Git."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return None


def _get_log_level_from_branch(branch: str | None) -> str:
    """Mapeia branch para log level automaticamente."""
    if not branch:
        return "INFO"  # Default conservador

    branch_lower = branch.lower()

    # Dev branches → DEBUG (mais detalhes para desenvolvimento)
    if branch_lower in ("dev", "development"):
        return "DEBUG"
    elif branch_lower.startswith(("feature/", "poc/", "hotfix/")):
        return "DEBUG"

    # Prod branches → INFO (menos ruído em produção)
    elif branch_lower == "main":
        return "INFO"
    elif branch_lower.startswith("release/"):
        return "INFO"

    # Padrão: branches desconhecidas → DEBUG (assumindo dev)
    else:
        return "DEBUG"


def load_config() -> AppConfig:
    """Carrega configuração de environment variables com detecção automática de branch."""
    # Detecta branch automaticamente
    current_branch = _detect_current_branch()
    auto_log_level = _get_log_level_from_branch(current_branch)

    # Prioridade: env var > auto detecção > default
    log_level = os.getenv("SKYBRIDGE_LOG_LEVEL", auto_log_level)

    # Log para debug da detecção
    if current_branch:
        print(f"[CONFIG] Branch detected: {current_branch} → Log level: {log_level}")

    return AppConfig(
        host=os.getenv("SKYBRIDGE_HOST", "0.0.0.0"),
        port=int(os.getenv("SKYBRIDGE_PORT", "8000")),
        log_level=log_level,
        # ... resto da config
    )
```

**Override manual (sempre funciona):**
```bash
# Força DEBUG mesmo em main
SKYBRIDGE_LOG_LEVEL=DEBUG python -m apps.server.main

# Força INFO mesmo em dev
SKYBRIDGE_LOG_LEVEL=INFO python -m apps.server.main
```

#### 7.1.1 Atualizar ColorFormatter

**Arquivo:** `src/runtime/observability/logger.py`

```python
def _get_status_color(self, status: int) -> str:
    """Retorna cor baseada no status code."""
    if 200 <= status < 300:
        return Colors.INFO  # Verde
    elif 400 <= status < 500:
        return Colors.WARNING  # Amarelo
    elif 500 <= status < 600:
        return Colors.ERROR  # Vermelho
    return Colors.RESET

def _format_structured_request(self, record: logging.LogRecord) -> str:
    """Formata request log com campos estruturados."""
    # Implementa formatação com status, duration, correlation_id
```

#### 7.1.2 Criar get_log_config()

**Arquivo:** `apps/server/main.py`

```python
def get_log_config() -> dict:
    """Configuração de logging para uvicorn."""
    logs_dir = Path("workspace/skybridge/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "skybridge": {
                "()": "runtime.observability.logger.ColorFormatter",
            }
        },
        "handlers": {
            "console": {
                "formatter": "skybridge",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "formatter": "skybridge",
                "class": "logging.FileHandler",
                "filename": str(logs_dir / "{date}.log"),
                "encoding": "utf-8",
            }
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": [],  # ← DESABILITADO - middleware cuida
                "level": "INFO",
                "propagate": False,
            },
        }
    }
```

### 7.2 Fase 2: Middleware (LOG-002 base)

#### 7.2.1 Criar RequestLoggingMiddleware

**Arquivo:** `src/runtime/delivery/middleware/request_log.py`

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from time import time
import logging

logger = logging.getLogger("skybridge.request")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para log de requests no formato Skybridge."""

    async def dispatch(self, request: Request, call_next):
        start_time = time()
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            process_time = (time() - start_time) * 1000
            self._log_request(request, status_code, process_time, correlation_id)
            raise

        process_time = (time() - start_time) * 1000
        self._log_request(request, status_code, process_time, correlation_id)

        response.headers["x-process-time"] = f"{process_time:.2f}ms"
        return response

    def _log_request(self, request: Request, status_code: int, process_time: float, correlation_id: str):
        log_record = logging.LogRecord(
            name="skybridge.request",
            level=logging.INFO,
            pathname="", lineno=0,
            msg=f"{request.method} {request.url.path}",
            args=(), exc_info=None,
        )
        log_record.status_code = status_code
        log_record.duration_ms = round(process_time, 2)
        log_record.correlation_id = correlation_id
        logger.handle(log_record)
```

#### 7.2.2 Atualizar Ordem dos Middlewares

**Arquivo:** `src/runtime/bootstrap/app.py`

```python
def _setup_middleware(self):
    """Configura middlewares."""
    from runtime.delivery.middleware.request_log import RequestLoggingMiddleware

    # ORDEM IMPORTA!
    self.app.add_middleware(CorrelationMiddleware)       # 1º
    self.app.add_middleware(RequestLoggingMiddleware)    # 2º
    self.app.add_middleware(CORSMiddleware)              # 3º (último)
```

### 7.3 Fase 3: Frontend Integration

#### 7.3.0 Estratégia de Redirect Automático (NOVO)

**⚠️ CRÍTICO:** A barra no final (`/web/`) é obrigatória para SPAs com assets relativos.

**Por que isso importa?**
```html
<!-- Se usuário acessa /web (sem barra) -->
<script src="./app.js"></script>
<!-- Browser resolve para: http://localhost:8000/app.js ❌ -->

<!-- Se usuário acessa /web/ (com barra) -->
<script src="./app.js"></script>
<!-- Browser resolve para: http://localhost:8000/web/app.js ✅ -->
```

**Fluxo completo de redirects:**
```
/                    → 302 → /web/
/web                 → 302 → /web/ (normalização)
/web/dashboard       → 200  → index.html (SPA routing)
/web/assets/app.js   → 200  → arquivo estático
```

#### 7.3.1 Servir WebUI Estático

**Arquivo:** `apps/server/main.py`

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path

class SkybridgeServer:
    def __init__(self):
        self.skybridge_app = get_app()
        self.app = self.skybridge_app.app
        self._setup_static_routes()

    def _setup_static_routes(self):
        """Configura rotas para servir frontend estático."""
        web_dist = Path(__file__).parent.parent / "web" / "dist"

        if web_dist.exists():
            # Arquivos estáticos
            self.app.mount("/web/assets", StaticFiles(directory=web_dist / "assets"), name="assets")

            # Fallback SPA (apenas para /web/{path:path})
            @self.app.get("/web/{path:path}")
            async def webui_spa(path: str):
                return FileResponse(web_dist / "index.html")

            # ⚠️ IMPORTANTE: Redirect /web → /web/ para normalizar
            @self.app.get("/web")
            async def web_redirect():
                """Normaliza /web para /web/ (barra no final é obrigatória)."""
                return RedirectResponse(url="/web/")
```

#### 7.3.2 Redirect Raiz para WebUI

```python
@app.get("/")
async def root():
    """Redirect raiz para WebUI."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/web/")
```

#### 7.3.3 Configuração Vite (NOVO)

**Arquivo:** `apps/web/vite.config.ts`

```typescript
import { defineConfig } from 'vite'

export default defineConfig({
  base: '/web/',  // ← Com barra no final é obrigatório!
  // ... resto da config
})
```

### 7.4 Fase 4: Ngrok Integration

```python
def main():
    """Ponto de entrada do servidor unificado."""
    config = get_config()
    logger = get_logger(level=config.log_level)

    print_banner("Skybridge Server", __version__)
    logger.info(f"Iniciando Skybridge Server v{__version__}")

    # Ngrok integration
    ngrok_config = load_ngrok_config()
    tunnel_url = None

    if ngrok_config.enabled:
        logger.info("Ngrok habilitado - iniciando túnel...")
        try:
            from pyngrok import ngrok

            if ngrok_config.auth_token:
                ngrok.set_auth_token(ngrok_config.auth_token)

            if ngrok_config.domain:
                tunnel = ngrok.connect(config.port, domain=ngrok_config.domain, bind_tls=True)
            else:
                tunnel = ngrok.connect(config.port)

            tunnel_url = tunnel.public_url
            print_ngrok_urls(tunnel_url, reserved_domain=ngrok_config.domain)
        except Exception as e:
            logger.error("Falha ao iniciar Ngrok", extra={"error": str(e)})

    # Run server com logging customizado
    server = SkybridgeServer()
    server.run(
        host=config.host,
        port=config.port,
        log_config=get_log_config(),
        access_log=False,
    )
```

---

## 8. Planos de Teste

### 8.1 Testes Funcionais

| ID | Cenário | Input | Output Esperado |
|----|---------|-------|-----------------|
| TC-001 | Health Check | `GET /api/health` | 200, log verde |
| TC-002 | Not Found | `GET /api/inexistente` | 404, log amarelo |
| TC-003 | Server Error | `GET /api/error` | 500, log vermelho |
| TC-004 | WebUI Load | `GET /web/` | 200, HTML válido |
| TC-005 | SPA Fallback | `GET /web/dashboard` | 200, index.html |
| TC-006 | Ngrok Tunnel | `GET {tunnel}/api/health` | 200 via túnel |

### 8.2 Testes Não-Funcionais

| ID | Métrica | Método | Target |
|----|---------|--------|--------|
| TNF-001 | Logging overhead | Benchmark | < 2.1ms |
| TNF-002 | Correlation propagation | Trace | 100% propagado |
| TNF-003 | Log rotation | Manual | Arquivo diário criado |

---

## 9. Critérios de Sucesso

### Mínimo Viável (MVP)
- [ ] `python -m apps.server.main` inicia sem erros
- [ ] Logs coloridos funcionando
- [ ] RequestLoggingMiddleware captura todos os requests
- [ ] Status codes com cores corretas (2xx/4xx/5xx)
- [ ] WebUI acessível via `/web/`
- [ ] Arquivo de log criado em `workspace/skybridge/logs/`

### Completo
- [ ] Todos os testes (TC-001 a TC-006) passando
- [ ] Ngrok funcionando com domínio reservado
- [ ] Correlation ID propagado em 100% dos requests
- [ ] Zero warnings no startup
- [ ] Documentação atualizada

---

## 10. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Setup timing de logging | Média | Alto | Configurar ANTES de importar FastAPI |
| Ordem dos middlewares | Baixa | Alto | Documentar ordem correta + testes |
| Overhead performance | Baixa | Médio | Validado nos PoCs (< 2.1ms) |
| Ngrok instability | Média | Baixo | Graceful degradation |

---

## 11. Implementação

### 11.1 Fases

| Fase | Descrição | Estimativa |
|------|-----------|------------|
| F1 | Logging (LOG-001 base) | 2-3h |
| F2 | Middleware (LOG-002 base) | 2-3h |
| F3 | WebUI integration | 1-2h |
| F4 | Ngrok integration | 1h |
| F5 | Validação e testes | 1-2h |
| **Total** | | **7-11h** |

### 11.2 Próximos Passos

1. Explorar estrutura atual de logging (`src/runtime/observability/`)
2. Implementar ColorFormatter atualizado
3. Implementar RequestLoggingMiddleware
4. Criar `apps/server/main.py`
5. Testar todos os cenários
6. Documentar

---

## 12. Relacionamento com Outros PRDs

| PRD | Relação | Descrição |
|-----|---------|-----------|
| **PRD002** | Evolui | Health endpoint será mantido |
| **PRD014** | Complementa | WebUI Dashboard servida pelo novo servidor |
| **PRD015** | Independente | Métricas Prometheus (fase futura) |
| **PRD017** | Independente | Mensageria standalone não é afetada |

---

## 13. Referências

### PoCs Relacionados
- **LOG-001:** `workspace/skybridge/pocs/logs/log-001/` — Uvicorn Log Config
- **LOG-002:** `workspace/skybridge/pocs/logs/log-002/` — Middleware Request Logging
- **RELATÓRIO:** `workspace/skybridge/pocs/logs/RELATORIO-CONSOLIDADO.md`

### Documentação Relacionada
- **PLAN.md:** Plano detalhado de implementação
- **PB002:** Documentação Ngrok

---

## 14. Histórico de Mudanças

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-01-26 | Sky | Criação inicial do PRD |
| 1.1 | 2026-01-26 | Sky | Adiciona RF002.1: Detecção automática de log level por branch |
| 1.1 | 2026-01-26 | Sky | Adiciona seção 7.1.0: Implementação de detecção de branch |
| 1.1 | 2026-01-26 | Sky | Atualiza RF003: Estratégia de redirect /web → /web/ |
| 1.1 | 2026-01-26 | Sky | Adiciona seção 7.3.0: Estratégia de redirect automático |
| 1.1 | 2026-01-26 | Sky | Adiciona seção 7.3.3: Configuração Vite com base: '/web/' |

---

> "A simplicidade é o último grau de sofisticação." – made by Sky 🚀
