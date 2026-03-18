# PL003 — Isolamento Profissional de Testes (ADR024 Estendida)

**Status:** 📋 **PLANEJADO**
**Sequência:** 003
**Depende de:** ADR024
**É dependência de:** PRD023

## Contexto e Problema

**Problema Crítico Identificado:**
- Testes estão usando banco de dados de produção (`data/jobs.db`)
- O singleton `get_job_queue()` cria uma instância global compartilhada
- A ADR024 define isolamento por workspace, mas o singleton ignora esse contexto

**Arquivo Crítico:**
- `tests/core/contexts/webhooks/test_integration.py` - Usa `get_job_queue()` diretamente (linha 36)

**Arquitetura Atual:**
```python
# handlers.py - Singleton GLOBAL (linha 109-131)
def get_job_queue() -> JobQueuePort:
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueueFactory.create_from_env()  # ← data/jobs.db
    return _job_queue
```

**ADR024 Define:**
```
workspace/
├── core/
│   └── data/
│       └── jobs.db          # ← Banco isolado do core
├── trading/
│   └── data/
│       └── jobs.db          # ← Banco isolado do trading
```

## Decisão: Extensão da ADR024

### Adicionar Seção: Ambiente de Testes

**Caminho para testes:** `/test/contexto.db`

**Princípios:**
1. **Teste NUNCA toca produção** - `data/jobs.db` é inalcançável em testes
2. **Cada teste tem seu banco** - `tmp_path` para isolamento total
3. **Singleton respeita workspace** - Cache por workspace, não global

### Nova Estrutura

```
workspace/
├── core/
│   └── data/
│       └── jobs.db          # ← Produção do workspace core
├── trading/
│   └── data/
│       └── jobs.db          # ← Produção do workspace trading
└── test/                    # ← NOVO: Ambiente de testes
    └── contexto.db          # ← Base temporária para testes
```

## Descobertas Adicionais

**Contexto workspace já existe:**
- `src/runtime/workspace/workspace_context.py` já tem `get_current_workspace()` implementado
- Usa `ContextVar` para suportar threads/tasks sem contexto de request
- `set_current_workspace()` pode ser usado para testes e worker threads

**Hardcode problemático:**
- `src/infra/webhooks/adapters/job_queue_factory.py:123` tem `"data/jobs.db"` hardcoded
- Precisa ser removido/alterado para respeitar workspace

**Uso de `get_job_queue()`:**
- `src/runtime/bootstrap/app.py:96,105` - Inicia worker (continua funcionando)
- `src/runtime/delivery/routes.py:763,814,816` - Métricas/listagem (funciona via header)
- `src/core/webhooks/application/handlers.py` - Onde é definido (precisa modificar)
- `tests/core/contexts/webhooks/test_integration.py` - **CRÍTICO: usa singleton**

## Implementação

### Fase 0: Verificar e Remover Hardcode (PRÉ-REQUISITO)

**Arquivo:** `src/infra/webhooks/adapters/job_queue_factory.py`

**Remover linha 123:**
```python
# ANTES
"db_path": os.getenv("SQLITE_DB_PATH", "data/jobs.db"),  # ← Hardcode!

# DEPOIS (remover ou usar placeholder)
"db_path": os.getenv("SQLITE_DB_PATH"),  # ← Não tem padrão, usa from_context()
```

**Nota:** O `create_from_env()` não deve mais ser usado em produção. Use `from_context()`.

### Fase 1: Estender ADR024 (Documento)

**Arquivo:** `docs/adr/ADR024-workspaces-multi-instancia.md`

**Adicionar seção "Ambiente de Testes":**
```markdown
## Ambiente de Testes

### Princípios
1. **Teste NUNCA toca produção** - `data/jobs.db` é proibido em testes
2. **Cada teste tem seu banco** - Usar `tmp_path` do pytest
3. **Singleton respeita contexto** - Cache por workspace/teste

### Caminho de Teste
- **Produção:** `workspace/{workspace_id}/data/jobs.db`
- **Testes:** `/test/contexto.db` ou `tmp_path/test.db`

### Padrão para Testes
```python
def test_isolamento(tmp_path):
    queue = SQLiteJobQueue.from_context(
        request,
        base_path=tmp_path  # ← Isolamento total
    )
```
```

### Fase 2: Modificar Singleton para Workspaces

**Arquivo:** `src/core/webhooks/application/handlers.py`

**Mudança:**
```python
# ANTES (singleton global)
_job_queue: JobQueuePort | None = None

def get_job_queue() -> JobQueuePort:
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueueFactory.create_from_env()
    return _job_queue

# DEPOIS (cache por workspace)
_job_queues: dict[str, JobQueuePort] = {}

def get_job_queue() -> JobQueuePort:
    """Retorna instância do job queue RESPEITANDO O WORKSPACE."""
    global _job_queues

    # Obter workspace atual do contexto
    from runtime.workspace.workspace_context import get_current_workspace
    workspace_id = get_current_workspace()  # ← Context-aware

    # Cache por workspace
    if workspace_id not in _job_queues:
        from infra.webhooks.adapters.sqlite_job_queue import SQLiteJobQueue
        from runtime.config.config import get_base_path

        base_path = get_base_path()
        db_path = base_path / "workspace" / workspace_id / "data" / "jobs.db"

        _job_queues[workspace_id] = SQLiteJobQueue(db_path=db_path)

    return _job_queues[workspace_id]
```

