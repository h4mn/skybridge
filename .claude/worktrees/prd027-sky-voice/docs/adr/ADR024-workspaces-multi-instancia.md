---
status: aceito
data: 2026-01-31
aprovada_por: usuário
data_aprovacao: 2026-01-31
implementacao: pendente
relacionado: PRD018, PRD013
---

# ADR024 — Workspaces Multi-Instância com Isolamento de Dados

**Status:** ✅ **ACEITO**

**Data:** 2026-01-31
**Data de Aprovação:** 2026-01-31
**Relacionado:** PRD018 (Job Queue), PRD013 (Webhook Agents)

## Contexto

Atualmente a Skybridge possui uma estrutura monolítica de dados que mistura jobs de múltiplas instâncias/contextos:

```
ATUAL (monolítico):
├── data/jobs.db              # ← Todos os jobs misturados
├── workspace/skybridge/      # ← Uso genérico
└── ../skybridge-auto/         # ← Worktrees misturadas fora do repo
    ├── skybridge-github-123/
    └── skybridge-github-456/
```

**Problemas identificados:**

1. **Isolamento inadequado:** Jobs de diferentes contextos (skybridge, trading, futura) ficam misturados no mesmo banco
2. **Worktrees fora do repo:** `../skybridge-auto` fica fora do repositório, difícil de gerenciar
3. **Sem multi-tenancy:** Impossível rodar múltiplas instâncias isoladas no mesmo servidor
4. **Escalabilidade limitada:** Não suporta múltiplos projetos/repositórios facilmente

**Necessidade:**
- Suportar múltiplas instâncias de trabalho (skybridge, trading, futura, etc.)
- Cada instância com seus próprios jobs, worktrees e dados
- WebUI com seletor para alternar entre instâncias
- Suporte a múltiplos projetos/repositórios externos

## Decisão

**A Skybridge adota workspaces multi-instância com isolamento completo de dados.**

### Princípios

1. **Uma instância = Um workspace**
   - Cada workspace isolado com seus próprios dados
   - `workspace/core/` → Instância principal (auto-evo)
   - `workspace/trading/` → Instância de trading (extensão)
   - `/caminho/absoluto/futura/workspace/` → Outro projeto

2. **Instância `core` é obrigatória**
   - Auto-criada na primeira inicialização
   - Configurações e segredos padrão do sistema
   - Outras instâncias são opcionais

3. **Dados por workspace**
   - Cada workspace tem seu próprio `jobs.db`
   - Worktrees DENTRO do workspace: `{workspace}/worktrees/`
   - Isolamento total entre instâncias

4. **Servidor multi-tenant**
   - `data/workspaces.db` - Metadados de workspaces
   - API com prefixo de workspace: `/api/:workspace/jobs`
   - WebUI com seletor de instância

### Estrutura de Diretórios

```
ESTRUTURA NOVA:
├── data/
│   └── workspaces.db           # ← Metadados (nome, caminho, status)
│
├── workspace/                  # ← Isolado pelo .gitignore
│   ├── core/                   # ← Instância OBRIGATÓRIA (auto-evo)
│   │   ├── .env                 # ← Segredos da instância core
│   │   ├── .env.example         # ← Template da instância core
│   │   ├── config.json          # ← Configurações específicas
│   │   ├── data/
│   │   │   ├── jobs.db         # ← Jobs da instância core
│   │   │   └── executions.db    # ← Execuções de agentes (local)
│   │   ├── worktrees/          # ← Worktrees DENTRO do workspace
│   │   │   ├── skybridge-github-123/
│   │   │   └── skybridge-github-456/
│   │   ├── snapshots/
│   │   └── logs/
│   │
│   ├── trading/               # ← Instância OPCIONAL (extensão)
│   │   ├── .env                 # ← Segredos da instância trading
│   │   ├── .env.example         # ← Template da instância trading
│   │   ├── config.json          # ← Configurações específicas
│   │   ├── data/
│   │   │   ├── jobs.db
│   │   │   └── executions.db
│   │   └── worktrees/
│   │
│   └── futura/                 # ← Instância OPCIONAL (outro projeto)
│       ├── .env
│       ├── .env.example
│       ├── config.json
│       ├── data/
│       │   ├── jobs.db
│       │   └── executions.db
│       └── worktrees/
│
├── .gitignore                  # ← Deve ignorar workspace/
└── .workspaces                 # ← Arquivo de configuração (JSON)
```

**Nota sobre .gitignore:**

