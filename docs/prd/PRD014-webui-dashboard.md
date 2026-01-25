# PRD014: Skybridge WebUI - Dashboard de Monitoramento

**Status:** 🚧 Em Elaboração
**Data:** 2026-01-11
**Autor:** Sky
**Versão:** 1.2

---

## Status de Implementação

### Fase 0: Definição (Semana 1) - 🚧 EM PROGRESSO

- [x] Análise de arquitetura existente (FastAPI, CORS, middlewares)
- [x] Levantamento de endpoints disponíveis para UI
- [x] **Decisão de stack: React + Bootstrap UI + Vite** ✅
- [x] Estrutura de diretórios (`apps/web/main.py`)
- [x] Definição de comunicação (axios, SSE, static files)
- [ ] Especificação de componentes UI
- [ ] Mockup de telas principais
- [ ] Definição de endpoints adicionais necessários

---

## 1. Executivo Resumido

### Problema

Atualmente, o monitoramento do sistema de webhook agents (PRD013) é feito **apenas via linha de comando**:

```bash
# Para ver logs
tail -f workspace/skybridge/logs/$(date +%Y-%m-%d).log

# Para ver worktrees
find worktrees -name "agent.log" -exec cat {} \;

# Para ver snapshots
find worktrees -name "snapshot.json" -exec cat {} \;
```

**Limitações:**
- Não existe visão consolidada do sistema
- Logs são espalhados em múltiplos arquivos
- Impossível acompanhar em tempo real sem SSH
- Sem histórico visual de execuções
- Sem alertas visuais de falhas
- Sem dashboard de métricas

### Solução

**Skybridge WebUI** - Dashboard web para monitoramento em tempo real do sistema de webhook agents.

**Princípios:**
1. **Fachada separada:** `apps/web/main.py` (similar a `apps/api/main.py`)
2. **Processo independente:** Terminal próprio com logs dedicados
3. **Compartilhamento de infra:** Usa mesma API FastAPI (axios + static)
4. **Real-time:** Server-Sent Events (SSE) para logs/streaming
5. **Debug mode:** Vite com HMR e logs detalhados

### Proposta de Valor

| Benefício | Antes (CLI) | Depois (WebUI) |
|-----------|-------------|----------------|
| Visibilidade | Logs espalhados | Dashboard consolidado |
| Tempo real | `tail -f` manual | Streaming automático |
| Histórico | Grep em arquivos | Busca visual + filtros |
| Alertas | Sem alertas | Notificações visuais |
| Acesso | SSH obrigatório | Browser qualquer lugar |
| Métricas | Manual | Gráficos + tabelas |

### Success Metrics

- **Mês 1:** 80% dos monitoramentos via WebUI (vs CLI)
- **Mês 1:** <5s para detectar problema (vs minutos/horas)
- **Mês 3:** Expansão para mobile-responsive
- **Mês 6:** <1s latência de updates (SSE otimizado)

---

## 2. Contexto e Problema

### Dor Atual

```
┌─────────────────────────────────────────────────────────────────┐
│  Fluxo de Monitoramento Manual (Lento e Propenso a Erros)      │
│                                                                   │
│  1. Desenvolvedor abre terminal SSH                              │
│  2. Navega até diretório de logs                                 │
│  3. Executa tail -f no log do dia                               │
│  4. Fica monitorando manualmente                                 │
│  5. Webhook chega (sem aviso)                                    │
│  6. Procura job_id no log                                       │
│  7. Navega até worktree específico                              │
│  8. Lê .sky/agent.log                                           │
│  9. Lê .sky/snapshot.json                                       │
│  10. Verifica se há erros                                        │
│                                                                   │
│  Tempo médio: 5-10 minutos por evento                           │
│  Foco perdido: Sim (context switch constante)                   │
└───────────────────────────────────────────────────────────────────┘
```

### Problemas Específicos

| Problema | Frequência | Impacto |
|----------|-----------|---------|
| Não sei quando webhook chega | Sempre | Alta |
| Worktrees sujos acumulam | Diário | Alta |
| Logs difíceis de filtrar | Sempre | Média |
| Sem visão histórica | Sempre | Média |
| Impossível monitorar remotamente | Sempre | Baixa |

### Persona Principal

**Nome:** DevOps Maintainer
**Meta:** Monitorar sistema sem perder foco no desenvolvimento
**Frustrações:**
- "Tenho que ficar com tail -f aberto o dia todo"
- "Perco webhooks quando estou em reunião"
- "Descubro worktree sujo dias depois"
- "Sem dashboards, só logs brutos"

---

## 3. Solução Proposta

