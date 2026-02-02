# Standalone vs Main - Adaptações Necessárias

**Data:** 2025-01-17
**Status:** ⚠️ **OBSOLETO** - Ver ADR019 para estrutura atual
**Contexto:** Integração GitHub → Trello

---

## ⚠️ Aviso de Obsolescência

Este documento foi criado durante a transição de worktrees e descreve adaptações necessárias para a estrutura antiga (`src/skybridge/...`).

**Estrutura atual (após ADR019):**
- A simplificação da estrutura foi implementada via ADR019
- O renomeamento `platform` → `runtime` está completo
- A estrutura atual é `src/core/`, `src/infra/`, `src/kernel/`, `src/runtime/`

**Para informações sobre a estrutura atual, consulte:**
- **ADR019:** `docs/adr/ADR019-simplificacao-estrutura-src.md`
- **Implementação:** `src/runtime/` (ex-platform), `src/core/`, `src/infra/`

---

## 📋 Contexto (Histórico)

Durante a implementação da integração GitHub → Trello, identificamos diferenças entre:
- **Worktree kanban:** Estrutura simplificada (`src/core/...`)
- **Branch main:** Estrutura original (`src/skybridge/...`)

## 🔄 Diferenças Identificadas

### 1. Módulo `skybridge`

| Localização | Status |
|-------------|--------|
| `main/src/skybridge/__init__.py` | ✅ Existe (define `__version__`) |
| `kanban/src/` | ❌ Não existe (estrutura simplificada) |

**Impacto:**
- `apps/server/main.py` na main importa `from skybridge import __version__`
- Na kanban, esse import falha

**Solução temporária:**
- Usar `github_webhook_server.py` standalone (não depende do módulo skybridge)
- Após merge da kanban para main, remover código duplicado

### 2. InMemoryJobQueue

| Problema | Solução |
|----------|---------|
| Não herdava de `JobQueuePort` | Adicionar herança: `class InMemoryJobQueue(JobQueuePort)` |
| Implementação local incompleta | Adicionar métodos `dequeue()` e `size()` |

**Arquivo:** `src/infra/webhooks/adapters/in_memory_queue.py`

```python
# ANTES:
class InMemoryJobQueue:
    ...

# DEPOIS:
from core.webhooks.ports.job_queue_port import JobQueuePort

class InMemoryJobQueue(JobQueuePort):
    ...
```

### 3. Ngrok Integration

**Na main:** `apps/server/main.py` inicia ngrok automaticamente

**No standalone:** `github_webhook_server.py` precisa do mesmo código

**Solução implementada:**
- Adicionada função `start_ngrok()` ao `github_webhook_server.py`
- Lê variáveis de ambiente: `NGROK_ENABLED`, `NGROK_AUTH_TOKEN`, `NGROK_DOMAIN`
- Inicia túnel automaticamente se configurado

### 4. TrelloIntegrationService

**Integração em múltiplos pontos:**

| Componente | Modificação |
|------------|-------------|
| `github_webhook_server.py` | Adiciona `trello_service` opcional |
| `webhook_worker.py` | Adiciona `trello_service` ao JobOrchestrator |
| `webhook_processor.py` | Adiciona `trello_service` ao criar jobs |
| `handlers.py` | Adiciona `trello_service` ao WebhookHandler |

**Padrão:** Trello é 100% opcional - funciona sem ele

## 🚀 Como Usar

### Opção A: Standalone (kanban)

```bash
cd B:\_repositorios\skybridge-auto\kanban

# 1. Configure .env
# GITHUB_TOKEN=seu_token
# GITHUB_REPO=h4mn/skybridge
# TRELLO_API_KEY=sua_key
# TRELLO_API_TOKEN=seu_token
# TRELLO_BOARD_ID=seu_board_id
# NGROK_ENABLED=true
# NGROK_AUTH_TOKEN=seu_token
# NGROK_DOMAIN=cunning-dear-primate.ngrok-free.app

# 2. Inicie o servidor
PYTHONPATH=B:/_repositorios/skybridge-auto/kanban/src \
python src/core/webhooks/infrastructure/github_webhook_server.py

# 3. Execute o demo
PYTHONPATH=B:/_repositorios/skybridge-auto/kanban/src \
python src/core/kanban/testing/demo_github_to_trello.py
```

### Opção B: Main (após merge)

```bash
cd B:\_repositorios\skybridge

# 1. A worktree kanban será mergeada na main
# 2. apps/server/main.py já tem ngrok integrado
# 3. JobOrchestrator já tem TrelloIntegrationService
# 4. Basta configurar .env e rodar

python -m apps.server.main
```

## ⚠️ Limitações Atuais

### Ngrok Domain Conflict

**Problema:**
- Domínio ngrok reservado só pode ter **um** túnel ativo
- Se main está rodando, kanban não pode usar o mesmo domínio

**Soluções:**

1. **Usar ngrok sem domínio reservado** (URL aleatória)
   ```bash
   # Não configurar NGROK_DOMAIN
   # ngrok vai gerar: https://abc123.ngrok-free.app
   ```

2. **Usar pooling do ngrok** (load balancing)
   ```bash
   ngrok http 8000 --pooling-enabled
   ```

3. **Parar main antes de iniciar kanban** (não ideal)

4. **Usar URLs diferentes** (dois domínios reservados)

## 📝 Tasks Pendentes

### Para Merge da Kanban → Main

- [ ] Remover `github_webhook_server.py` standalone (código duplicado)
- [ ] Atualizar `apps/server/main.py` para importar de estrutura nova
- [ ] Criar módulo `version.py` para substituir `skybridge/__init__.py`
- [ ] Atualizar ADR020 com nova arquitetura
- [ ] Testar integração completa na main

### Para Documentação

- [ ] Atualizar WEBHOOK_SETUP.md com nova estrutura
- [ ] Criar guia de troubleshooting para ngrok conflicts
- [ ] Documentar padrão de feature toggle (Trello opcional)

## 🎯 Recomendações

### Curto Prazo (Demo)

1. Usar `github_webhook_server.py` standalone
2. Criar ngrok temporário sem domínio reservado
3. Testar fluxo completo GitHub → Trello

### Longo Prazo (Produção)

1. Merge worktree kanban → main
2. Usar `apps/api.main` (único ponto de entrada)
3. Configurar ngrok com domínio reservado permanente
4. Monitorar webhooks em produção

---

**Status:** Em andamento
**Próxima ação:** Merge kanban → main após testes validados

> "A simplicidade é o último grau de sofisticação." – Leonardo da Vinci
> made by Sky 🦍✨
