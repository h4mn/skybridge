# PLANO — Servidor Unificado apps.server.main

**Branch:** `feature/server-main`
**Worktree:** `B:\_repositorios\skybridge-workspace\server-main`
**Data:** 2026-01-26
**Baseado em:** PoCs LOG-001, LOG-002, LOG-003, LOG-004

---

## 📊 Resumo Executivo

Este documento consolida a análise de 4 PoCs de logging e define o plano de implementação do servidor unificado `apps.server.main`, que combinará:
- API FastAPI (backend)
- WebUI estático (frontend)
- Logging unificado (estratégia híbrida)
- Ngrok integration (túnel único)

---

## 🎯 Decisão Arquitetural

### Estratégia de Logging: **HÍBRIDA (LOG-001 + LOG-002)**

```
┌─────────────────────────────────────────────────────────┐
│                   apps.server.main                       │
│                                                           │
│  1️⃣ LOG-001: Uvicorn Log Config                          │
│     ├─ Startup logs → ColorFormatter                     │
│     ├─ Error logs → ColorFormatter                       │
│     └─ Arquivo rotativo → FileHandler                    │
│                                                           │
│  2️⃣ LOG-002: Middleware Request Logging                  │
│     ├─ Access logs → RequestLoggingMiddleware            │
│     ├─ duration_ms → Calculado pelo middleware           │
│     ├─ correlation_id → Do CorrelationMiddleware          │
│     └─ status color → Dinâmico por range                │
│                                                           │
│  uvicorn.run(access_log=False)  # Middleware cuida       │
└─────────────────────────────────────────────────────────┘
```

### Por Que Híbrida?

| Componente | Responsabilidade |
|------------|-----------------|
| **LOG-001** | Startup logs, error logs, configuração uvicorn |
| **LOG-002** | Access logs com duration, correlation_id |

---

## 📋 Matriz de Resultados dos PoCs

| PoC | Estratégia | DoD | Complexidade | Veredito |
|-----|-----------|-----|--------------|----------|
| **LOG-001** | Uvicorn Log Config | ✅ 100% | ⭐ Baixa | ✅ **ADOTAR** |
| **LOG-002** | Middleware Request Logging | ✅ 100% | ⭐⭐ Média | ✅ **ADOTAR** |
| **LOG-003** | Custom Log Filter | ✅ 100% | ⭐⭐⭐ Alta | ⚠️ Opcional |
| **LOG-004** | Stdout Interceptor | ⚠️ 60% | ⭐⭐⭐⭐ M.Alta | ❌ Descartar |

---

## 🔧 Implementação

### Fase 1: Logging (Base LOG-001)

#### 1.0 ⚠️ DETECÇÃO AUTOMÁTICA DE LOG LEVEL (NOVO)

**AGENTE OBSERVAR:** Implementar detecção automática de branch para definir log level.

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

**Arquivo:** `src/runtime/config/config.py`

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
SKYBRIDGE_LOG_LEVEL=DEBUG

# Força INFO mesmo em dev
SKYBRIDGE_LOG_LEVEL=INFO
```

#### 1.1 Atualizar ColorFormatter

**Arquivo:** `src/runtime/observability/logger.py`

**Adicionar:**
```python
def _parse_access_log(self, message: str) -> str:
    """Parseia access log do uvicorn."""
    pattern = r'"(\w+)\s+(\S+)\s+[^"]+"\s+(\d+)'
    match = re.search(pattern, message)
    if match:
        method, path, status = match.groups()
        status_color = self._get_status_color(int(status))
        return f"{method} {path} | {Colors.DIM}status:{Colors.RESET} {status_color}{status}{Colors.RESET}"
    return message

def _get_status_color(self, status: int) -> str:
    """Retorna cor baseada no status code."""
    if 200 <= status < 300:
        return Colors.INFO
    elif 400 <= status < 500:
        return Colors.WARNING
    elif 500 <= status < 600:
        return Colors.ERROR
    return Colors.RESET
```

#### 1.3 Criar get_log_config()

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
                "handlers": [],  # DESABILITADO - middleware cuida
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
        }
    }
```

---

### Fase 2: Middleware (Base LOG-002)

#### 2.1 Criar RequestLoggingMiddleware

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

#### 2.2 Atualizar Ordem dos Middlewares

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

---

### Fase 3: Frontend Integration

#### 3.0 ⚠️ ESTRATÉGIA DE REDIRECT AUTOMÁTICO (IMPORTANTE)

**AGENTE OBSERVAR:** A barra no final (`/web/`) é crítica para SPAs com assets relativos.

```
/web  (sem barra)  → Assets relativos quebram ❌
/web/ (com barra)  → Assets relativos funcionam ✅
```

**Por que?**
```html
<!-- Se usuário acessa /web (sem barra) -->
<script src="./app.js"></script>
<!-- Browser resolve para: http://localhost:8000/app.js ❌ -->

<!-- Se usuário acessa /web/ (com barra) -->
<script src="./app.js"></script>
<!-- Browser resolve para: http://localhost:8000/web/app.js ✅ -->
```

**Solução: Redirect automático para normalizar**
```python
# Sempre redirecionar /web → /web/
@app.get("/web")
async def web_no_slash():
    return RedirectResponse(url="/web/")
```

#### 3.1 Servir WebUI Estático

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

#### 3.2 Redirect Raiz para WebUI

```python
@app.get("/")
async def root():
    """Redirect raiz para WebUI."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/web/")
```

**Fluxo completo de redirects:**
```
/                    → 302 → /web/
/web                → 302 → /web/
/web/dashbord       → 200  → index.html (SPA routing)
/web/assets/app.js  → 200  → arquivo estático
```