Workspaces dentro do repositório são **isolados pelo .gitignore** e **NÃO versionados**:
- Dados gerados em runtime (`*.db`, logs, snapshots)
- Worktrees (cópias do repositório git)
- Configurações específicas (`.env`, `config.json`, `.env.example` com segredos)

```gitignore
# .gitignore
workspace/                    # ← Isola TODOS os workspaces (dados, configs, worktrees)
```

**Por que não versionar `.env` dos workspaces:**
- Cada workspace tem seus próprios segredos (API keys, tokens)
- `.env` contém informações sensíveis que NÃO vão para o git
- Apenas `.env.example` (template sem segredos) pode ser versionado

**Estrutura versionada vs não versionada:**

```
workspace/core/                  # ← NÃO versionado
├── .env                         # ❌ Segredos (não versionado)
├── .env.example                 # ✅ Template (pode ser versionado)
├── config.json                  # ❌ Configs específicas (não versionado)
├── data/jobs.db                 # ❌ Dados runtime (não versionado)
└── worktrees/                   # ❌ Worktrees (não versionado)
```

### Arquivo `.workspaces`

**Formato JSON:**

```json
{
  "default": "core",
  "workspaces": {
    "core": {
      "name": "Skybridge Core",
      "path": "workspace/core",
      "description": "Instância principal do Skybridge",
      "auto": true,
      "enabled": true
    },
    "trading": {
      "name": "Trading Bot",
      "path": "workspace/trading",
      "description": "Bot de finanças e trading",
      "auto": false,
      "enabled": true
    },
    "futura": {
      "name": "Futura Project",
      "path": "/c/repos/futura/workspace/futura",
      "description": "Instância do projeto Futura",
      "auto": false,
      "enabled": false
    }
  }
}
```

**Campos:**
- `default`: Workspace ativo por padrão
- `auto`: `true` = criado automaticamente pelo sistema (só `core`)
- `enabled`: `false` = desabilitado temporariamente

### API Multi-Tenant

**Workspace via header (escolhido):**

```
ANTES:
GET /api/webhooks/jobs              ← Todos os jobs misturados

DEPOIS:
GET /api/workspaces                   ← Listar workspaces (management)
GET /api/jobs                         ← Usa workspace do header
```

**Header `X-Workspace`:**

```http
GET /api/jobs
X-Workspace: core                    ← Usa workspace core

GET /api/jobs
X-Workspace: trading                 ← Usa workspace trading
```

**Endpoint de management (sem header):**

```http
GET /api/workspaces                   ← Lista todos os workspaces
POST /api/workspaces                  ← Criar novo workspace
GET /api/workspaces/:id               ← Detalhes de um workspace
DELETE /api/workspaces/:id            ← Deletar workspace
```

### Configuração e Segredos

**Cada workspace tem sua própria configuração:**

```
workspace/core/
├── .env                      # ← Segredos da instância core
├── .env.example              # ← Template da instância core
├── config.json               # ← Configurações específicas
├── data/jobs.db
└── worktrees/

workspace/trading/
├── .env                      # ← Segredos da instância trading
├── .env.example              # ← Template da instância trading
├── config.json               # ← Configurações específicas
├── data/jobs.db
└── worktrees/
```

**Isolamento completo:**
- ✅ Cada workspace tem seu próprio `.env` (segredos isolados)
- ✅ `.env.example` por workspace (template específico)
- ✅ `config.json` por workspace (configs específicas)
- ✅ Nenhum compartilhamento de configurações entre instâncias

**Sem `.env` na raiz do projeto:**
- O `.env` raiz pode existir apenas para desenvolvimento local
- **NÃO** é usado em produção (cada workspace usa seu próprio `.env`)
- Remove risco de misturar segredos de instâncias diferentes

### Middleware de Workspace

**Comportamento do middleware:**

```python
# Pseudo-código do middleware
async def workspace_middleware(request: Request):
    # 1. Lê header X-Workspace
    workspace_id = request.headers.get("X-Workspace", "core")

    # 2. Carrega .env do workspace
    load_workspace_env(workspace_id)  # ← Carrega workspace/{workspace_id}/.env

    # 3. Valida se workspace existe
    if not workspace_exists(workspace_id):
        return HTTPException(404, "Workspace not found")

    # 4. Injeta no contexto da request
    request.state.workspace = workspace_id

    # 5. Injeta no context['workspace'] para use nos handlers
    # (usado por SQLiteJobQueue, AgentExecutionStore, etc.)

    return await call_next(request)
```

**Carregamento de `.env` por workspace:**