### Visão Arquitetural

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TERMINAL 1 (Backend API)                             │
│  python apps/api/main.py                                                        │
│  → FastAPI na porta 8000                                                        │
│  → /health, /discover, /webhooks/{source}                                      │
│  → /webhooks/jobs, /webhooks/worktrees (novos)                                 │
│  → /observability/logs/stream (SSE)                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP/JSON
                                      │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TERMINAL 2 (Frontend Web)                            │
│  python apps/web/main.py                                                        │
│  → Vite dev server na porta 5173                                                │
│  → HMR (Hot Module Replacement)                                                 │
│  → Debug mode ativado                                                           │
│  → Próprio logger com prefixo [WEBUI]                                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Browser
                                      │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              BROWSER (http://localhost:5173)                   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         HEADER (Bootstrap Navbar)                      │   │
│  │  [Skybridge] [Dashboard] [Worktrees] [Logs] [Settings]                │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ API Status    │  │ Active Jobs   │  │ Worktrees     │  │ Success Rate  │   │
│  │ ONLINE (✅)    │  │ 3 processing  │  │ 12 ativos     │  │ 94.5%         │   │
│  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         REAL-TIME LOGS (SSE)                           │   │
│  │  [14:30:15] INFO  webhook-github-issues-225-cf560ba0 created           │   │
│  │  [14:30:16] INFO  worktree skybridge-github-225-abc123 created          │   │
│  │  [14:30:17] DEBUG agent spawned with skill resolve-issue                │   │
│  │  [14:30:18] INFO  Agent: Analyzing issue #225...                       │   │
│  │  [14:30:20] DEBUG Reading src/skybridge/core/__init__.py...            │   │
│  │  [14:30:45] INFO  Agent: Implementing fix...                            │   │
│  │  [14:31:30] INFO  Agent: Running tests...                               │   │
│  │  [14:31:45] SUCCESS Issue resolved, PR #226 created                    │   │
│  │  [14:31:46] INFO  Worktree validated, cleanup scheduled                │   │
│  │  ▼ Auto-scroll enabled                                                  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         ACTIVE WORKTREES TABLE                          │   │
│  │  ┌──────────────────┬─────────────┬──────────┬──────────────┬────────┐ │   │
│  │  │ Worktree         │ Job ID      │ Status   │ Created      │ Actions│ │   │
│  │  ├──────────────────┼─────────────┼──────────┼──────────────┼────────┤ │   │
│  │  │ skybridge-github-│ abc123      │ RUNNING  │ 2 min ago    │ [View] │ │   │
│  │  │ issues-225-abc123│             │          │              │        │ │   │
│  │  ├──────────────────┼─────────────┼──────────┼──────────────┼────────┤ │   │
│  │  │ skybridge-github-│ def456      │ COMPLETED│ 15 min ago   │[Clean] │ │   │
│  │  │ issues-224-def456│             │          │              │        │ │   │
│  │  └──────────────────┴─────────────┴──────────┴──────────────┴────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados (Real-time)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FLUXO DE DADOS REAL-TIME                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  1. Webhook chega                                                               │
│     POST /webhooks/github                                                       │
│     ↓                                                                           │
│  2. Job enfileirado                                                             │
│     job_queue.append(job)                                                       │
│     ↓                                                                           │
│  3. Worker processa                                                             │
│     job_orchestrator.execute(job)                                              │
│     ↓                                                                           │
│  4. Logger escreve (JSON estruturado)                                          │
│     logger.info("Agent spawned", extra={"job_id": "abc123"})                   │
│     ↓                                                                           │
│  5. SSE endpoint lê linha                                                       │
│     GET /observability/logs/stream → SSE stream                                 │
│     ↓                                                                           │
│  6. Frontend recebe evento                                                      │
│     eventSource.onmessage = (e) => appendLog(e.data)                            │
│     ↓                                                                           │
│  7. Tabela atualizada automaticamente                                          │
│     worktreesTable.refresh()                                                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Convenção de Nomes de Artefatos

### Estrutura de Diretórios

```
skybridge/
├── apps/
│   ├── api/
│   │   └── main.py              # Backend API (existente)
│   └── web/
│       ├── main.py              # Fachada frontend (NOVO)
│       ├── package.json         # Dependências Node
│       ├── vite.config.ts       # Config Vite
│       ├── tsconfig.json        # Config TypeScript
│       ├── index.html           # Entry HTML
│       └── src/
│           ├── main.tsx         # Entry React
│           ├── App.tsx          # Componente principal
│           ├── api/
│           │   ├── client.ts     # Axios HTTP client
│           │   └── endpoints.ts  # API endpoints
│           ├── components/
│           │   ├── Header.tsx
│           │   ├── LogStream.tsx
│           │   ├── WorktreeTable.tsx
│           │   └── MetricCard.tsx
│           ├── pages/
│           │   ├── Dashboard.tsx
│           │   ├── Worktrees.tsx
│           │   ├── Logs.tsx
│           │   └── Settings.tsx
│           └── styles/
│               └── main.css     # Custom CSS (Bootstrap override)
│
├── src/skybridge/
│   ├── platform/
│   │   ├── bootstrap/
│   │   │   └── app.py          # Adicionar StaticFiles para /webui
│   │   └── delivery/
│   │       └── routes.py       # Adicionar endpoints UI
│   └── web/
│       ├── __init__.py
│       ├── facade.py           # Fachada de execução do frontend
│       └── logger.py           # Logger dedicado [WEBUI]
│
└── static/
    └── webui/
        └── build/              # Frontend buildado (produção)
```

### Fachada Frontend (`apps/web/main.py`)

Similar a `apps/api/main.py`:

```python
"""
WebUI App — Thin adapter para interface web.

Ponto de entrada da aplicação Skybridge WebUI (Dashboard).
"""

import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from skybridge.platform.config.config import get_config
from skybridge.platform.observability.logger import get_logger, print_banner, Colors
from skybridge import __version__


def main():
    """Ponto de entrada do WebUI."""
    config = get_config()

    # Logger dedicado com prefixo [WEBUI]
    logger = get_logger(level="DEBUG")  # Sempre DEBUG em desenvolvimento

    # Banner específico
    print_banner("Skybridge WebUI", __version__)
    print()
    logger.info(f"Iniciando {Colors.WHITE}WebUI{Colors.RESET} em modo DEBUG")
    logger.info(f"API URL: {Colors.CYAN}http://{config.host}:{config.port}{Colors.RESET}")

    # Executa Vite dev server
    frontend_dir = Path(__file__).parent
    vite_cmd = ["npm", "run", "dev"]

    logger.debug(f"Executando Vite: {' '.join(vite_cmd)}", extra={
        "cwd": str(frontend_dir),
        "port": 5173
    })

    try:
        subprocess.run(vite_cmd, cwd=frontend_dir, check=True)
    except KeyboardInterrupt:
        logger.info(f"{Colors.WHITE}WebUI{Colors.RESET} encerrado pelo usuário")
    except subprocess.CalledProcessError as e:
        logger.error(f"Vite falhou: {e}")


if __name__ == "__main__":
    main()
```

---

## 5. Requisitos Funcionais

### RF001: Dashboard Principal com Métricas
- **Descrição:** Tela inicial com cards de métricas principais
- **Métricas:**
  - API Status (online/offline)
  - Active Jobs (fila + processando)
  - Worktrees ativos (count)
  - Success Rate (últimas 24h)
- **Atualização:** Polling a cada 5s (ou SSE quando disponível)
- **Prioridade:** Alta

### RF002: Tabela de Worktrees Ativos
- **Descrição:** Tabela listando todos os worktrees com ações
- **Colunas:**
  - Worktree name
  - Job ID
  - Status (RUNNING, COMPLETED, FAILED, TIMED_OUT)
  - Created at (tempo relativo: "2 min ago")
  - Actions (View logs, Clean up, Keep)
- **Ações:**
  - **View:** Abre modal com agent.log + snapshot.json
  - **Clean:** Remove worktree (com confirmação)
  - **Keep:** Marca para não limpar automaticamente
- **Atualização:** Real-time via SSE
- **Prioridade:** Alta

### RF003: Streaming de Logs em Tempo Real
- **Descrição:** Painel de logs com streaming via SSE
- **Features:**
  - Auto-scroll (toggleável)
  - Filtros por nível (DEBUG, INFO, WARNING, ERROR)
  - Busca full-text
  - Highlight por nível (cores)
  - Cópia de linha individual
- **Endpoint:** `GET /observability/logs/stream` (SSE)
- **Prioridade:** Alta

### RF004: Detalhes de Worktree (Modal)
- **Descrição:** Modal com detalhes completos de um worktree
- **Abas:**
  - **Agent Log:** Conteúdo de `.sky/agent.log`
  - **Snapshot:** `.sky/snapshot.json` (diff visual)
  - **Thinking Steps:** Passos de raciocínio do agente
  - **Files Changed:** Lista de arquivos modificados/criados/deletados
- **Prioridade:** Média

### RF005: Busca e Filtros Históricos
- **Descrição:** Tela de busca em logs históricos
- **Filtros:**
  - Período (date range picker)
  - Source (GitHub, Discord, etc)
  - Event type (issues.opened, etc)
  - Status (success, failed, timeout)
  - Job ID (busca exata)
- **Resultado:** Tabela com links para worktrees
- **Prioridade:** Média

### RF006: Configuração de Webhooks
- **Descrição:** Tela para configurar webhooks sem editar .env
- **Campos:**
  - GitHub secret (masked)
  - Enabled sources (checkboxes)
  - Worktree base path
  - Claude Code CLI path
- **Ação:** Salvar (recomenda reload do worker)
- **Prioridade:** Baixa

### RF007: Handler Discovery UI
- **Descrição:** Interface visual para `/discover`
- **Features:**
  - Lista de todos os handlers
  - Filtros por kind (query, command)
  - Detalhes de input/output schemas
  - Test interativo (enviar request)
- **Prioridade:** Baixa

### RF008: Dark Mode Toggle
- **Descrição:** Alternar entre tema claro e escuro
- **Implementação:** Bootstrap dark mode + toggle no Header
- **Persistência:** localStorage
- **Prioridade:** Baixa

---

## 6. Requisitos Não-Funcionais

### RNF001: Independência de Processos
- **Descrição:** Frontend deve rodar em processo separado do backend
- **Implementação:** `python apps/web/main.py` inicia Vite dev server
- **Benefício:** Logs separados, restart independente
- **Prioridade:** Alta

### RNF002: Debug Mode Sempre Ativo (Dev)
- **Descrição:** Em desenvolvimento, Vite deve rodar com logs detalhados
- **Implementação:** `VITE_DEBUG=true` no `.env`
- **Logs:** Prefixo `[WEBUI]` em todas as mensagens
- **Prioridade:** Alta

### RNF003: Comunicação via Axios
- **Descrição:** Usar axios para todas as chamadas HTTP
- **Features:**
  - Interceptor para correlation_id
  - Interceptor para auth (se necessário)
  - Tratamento unificado de erros
  - Timeout configurável
- **Prioridade:** Alta

### RNF004: Server-Sent Events (SSE)
- **Descrição:** Usar SSE para streaming de logs e updates
- **Endpoints:**
  - `/observability/logs/stream` - Logs em tempo real
  - `/webhooks/jobs/stream` - Updates de jobs (opcional)
- **Reconexão:** Automática com backoff exponencial
- **Prioridade:** Alta

### RNF005: Responsividade Mobile
- **Descrição:** UI deve funcionar em mobile (>=375px)
- **Implementação:** Bootstrap grid + breakpoints
- **Limitações:** Tabelas podem ter scroll horizontal
- **Prioridade:** Média

### RNF006: Performance
- **Descrição:** Carregamento inicial <2s, updates <100ms
- **Implementação:**
  - Code splitting por rota
  - Lazy loading de componentes
  - Cache de responses (axios)
- **Prioridade:** Média

### RNF007: Acessibilidade
- **Descrição:** Seguir WCAG 2.1 AA
- **Implementação:**
  - ARIA labels em botões/inputs
  - Navegação por teclado
  - Contraste adequado
- **Prioridade:** Baixa

---

## 7. Endpoints API Necessários

### Endpoints Existentes (Reutilizar)

```
GET  /health           # API status
GET  /discover         # Handler discovery
GET  /discover/{method}  # Handler details
```

### Novos Endpoints (Backend)

```python
# src/skybridge/platform/delivery/routes.py (adicionar)

@router.get("/webhooks/jobs")
async def list_webhook_jobs():
    """Lista todos os jobs de webhook."""
    from skybridge.core.contexts.webhooks.application.handlers import get_job_queue
    job_queue = get_job_queue()
    return {
        "jobs": [
            {
                "job_id": job.id,
                "source": job.source,
                "event_type": job.event_type,
                "status": job.status.value,  # PENDING, PROCESSING, COMPLETED, FAILED
                "created_at": job.created_at.isoformat(),
                "worktree_path": job.worktree_path,
            }
            for job in job_queue.get_all_jobs()
        ]
    }

@router.get("/webhooks/worktrees")
async def list_worktrees():
    """Lista todos os worktrees ativos."""
    from pathlib import Path
    from skybridge.platform.config.config import get_webhook_config

    config = get_webhook_config()
    worktrees_path = Path(config.worktree_base_path)

    worktrees = []
    if worktrees_path.exists():
        for item in worktrees_path.iterdir():
            if item.is_dir() and item.name.startswith("skybridge-github-"):
                # Lê snapshot se existir
                snapshot_path = item / ".sky" / "snapshot.json"
                snapshot = None
                if snapshot_path.exists():
                    import json
                    snapshot = json.loads(snapshot_path.read_text())

                worktrees.append({
                    "name": item.name,
                    "path": str(item),
                    "snapshot": snapshot,
                })

    return {"worktrees": worktrees}

@router.get("/webhooks/worktrees/{worktree_name}")
async def get_worktree_details(worktree_name: str):
    """Retorna detalhes completos de um worktree."""
    from pathlib import Path
    from skybridge.platform.config.config import get_webhook_config
    import json

    config = get_webhook_config()
    worktree_path = Path(config.worktree_base_path) / worktree_name

    if not worktree_path.exists():
        raise HTTPException(404, f"Worktree not found: {worktree_name}")

    # Lê agent log
    agent_log_path = worktree_path / ".sky" / "agent.log"
    agent_log = None
    if agent_log_path.exists():
        agent_log = agent_log_path.read_text(encoding="utf-8")

    # Lê snapshot
    snapshot_path = worktree_path / ".sky" / "snapshot.json"
    snapshot = None
    if snapshot_path.exists():
        snapshot = json.loads(snapshot_path.read_text())

    return {
        "name": worktree_name,
        "path": str(worktree_path),
        "agent_log": agent_log,
        "snapshot": snapshot,
    }

@router.delete("/webhooks/worktrees/{worktree_name}")
async def delete_worktree(worktree_name: str):
    """Remove um worktree."""
    from pathlib import Path
    from skybridge.platform.config.config import get_webhook_config

    config = get_webhook_config()
    worktree_path = Path(config.worktree_base_path) / worktree_name

    if not worktree_path.exists():
        raise HTTPException(404, f"Worktree not found: {worktree_name}")

    # Remove worktree
    import subprocess
    subprocess.run(["git", "worktree", "remove", str(worktree_path)], check=True)

    return {"ok": True, "message": f"Worktree {worktree_name} removed"}

@router.get("/observability/logs")
async def get_logs(tail: int = 100, level: str | None = None):
    """Retorna logs recentes (com filtros)."""
    from pathlib import Path
    from datetime import datetime

    log_file = Path("workspace/skybridge/logs") / f"{datetime.now():%Y-%m-%d}.log"

    if not log_file.exists():
        return {"lines": []}

    lines = log_file.read_text(encoding="utf-8").splitlines()

    # Filtra por nível se especificado
    if level:
        lines = [l for l in lines if f"[{level.upper()}]" in l]

    return {"lines": lines[-tail:]}

@router.get("/observability/logs/stream")
async def stream_logs():
    """Stream logs em tempo real via SSE."""
    from fastapi.responses import StreamingResponse
    import asyncio

    async def log_generator():
        """Gerador que lê novas linhas do log."""
        from pathlib import Path
        from datetime import datetime
        import time

        log_file = Path("workspace/skybridge/logs") / f"{datetime.now():%Y-%m-%d}.log"
        last_position = 0

        if log_file.exists():
            last_position = log_file.stat().st_size

        while True:
            if log_file.exists():
                current_size = log_file.stat().st_size

                if current_size > last_position:
                    # Lê novas linhas
                    with open(log_file, "rb") as f:
                        f.seek(last_position)
                        new_lines = f.read().decode("utf-8")

                    for line in new_lines.splitlines():
                        if line.strip():
                            yield f"data: {line}\n\n"

                    last_position = current_size

            await asyncio.sleep(0.5)  # Poll a cada 500ms

    return StreamingResponse(log_generator(), media_type="text/event-stream")
```

---

## 8. Stack Técnica

### Frontend

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **React** | 18.3+ | Maduro, ecosystem rico |
| **TypeScript** | 5.7+ | Type safety, DX |
| **Vite** | 6.0+ | Dev server rápido, HMR |
| **React Bootstrap** | 2.10+ | Componentes Bootstrap para React |
| **Bootstrap** | 5.3+ | UI framework |
| **Axios** | 1.7+ | HTTP client |
| **React Router** | 6.22+ | Client-side routing |
| **React Query** | 5.28+ | Server state, cache, polling |
| **Date-fns** | 3.3+ | Manipulação de datas |

### Dependências (package.json)

```json
{
  "name": "skybridge-webui",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --debug",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.22.0",
    "react-bootstrap": "^2.10.5",
    "bootstrap": "^5.3.3",
    "axios": "^1.7.9",
    "@tanstack/react-query": "^5.28.0",
    "date-fns": "^3.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.7.2",
    "vite": "^6.0.11",
    "eslint": "^8.57.0"
  }
}
```

### Decisão de Stack: React

**Escolha:** React foi selecionado como framework frontend.

**Justificativa:**
- **Ecosystem maior:** Maior variedade de bibliotecas e componentes
- **Comunidade ativa:** Maior base de usuários para suporte
- **React Bootstrap:** Integração madura com Bootstrap 5
- **React Query:** Solução robusta para server state, cache e polling
- **Compatibilidade:** Melhor integração com ferramentas existentes no ecossistema

**Alternativas consideradas:**
- Vue 3 (descartado: ecosystem menor, apesar de learning curve mais suave)

---

## 9. Casos de Uso

### UC001: Monitoramento em Tempo Real

**Ator:** DevOps Maintainer
**Pré-condições:** WebUI aberta no browser
**Fluxo Principal:**
1. Usuário abre `http://localhost:5173`
2. Dashboard carrega com métricas atuais
3. Log stream começa a receber eventos via SSE
4. Webhook chega
5. Novo log aparece automaticamente (auto-scroll)
6. Card "Active Jobs" incrementa
7. Linha na tabela "Worktrees" aparece (status: RUNNING)
8. Agente completa
9. Status muda para COMPLETED
10. Linha fica verde (success color)

**Pós-condições:** Usuário viu tudo em tempo real
**Alternativas:**
- 4a: Webhook falha → Linha fica vermelha (error color)

### UC002: Investigação de Worktree

**Ator:** DevOps Maintainer
**Pré-condições:** Worktree suspeito na tabela
**Fluxo Principal:**
1. Usuário clica "View" em worktree
2. Modal abre com abas
3. Aba "Agent Log" mostra execuções
4. Aba "Thinking Steps" mostra raciocínio
5. Aba "Files Changed" mostra diff
6. Usuário identifica problema
7. Usuário clica "Keep" (para investigar depois)

**Pós-condições:** Worktree preservado, problema entendido

### UC003: Limpeza de Worktree

**Ator:** DevOps Maintainer
**Pré-condições:** Worktree COMPLETED na tabela
**Fluxo Principal:**
1. Usuário clica "Clean" em worktree
2. Modal de confirmação aparece
3. Usuário confirma
4. Requisição DELETE enviada
5. Worktree removido
6. Linha some da tabela
7. Toast success aparece

**Pós-condições:** Worktree limpo, espaço liberado

### UC004: Busca Histórica

**Ator:** DevOps Maintainer
**Pré-condições:** Quer encontrar job específico
**Fluxo Principal:**
1. Usuário navega para "Logs"
2. Seleciona período (últimas 24h)
3. Digita job_id no search
4. Clica "Search"
5. Tabela com resultados aparece
6. Clica no job desejado
7. Modal de worktree abre

---

## 10. Roadmap de Implementação

### Fase 0: Setup (Dia 1-2) - 🔮 PENDENTE
**Objetivo:** Estrutura pronta

- [ ] Criar `apps/web/` com `package.json`
- [ ] Criar `apps/web/main.py` (fachada)
- [ ] Configurar Vite + TypeScript
- [ ] Criar estrutura `src/`
- [ ] Testar: `python apps/web/main.py` → Vite inicia

### Fase 1: API Client + Layout (Dia 3-4) - 🔮 PENDENTE
**Objetivo:** Comunicação com backend

- [ ] Criar `api/client.ts` (axios)
- [ ] Criar `api/endpoints.ts`
- [ ] Implementar header/navbar (Bootstrap)
- [ ] Implementar rotas React Router
- [ ] Testar: chamadas à API funcionam

### Fase 2: Dashboard (Dia 5-6) - 🔮 PENDENTE
**Objetivo:** Tela inicial com métricas

- [ ] Criar `MetricCard.tsx`
- [ ] Criar `Dashboard.tsx`
- [ ] Implementar polling para métricas
- [ ] Testar: cards atualizam a cada 5s

### Fase 3: Worktrees Table (Dia 7-8) - 🔮 PENDENTE
**Objetivo:** Listar worktrees com ações

- [ ] Criar `WorktreeTable.tsx`
- [ ] Implementar actions (View, Clean, Keep)
- [ ] Criar modal de detalhes
- [ ] Testar: tabela funciona

### Fase 4: Log Streaming (Dia 9-10) - 🔮 PENDENTE
**Objetivo:** Logs em tempo real

- [ ] Backend: implementar `/observability/logs/stream` (SSE)
- [ ] Frontend: criar `LogStream.tsx` com EventSource
- [ ] Implementar filtros por nível
- [ ] Implementar auto-scroll
- [ ] Testar: logs aparecem em tempo real

### Fase 5: Polish (Dia 11-12) - 🔮 PENDENTE
**Objetivo:** Acabamento

- [ ] Dark mode
- [ ] Responsividade mobile
- [ ] Loading states
- [ ] Error boundaries
- [ ] Testes E2E (Playwright)

---

## 11. Success Metrics

### Métricas de Adoção

| Métrica | Baseline | Mês 1 | Mês 3 |
|---------|----------|-------|-------|
| Usuários ativos/semana | 0 | 5 | 15 |
| Tempo médio de monitoramento | 30min | 5min | 2min |
| Worktrees limpos via UI | 0% | 70% | 90% |
| Satisfação (survey) | N/A | 7/10 | 9/10 |

### Métricas Técnicas

| Métrica | Target |
|---------|--------|
| Tempo de carregamento inicial | <2s |
| Latência de updates (SSE) | <500ms |
| Uptime do WebUI | 99% |
| Memory leak | Zero (após 24h) |

---

## 12. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| SSE não reconecta | Média | Alto | **Backoff exponencial + heartbeat** |
| Memory leak no frontend | Baixa | Médio | **React Query auto-cleanup + monitoramento** |
| Vite dev server crash | Baixa | Médio | **Auto-restart via supervisor** |
| Worktree race condition | Média | Baixo | **Backend locks + retry** |
| UI não escala (100+ worktrees) | Baixa | Alto | **Virtualização (react-window)** |

---

## 13. Próximos Passos

### Imediato (Hoje)
1. ✅ **PRD** (este documento)
2. ✅ **Decisão: React** (ecossistema maior)
3. 🔲 **Revisão com stakeholder**

### Curto Prazo (Semana 1)
1. 🔲 **Setup** (Fase 0)
2. 🔲 **API Client** (Fase 1)
3. 🔲 **Primeira tela** (Dashboard)

### Médio Prazo (Semana 2-3)
1. 🔲 **Implementação completa** (Fases 2-4)
2. 🔲 **Testes E2E**
3. 🔲 **Deploy em dev**

---

## 14. Apêndice

### A. Exemplo de Compo nente React

```tsx
// frontend/src/components/MetricCard.tsx
import { Card } from 'react-bootstrap'
import { useQuery } from '@tanstack/react-query'
import apiEndpoints from '../api/endpoints'

interface MetricCardProps {
  title: string
  queryKey: string
  queryFn: () => Promise<any>
  renderValue: (data: any) => string | number
  variant?: 'primary' | 'success' | 'warning' | 'danger'
}

export default function MetricCard({
  title,
  queryKey,
  queryFn,
  renderValue,
  variant = 'primary',
}: MetricCardProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: [queryKey],
    queryFn,
    refetchInterval: 5000,  // Poll a cada 5s
  })

  if (isLoading) return <Card>Loading...</Card>
  if (error) return <Card bg="danger">Error</Card>

  return (
    <Card border={variant} className="h-100">
      <Card.Body>
        <Card.Subtitle className="text-muted">{title}</Card.Subtitle>
        <h2 className={`text-${variant}`}>{renderValue(data)}</h2>
      </Card.Body>
    </Card>
  )
}
```

### B. Exemplo de SSE Hook

```typescript
// frontend/src/hooks/useLogStream.ts
import { useEffect, useState } from 'react'

export function useLogStream() {
  const [logs, setLogs] = useState<string[]>([])

  useEffect(() => {
    const eventSource = new EventSource(
      'http://localhost:8000/observability/logs/stream'
    )

    eventSource.onmessage = (e) => {
      setLogs((prev) => [...prev, e.data])
    }

    eventSource.onerror = (err) => {
      console.error('SSE error:', err)
      eventSource.close()
    }

    return () => eventSource.close()
  }, [])

  return logs
}
```

### C. Referências

- [PRD013: Webhook Autonomous Agents](./PRD013-webhook-autonomous-agents.md)
- [SPEC008: AI Agent Interface](../spec/SPEC008-AI-Agent-Interface.md)
- [FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)
- [Vite SSE Guide](https://vitejs.dev/guide/features.html#html-proxy)

---

## Aprovações

| Papel | Nome | Data | Assinatura |
|-------|------|------|------------|
| Autor | Sky | 2026-01-11 | ✍️ |
| Tech Lead | ___________ | ___________ | ______ |
| Product Manager | ___________ | ___________ | ______ |

---

> "A interface perfeita é invisível - o usuário vê seus dados, não a aplicação." – made by Sky 🎨

---

**Documento versão:** 1.2
**Última atualização:** 2026-01-25
**Status:** 🚧 Em Elaboração

---

## 15. Gap Analysis: Documentação vs Implementação

**Data da Análise:** 2026-01-25
**Responsável:** Sky

### Resumo Executivo

Este PRD foi elaborado com stack técnica e estrutura bem definidas, mas uma análise do código atual revela **inconsistências significativas** entre o proposto e o implementado. O status do WebUI é de "proposta aprovada, aguardando implementação".

### Propostas e Decisões Documentadas

#### PRD014: Skybridge WebUI - Dashboard de Monitoramento
- **Status:** 🚧 Em Elaboração
- **Stack Decidida:** React 18.3+ + TypeScript 5.7+ + Vite 6.0+ + React Bootstrap 2.10+
- **Estrutura Planejada:**
  - `apps/web/main.py` (fachada Python)
  - `apps/web/package.json` (dependências Node)
  - `apps/web/src/` (código React)

#### SPEC008: AI Agent Interface
- **Status:** Rascunho
- **Foco:** Interface para agentes de IA via stdin/stdout

### Stack Técnica Planejada

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| React | 18.3+ | Ecossistema maduro |
| TypeScript | 5.7+ | Type safety, DX |
| Vite | 6.0+ | Dev server rápido, HMR |
| React Bootstrap | 2.10+ | Componentes UI |
| Bootstrap | 5.3+ | Framework visual |
| Axios | 1.7+ | Cliente HTTP |
| React Router | 6.22+ | Client-side routing |
| React Query | 5.28+ | Server state, cache |

### Estado Atual da Implementação

#### ✅ O QUE EXISTE:
- Documentação PRD completa com roadmap (Fases 0-5)
- Stack técnica definida
- Diretório `apps/web/` com:
  - `dist/index.html` (build prévio?)
  - `node_modules/` (dependências internas)
- Dependências backend declaradas (FastAPI, Uvicorn, Pydantic)

#### ❌ O QUE NÃO EXISTE:
1. **Código Fonte Frontend:**
   - `package.json` não existe
   - Diretório `src/` não existe
   - `vite.config.ts` não existe
   - `tsconfig.json` não existe
   - Código React/TypeScript ausente

2. **Fachada Python:**
   - `apps/web/main.py` não implementado

3. **API Endpoints para UI:**
   - `/webhooks/jobs` - Listar jobs
   - `/webhooks/worktrees` - Listar worktrees
   - `/webhooks/worktrees/{name}` - Detalhes do worktree
   - `/webhooks/worktrees/{name}` (DELETE) - Remover worktree
   - `/observability/logs` - Logs históricos
   - `/observability/logs/stream` - SSE para logs

### Inconsistências Identificadas

| # | Inconsistência | Proposto | Realidade | Impacto |
|---|----------------|----------|-----------|---------|
| **1** | Fachada Python | `apps/web/main.py` executa Vite | Arquivo não existe | Impossível iniciar WebUI |
| **2** | Dependências Frontend | React, Bootstrap, Vite em `package.json` | Sem `package.json` | Sem dependências para desenvolvimento |
| **3** | Estrutura de diretórios | `apps/web/src/` completo | Apenas `dist/` e `node_modules/` | Não há código fonte |
| **4** | API endpoints | 6 novos endpoints planejados | Nenhum implementado | Frontend não teria backend |
| **5** | .gitignore | Não mencionado | `dist/` existe sem referência | Incerteza sobre versionamento |

### Status dos Componentes

| Componente | Status | Próximo Passo |
|------------|--------|---------------|
| Documentação PRD014 | ✅ Completa | Revisão stakeholder |
| Stack Técnica | ✅ Decidida | Setup Fase 0 |
| Estrutura de diretórios | ⚠️ Parcial | Criar `src/` e configs |
| Fachada Python (`main.py`) | ❌ Ausente | Implementar |
| Código React/TypeScript | ❌ Ausente | Criar do zero |
| API endpoints para UI | ❌ Ausentes | Implementar |
| SSE streaming logs | ❌ Ausente | Implementar |

### Recomendações

1. **Prioridade 1:** Implementar Fase 0 do PRD014
   - Criar `package.json` com stack declarada
   - Implementar `apps/web/main.py`
   - Configurar Vite + TypeScript

2. **Prioridade 2:** Implementar API endpoints necessários
   - `/webhooks/jobs`
   - `/webhooks/worktrees`
   - `/observability/logs/stream` (SSE)

3. **Prioridade 3:** Desenvolver componentes React
   - Dashboard principal
   - Tabela de worktrees
   - Streaming de logs

4. **Atualizar .gitignore:**
   - Adicionar referência a `dist/`
   - Considerar `*.log` específico do WebUI

### Conclusão

O projeto possui uma proposta web completa e tecnicamente sólida, mas a implementação está estagnada na fase de planejamento. A decisão técnica foi tomada, mas o código fonte do frontend não foi criado.

**Ação Recomendada:** Iniciar implementação pela Fase 0 (setup) para estabelecer a base antes de prosseguir com features mais complexas.

> "Documentação sem código é apenas um sonho; código sem documentação é um pesadelo. Equilíbrio é a chave." – made by Sky 🎯

---

## Histórico de Mudanças

| Versão | Data | Alterações |
|--------|------|------------|
| 1.2 | 2026-01-25 | Adicionada seção 15: Gap Analysis com análise de inconsistências entre documentação e implementação |
| 1.1 | 2026-01-11 | Decisão de stack: React selecionado; removida alternativa Vue |
| 1.0 | 2026-01-11 | Versão inicial do PRD |