#### 3.3 Configuração Vite

```typescript
// apps/web/vite.config.ts
export default defineConfig({
  base: '/web/',  // ← Com barra no final!
})
```

---

### Fase 4: Ngrok Integration

#### 4.1 Mover Lógica do Ngrok

**Arquivo:** `apps/server/main.py`

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
        log_config=get_log_config(),  # ← LOG-001
        access_log=False,             # ← LOG-002
    )
```

---

### Fase 5: Atualizar ColorFormatter para Middleware

#### 5.1 Suporte a Campos Estruturados

**Arquivo:** `src/runtime/observability/logger.py`

```python
def format(self, record: logging.LogRecord) -> str:
    """Formata record com cores."""

    # Detecta campos estruturados do middleware
    if hasattr(record, "status_code"):
        return self._format_structured_request(record)

    # Detecta access log do uvicorn
    if record.name == "uvicorn.access":
        message = self._parse_access_log(record.getMessage())
    else:
        message = record.getMessage()

    # ... resto do código existente

def _format_structured_request(self, record: logging.LogRecord) -> str:
    """Formata request log com campos estruturados."""
    reset = Colors.RESET

    timestamp = f"{Colors.DIM}{self.formatTime(record, self.DATE_FORMAT)}{reset}"

    level_color = self.LEVEL_COLORS.get(record.levelno, "")
    levelname = f"{level_color}{record.levelname}{reset}"

    name = f"{Colors.BLUE}{record.name}{reset}"

    # Status com cor
    status = getattr(record, "status_code", 0)
    status_color = self._get_status_color(status)

    # Duration
    duration = getattr(record, "duration_ms", 0)

    # Correlation ID
    correlation = getattr(record, "correlation_id", "N/A")

    return (
        f"{timestamp}{Colors.PIPE} |{reset} "
        f"{levelname:<8}{Colors.PIPE} |{reset} "
        f"{name}{Colors.PIPE} |{reset} "
        f"{record.msg} "
        f"| {Colors.DIM}status:{Colors.RESET} {status_color}{status}{Colors.RESET} "
        f"| {Colors.DIM}duration:{Colors.RESET} {duration}ms "
        f"| {Colors.DIM}correlation:{Colors.RESET} {correlation}"
    )
```

---

## 📁 Estrutura de Arquivos

```
apps/server/
├── __init__.py
└── main.py              ← Servidor unificado (novo)

src/runtime/
├── bootstrap/
│   └── app.py           ← Adicionar RequestLoggingMiddleware
├── delivery/
│   └── middleware/
│       ├── __init__.py
│       ├── request_log.py  ← Novo middleware
│       └── ...           ← CorrelationMiddleware existe
└── observability/
    └── logger.py         ← Atualizar ColorFormatter
```

---

## ⚠️ Armadilhas a Evitar

| Armadilha | Solução |
|-----------|----------|
| Setup timing errado | Configurar logging **ANTES** de importar FastAPI |
| `handlers = []` falha | Usar `handlers.clear()` |
| Duplicação de logs | Setar `propagate=False` |
| Ordem dos middlewares | Correlation → RequestLogging → CORS |
| Access log duplicado | `access_log=False` no uvicorn.run() |

---

## 🧪 Testes de Validação

### Teste 1: Health Check (200)
```bash
curl http://localhost:8000/api/health
# Esperado: status: 200 verde
```

### Teste 2: Not Found (404)
```bash
curl http://localhost:8000/api/inexistente
# Esperado: status: 404 amarelo
```

### Teste 3: Server Error (500)
```bash
curl http://localhost:8000/api/error
# Esperado: status: 500 vermelho
```

### Teste 4: WebUI
```bash
curl http://localhost:8000/web/
# Esperado: SPA carrega
```

### Teste 5: Ngrok
```bash
# Com NGROK_ENABLED=true
curl https://seu-dominio.ngrok-free.app/api/health
# Esperado: funcionando via túnel
```

---

## 📊 Performance Impact Estimado

| Componente | Overhead | Justificativa |
|------------|----------|---------------|
| ColorFormatter | ~0.1ms | Só formatação |
| RequestLoggingMiddleware | ~1-2ms | Mede tempo + LogRecord |
| **Total** | **~1.2-2.1ms** | Aceitável |

---

## 📚 Referências dos PoCs

- **LOG-001:** `workspace/skybridge/pocs/logs/log-001/`
- **LOG-002:** `workspace/skybridge/pocs/logs/log-002/`
- **Relatório:** `workspace/skybridge/pocs/logs/RELATORIO-CONSOLIDADO.md`

---

## ✅ Checklist de Implementação

### Fase 1: Logging
- [ ] Atualizar ColorFormatter com _parse_access_log()
- [ ] Atualizar ColorFormatter com _get_status_color()
- [ ] Atualizar ColorFormatter com _format_structured_request()
- [ ] Criar get_log_config() em apps/server/main.py

### Fase 2: Middleware
- [ ] Criar RequestLoggingMiddleware
- [ ] Atualizar _setup_middleware() no bootstrap
- [ ] Testar ordem dos middlewares

### Fase 3: WebUI
- [ ] Criar _setup_static_routes()
- [ ] Criar redirect raiz para /web/
- [ ] Testar SPA fallback

### Fase 4: Ngrok
- [ ] Mover lógica ngrok para server/main.py
- [ ] Testar túnel único
- [ ] Testar domínio reservado

### Fase 5: Validação
- [ ] Teste 200 (verde)
- [ ] Teste 404 (amarelo)
- [ ] Teste 500 (vermelho)
- [ ] Teste WebUI
- [ ] Teste Ngrok

---

> "A simplicidade é o último grau de sofisticação." – made by Sky 🚀