```python
def load_workspace_env(workspace_id: str):
    """Carrega .env específico do workspace."""
    env_path = f"workspace/{workspace_id}/.env"
    if Path(env_path).exists():
        load_dotenv(env_path)  # Sobrescreve vars de ambiente
```

**Uso no código:**

```python
# SQLiteJobQueue usa workspace do contexto
def get_job_queue():
    workspace = get_current_workspace()  # do contexto
    db_path = f"workspace/{workspace}/data/jobs.db"
    return SQLiteJobQueue(db_path=db_path)
```

## Alternativas Consideradas

### Opção A: Workspaces fora do repositório

**Padrão:** Workspaces em `../skybridge-workspaces/{instancia}/`

**Vantagens:**
- ✅ Separação total do código

**Desvantagens:**
- ❌ Difficil gerenciar múltiplos locais
- ❌ Perde referência ao repositório
- ❌ Worktrees ainda fora do repo

**Decisão:** ❌ **REJEITADA** — workspaces DENTRO do repo

### Opção B: Um único banco com coluna de workspace

**Padrão:** Tabela `jobs` com coluna `workspace_id`

**Vantagens:**
- ✅ Um banco só

**Desvantagens:**
- ❌ Isolamento inadequado (um bug afeta todos)
- ❌ Performance (filtro obrigatório em toda query)
- ❌ Difícil backup por instância

**Decisão:** ❌ **REJEITADA** — isolamento via bancos separados

### Opção C: Workspaces multi-instância (Escolhida)

**Padrão:** Um banco por workspace, metadados centralizados

**Vantagens:**
- ✅ Isolamento completo (crash não afeta outros)
- ✅ Performance (queries diretas sem filtro)
- ✅ Backup/restore por instância
- ✅ Multi-tenancy nativo
- ✅ Worktrees dentro do workspace

**Desvantagens:**
- ⚠️ Migração necessária
- ⚠️ Complexidade adicional

**Decisão:** ✅ **ESCOLHIDA** — prepara para escalabilidade

## Consequências

### Imediatas

1. **Criação da estrutura de workspaces**
   - Criar `workspace/core/` com subdiretórios (`data/`, `worktrees/`, `logs/`)
   - Criar `workspace/core/.env` (segredos da instância core)
   - Criar `workspace/core/.env.example` (template)
   - Criar `workspace/core/config.json` (configs específicas)
   - Mover `data/jobs.db` → `workspace/core/data/jobs.db`
   - Criar `data/workspaces.db` com entrada `core`
   - Atualizar `.gitignore` para isolar `workspace/`

2. **Middleware de workspace**
   - Implementar middleware que lê `X-Workspace` header
   - Define workspace ativo no contexto da request
   - Fallback para `core` se header não fornecido

3. **Código existente**
   - Atualizar `SQLiteJobQueue` para usar workspace do contexto
   - `AgentExecutionStore` usa `{workspace}/data/executions.db`
   - Renomear `agent_executions.db` → `executions.db`
   - `WorktreeManager` usa `{workspace}/worktrees/`

### Ferramentas CLI

**Novo comando `skybridge workspace`:**

```bash
# Listar workspaces
skybridge workspace list
# core (workspace/core) [ACTIVE]
# trading (workspace/trading)

# Criar nova instância
skybridge workspace create trading --name "Trading Bot"

# Deletar instância
skybridge workspace delete trading --backup

# Backup
skybridge workspace backup core --output backups/core-20250131.tar.gz

# Restore
skybridge workspace restore backups/core-20250131.tar.gz

# Ativar workspace
skybridge workspace use trading

# Gerenciamento de configurações para worktrees
# Copiar .env/config de um workspace para worktrees específicas
skybridge workspace config sync core --to worktree-name
skybridge workspace config sync trading --to "skybridge-github-123"

# Sincronização de volta (worktree → workspace)
# Quando uma worktree cria novas configs/chaves, leva de volta para o workspace pai
skybridge workspace config sync worktree-name --to core --bidirectional
skybridge workspace config sync "github-pr-456" --to core --merge
# Resultado: novas chaves do .env da worktree são mergeadas no core
# Chaves existentes no core NÃO são sobrescritas (apenas adiciona novas)

# Mover .env e config.json entre workspaces
skybridge workspace config move --from core --to trading --include-env
skybridge workspace config move --from core --to trading --include-config

# Listar configurações de um workspace
skybridge workspace config list core
# .env: 12 variáveis
# config.json: {"timeout": 300, "max_retries": 3}

# Validar configurações de um workspace
skybridge workspace config validate core

# Comparar configurações (ver diferenças)
skybridge workspace config diff core worktree-name
# Mostra quais chaves estão diferentes entre os dois .env
```