### Fase 3: Fixtures Profissionais para Testes

**Arquivo:** `tests/conftest.py`

**Adicionar:**
```python
import pytest
from unittest.mock import AsyncMock
from core.webhooks.ports.job_queue_port import JobQueuePort

@pytest.fixture
def mock_job_queue():
    """Job Queue mock para garantir isolamento em testes."""
    mock_queue = AsyncMock(spec=JobQueuePort)
    mock_queue.enqueue = AsyncMock(return_value="test-job-id")
    mock_queue.get_job = AsyncMock(return_value=None)
    mock_queue.dequeue = AsyncMock(return_value=None)
    mock_queue.size = Mock(return_value=0)
    mock_queue.clear = AsyncMock()
    return mock_queue

@pytest.fixture
def isolated_job_queue(tmp_path):
    """Job queue REAL mas isolado em tmp_path."""
    from infra.webhooks.adapters.sqlite_job_queue import SQLiteJobQueue

    db_path = tmp_path / "test_jobs.db"
    queue = SQLiteJobQueue(db_path=db_path)
    return queue
```

### Fase 4: Corrigir Teste Crítico

**Arquivo:** `tests/core/contexts/webhooks/test_integration.py`

**Mudança:**
```python
# ANTES
@pytest.fixture
def job_queue(self):
    """Retorna fila compartilhada."""
    return get_job_queue()  # ← Singleton global!

# DEPOIS
@pytest.fixture
def job_queue(self, isolated_job_queue):
    """Retorna fila isolada para este teste."""
    return isolated_job_queue  # ← Isolamento total
```

**Remover fixture `clear_queue`** (não é mais necessário com isolamento).

### Fase 5: Remover Vestígios de Bancos Antigos

**Arquivos a verificar/modificar:**
1. `data/jobs.db` - Deletar se existir
2. `data/agent_executions.db` - Deletar se existir
3. `src/infra/webhooks/adapters/job_queue_factory.py` - Remover hardcode de `data/jobs.db`

**Verificar se há referências:**
```bash
# Grep por "data/jobs.db" no código
grep -r "data/jobs.db" src/
```

### Fase 6: Atualizar Documentação

**Arquivo:** `docs/adr/ADR024-workspaces-multi-instancia.md`

**Adicionar checklist de remoção:**
```markdown
## Remoção de Bancos Antigos

### Vestígios a Remover
- [x] Remover `data/jobs.db` se existir
- [x] Remover `data/agent_executions.db` se existir
- [x] Remover hardcode de `data/jobs.db` do JobQueueFactory
- [x] Atualizar documentação para referenciar `workspace/{id}/data/jobs.db`
```

## Arquivos Críticos para Modificar

| Arquivo | Ação | Prioridade |
|---------|------|------------|
| `docs/adr/ADR024-workspaces-multi-instancia.md` | Adicionar seção "Ambiente de Testes" | Alta |
| `src/core/webhooks/application/handlers.py` | Modificar `get_job_queue()` para cache por workspace | Alta |
| `tests/conftest.py` | Adicionar fixtures `mock_job_queue` e `isolated_job_queue` | Alta |
| `tests/core/contexts/webhooks/test_integration.py` | Usar `isolated_job_queue` ao invés de singleton | Alta |
| `src/infra/webhooks/adapters/job_queue_factory.py` | Verificar/remover hardcode de `data/jobs.db` | Média |
| `.gitignore` | Garantir que `workspace/` está ignorado | Baixa |

## Verificação

### Como Testar

1. **Testes passam com isolamento:**
   ```bash
   python -m pytest tests/core/contexts/webhooks/test_integration.py -v
   ```

2. **Nenhum teste toca `data/jobs.db`:**
   ```bash
   # Deletar production DB antes dos testes
   rm -f data/jobs.db
   python -m pytest tests/ -v
   # data/jobs.db NÃO deve ser recriado
   ```

3. **Cada workspace tem seu banco:**
   ```bash
   ls workspace/core/data/jobs.db      # ← Deve existir
   ls workspace/trading/data/jobs.db    # ← Deve existir se trading criado
   ```

4. **Testes usam tmp_path:**
   ```bash
   python -m pytest tests/ -v --tb=short
   # Deve passar sem criar arquivos fora tmp_path/
   ```

## DoD (Definition of Done)

- [ ] ADR024 estendida com seção "Ambiente de Testes"
- [ ] Singleton `get_job_queue()` respeita workspace atual
- [ ] `tests/conftest.py` tem fixtures profissionais
- [ ] `tests/core/contexts/webhooks/test_integration.py` usa `isolated_job_queue`
- [ ] Nenhum teste toca `data/jobs.db`
- [ ] Bancos antigos removidos (`data/jobs.db`, `data/agent_executions.db`)
- [ ] Todos os testes passam com `python -m pytest tests/ -v`
- [ ] Pre-commit hooks passam

## Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Singleton compartilhado pode ser usado em outros lugares | Grep por `get_job_queue()` e substituir onde necessário |
| Testes podem depender de estado compartilhado | Usar `autouse` fixtures para limpar estado |
| Worker thread pode não ter contexto de workspace | Implementar `set_current_workspace()` para threads |

## Relacionamento

- **É dependência de:** PRD023 (WebUI Workspaces Globais)
- **Depende de:** ADR024 (Workspaces Multi-Instância)

> "Testes são a especificação que não mente" – made by Sky 🛡️