**Caso de uso: Worktrees com configurações compartilhadas**

Algumas worktrees precisam das mesmas configurações do workspace pai:
- Worktrees de repositórios externos (GitHub PRs)
- Worktrees de features que dependem de APIs específicas
- Ambientes temporários que precisam de acesso aos mesmos recursos

**Sincronização workspace → worktree (setup inicial):**
```bash
# Exemplo: worktree criada para um PR precisa da mesma API key do workspace core
skybridge worktree create github-pr-123 --from core
skybridge workspace config sync core --to github-pr-123 --include-env
# Resultado: github-pr-123/.env agora contém as mesmas variáveis do core
```

**Sincronização worktree → workspace (novas configurações):**
```bash
# Exemplo: durante desenvolvimento na worktree, uma nova API key é necessária
# 1. Desenvolvedor adiciona NOVA_API_KEY=xyz no .env da worktree
# 2. Para levar essa nova chave de volta para o workspace pai:
skybridge workspace config sync github-pr-123 --to core --merge
# Resultado: NOVA_API_KEY é adicionada ao core/.env
#          Chaves existentes no core NÃO são sobrescritas
```

**Comportamento do merge:**
- ✅ Adiciona novas chaves que existem na origem mas não no destino
- ❌ NÃO sobrescreve chaves existentes no destino (preserva valores)
- ⚠️ Se houver conflito (mesma chave com valores diferentes), pede confirmação interativa

**Segurança:** O comando `config sync` sempre pede confirmação antes de sobrescrever arquivos `.env`.

### WebUI

**Página "Workspaces" com:**
- Seletor de instância (dropdown)
- Métricas por workspace
- Botões de criar/deletar/backup
- Status de cada workspace

**Integração via header:**
```javascript
// Ao selecionar workspace no dropdown
const selectWorkspace = (workspaceId) => {
  // Define header global para todas as requests
  apiClient.defaults.headers['X-Workspace'] = workspaceId
  // Recarrega dados
  refetch()
}
```

### De Longo Prazo

1. **Multi-projeto**
   - Suportar workspaces de outros repositórios
   - Cada workspace pode ser um projeto diferente

2. **Auto-descoberta** (em discussão)
   - Detectar workspaces automaticamente
   - Registrar workspace ao encontrar `{path}/.workspaces/`

## Tópicos em Discussão

**Futuros / Não decididos:**

1. **Auto-descoberta**
   - Como detectar workspaces automaticamente?
   - Varrer diretórios ou registrar explicitamente?

2. **Compartilhamento de recursos**
   - Há recursos compartilhados entre workspaces?
   - Configurações globais vs específicas?

3. **Backup/restore**
   - Formato do backup? Tar? Zip?
   - Incluir worktrees no backup?

4. **Colisões de nomes**
   - Como garantir unicidade de nomes entre projetos?
   - Namespace por projeto?

5. **Migração de worktrees**
   - Script para mover `../skybridge-auto/*` → `workspace/core/worktrees/`
   - Preservar histórico git?

## Status de Implementação

- [x] ADR aprovada
- [x] **Ambiente de Testes** - Seção adicionada com princípios de isolamento
- [x] **Singleton get_job_queue()** - Cache por workspace implementado
- [x] **Fixtures profissionais** - mock_job_queue e isolated_job_queue em conftest.py
- [x] **Testes isolados** - test_integration.py usa isolated_job_queue
- [x] **Hardcode removido** - job_queue_factory.py sem hardcode de data/jobs.db
- [ ] Schema de `data/workspaces.db`
- [ ] Arquivo `.workspaces` parser (JSON)
- [ ] Middleware `X-Workspace` com carregamento de `.env`
- [ ] API de workspaces (CRUD - sem header)
- [ ] APIs existentes respeitam workspace do header
- [ ] WebUI seletor de workspace + header automático
- [ ] CLI `skybridge workspace`
- [ ] Script de setup (criar estrutura workspace/core/)
- [ ] Setup de `.env` e `config.json` por workspace
- [ ] CLI `skybridge workspace config sync/move/validate/diff`
- [ ] Sincronização bidirecional com merge (não sobrescrever chaves existentes)
- [ ] Atualização de `.gitignore`
- [ ] Renomear `agent_executions.db` → `executions.db`
- [ ] Testes end-to-end de workspaces

## Referências

- **PRD018:** Job Queue com SQLite
- **PRD013:** Webhook Autonomous Agents
- **ADR020:** Integração Trello (contextos diferentes)
- **Workspace README:** `workspace/README.md`

## Ambiente de Testes

### Princípios

1. **Teste NUNCA toca produção** - `data/jobs.db` é proibido em testes
2. **Cada teste tem seu banco** - Usar `tmp_path` do pytest para isolamento total
3. **Singleton respeita contexto** - Cache por workspace, não global

### Caminho de Teste

- **Produção:** `workspace/{workspace_id}/data/jobs.db`
- **Testes:** `tmp_path/test.db` ou `tmp_path/test_jobs.db`

### Padrão para Testes

```python
def test_isolamento(tmp_path):
    """Teste usa tmp_path para isolamento total."""
    from infra.webhooks.adapters.sqlite_job_queue import SQLiteJobQueue

    db_path = tmp_path / "test_jobs.db"
    queue = SQLiteJobQueue(db_path=db_path)
    # Teste com isolamento completo
```

### Fixtures Recomendadas

```python
# tests/conftest.py
@pytest.fixture
def mock_job_queue():
    """Job Queue mock para garantir isolamento em testes."""
    mock_queue = AsyncMock(spec=JobQueuePort)
    mock_queue.enqueue = AsyncMock(return_value="test-job-id")
    return mock_queue

@pytest.fixture
def isolated_job_queue(tmp_path):
    """Job queue REAL mas isolado em tmp_path."""
    from infra.webhooks.adapters.sqlite_job_queue import SQLiteJobQueue

    db_path = tmp_path / "test_jobs.db"
    queue = SQLiteJobQueue(db_path=db_path)
    return queue
```

### Verificação

Para garantir que testes não tocam produção:

```bash
# Deletar production DB antes dos testes
rm -f data/jobs.db
python -m pytest tests/ -v
# data/jobs.db NÃO deve ser recriado
```

### Configuração do pytest

**Localização do `tmp_path`:**
- **Padrão pytest:** `/tmp/pytest-of-user/pytest-XXX/` (temp do sistema)
- **Skybridge (ADR024):** `workspace/core/tmp_path/test_XXXXXX/`

**Override em `tests/conftest.py`:**

```python
@pytest.fixture
def tmp_path(tmp_path):
    """
    Override do tmp_path para usar workspace/core/tmp_path/.

    DOC: ADR024 - Temporários de teste ficam no workspace core.
    DOC: ADR024 - Limpo automaticamente pelo hook pós-commit.

    Isso facilita debug de testes (podemos inspecionar os .db)
    enquanto mantém isolamento do ambiente de produção.
    """
    from pathlib import Path
    import uuid

    # Usa workspace/core/tmp_path/ ao invés de /tmp/pytest-*
    custom_tmp_path = Path.cwd() / "workspace" / "core" / "tmp_path"
    custom_tmp_path.mkdir(parents=True, exist_ok=True)

    # Cria subdiretório único para este teste (preserva isolamento)
    test_tmp_path = custom_tmp_path / f"test_{uuid.uuid4().hex[:8]}"
    test_tmp_path.mkdir(exist_ok=True)

    return test_tmp_path
```

**Limpeza automática (versionado):**

```bash
# .githooks/post-commit (versionado no repositório)
# Configurar: git config core.hooksPath .githooks

TMP_PATH="workspace/core/tmp_path"
if [[ -d "$TMP_PATH" ]]; then
    rm -rf "$TMP_PATH" && mkdir -p "$TMP_PATH"
fi
```

**Setup inicial (clone do repositório):**

```bash
# Após clonar o repositório, configurar hooks:
git config core.hooksPath .githooks

# Verificar configuração:
git config core.hooksPath
# Saída: .githooks
```

**`.gitignore`:**

```gitignore
# Testes
.pytest_cache/
.coverage
htmlcov/
workspace/core/tmp_path/  # DOC: ADR024 - Temporários de testes (limpo pós-commit)
```

**Benefícios dessa configuração:**
1. **Debug facilitado** - Inspecionar `.db` durante desenvolvimento
2. **Não polui `/tmp/`** - Temporários ficam no workspace
3. **Limpeza automática** - Hook pós-commit mantém diretório limpo
4. **Não versionado** - `.gitignore` previne commits acidentais

## Decisões Relacionadas

- **Nome do banco:** `agent_executions.db` → `executions.db` (simplificação)
- **Localização:** Por workspace (`{workspace}/data/executions.db`)
- **Isolamento:** Cada instância tem suas próprias execuções de agentes
