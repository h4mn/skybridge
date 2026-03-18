---
status: aceito
data: 2026-02-01
relacionado: ADR024
---

# PB013 — Trabalhando com Workspaces Multi-Instância

## Objetivo

Guia prático de como trabalhar com workspaces após a implementação da ADR024.

**Status:** ✅ Playbook pronto para uso pós-implementação

---

## Visão Geral

Workspaces permitem isolar completamente diferentes instâncias do Skybridge:

```
workspace/
├── core/           ← Instância principal (auto-evo)
├── trading/        ← Bot de trading (extensão)
└── futura/         ← Outro projeto
```

Cada workspace tem seus próprios:
- **Segredos** (`.env` com API keys)
- **Configurações** (`config.json`)
- **Dados** (`jobs.db`, `executions.db`)
- **Worktrees** (`worktrees/`)

---

## Setup Inicial

### 1. Primeira Execução (Auto-criação do `core`)

```bash
# Ao rodar o Skybridge pela primeira vez
python -m apps.server.main

# O workspace 'core' é criado automaticamente:
# ✓ workspace/core/.env
# ✓ workspace/core/.env.example
# ✓ workspace/core/config.json
# ✓ workspace/core/data/jobs.db
# ✓ workspace/core/data/executions.db
# ✓ workspace/core/worktrees/
```

**Arquivo `.workspaces` criado:**
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
    }
  }
}
```

### 2. Configurar `.env` do `core`

```bash
# Editar .env do workspace core
code workspace/core/.env

# Adicionar suas configurações:
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
```

---

## Criando Novas Instâncias

### Via CLI

```bash
# Criar nova instância
skybridge workspace create trading --name "Trading Bot"

# Resultado:
# ✓ workspace/trading/.env
# ✓ workspace/trading/.env.example
# ✓ workspace/trading/config.json
# ✓ workspace/trading/data/jobs.db
# ✓ workspace/trading/data/executions.db
# ✓ workspace/trading/worktrees/
```

### Via WebUI

1. Acessar página **Workspaces**
2. Clicar em **"Criar Workspace"**
3. Preencher nome, descrição
4. Definir caminho (padrão: `workspace/<nome>`)
5. Clicar em **"Criar"**

---

## Alternando Entre Workspaces

### Via CLI

```bash
# Listar workspaces disponíveis
skybridge workspace list
# core (workspace/core) [ACTIVE]
# trading (workspace/trading)

# Ativar workspace específico
skybridge workspace use trading

# Ver workspace ativo
skybridge workspace current
# trading
```

### Via WebUI

1. Usar **seletor de workspace** no topo da página
2. Escolher workspace desejado
3. Dashboard/métricas são atualizadas automaticamente

**Header automático:**
```javascript
// WebUI envia header em todas as requests
X-Workspace: trading
```

---

## Gerenciando Configurações

### Sincronizar workspace → worktree

```bash
# Criar worktree para um PR
skybridge worktree create github-pr-123 --from core

# Sincronizar configurações do core para a worktree
skybridge workspace config sync core --to github-pr-123 --include-env

# Resultado: github-pr-123/.env contém as mesmas vars do core
```

### Sincronizar worktree → workspace (novas configs)

```bash
# Durante desenvolvimento na worktree, você adiciona nova API key:
# NOVA_API_KEY=xyz em github-pr-123/.env

# Para levar essa nova chave de volta para o core:
skybridge workspace config sync github-pr-123 --to core --merge

# Resultado: NOVA_API_KEY é adicionada ao core/.env
#          Chaves existentes no core NÃO são sobrescritas
```

### Listar configurações

```bash
skybridge workspace config list core
# .env: 12 variáveis
# config.json: {"timeout": 300, "max_retries": 3}
```

### Comparar configurações

```bash
skybridge workspace config diff core trading
# Diferenças de .env:
#   - TRADING_API_KEY: presente apenas em trading
#   - OPENAI_API_KEY: valores diferentes
```

### Validar configurações

```bash
skybridge workspace config validate core
# ✓ .env: 12 variáveis
# ✓ config.json: válido
# ⚠ Aviso: GITHUB_TOKEN não definida
```

---

## Backup e Restore

### Backup de um workspace

```bash
# Via CLI
skybridge workspace backup core --output backups/core-20260201.tar.gz

# Inclui:
# - .env, .env.example, config.json
# - data/*.db
# - worktrees/
# - logs/
```

### Restore de um workspace

```bash
skybridge workspace restore backups/core-20260201.tar.gz

# Resultado:
# ✓ workspace/ restaurado
# ✓ Dados, configs e worktrees restaurados
```

### Via WebUI

1. Página **Workspaces**
2. Botão **"Backup"** no workspace desejado
3. Arquivo `.tar.gz` é gerado e baixado

---

## Deletando Workspaces

### Via CLI

```bash
# Deletar com backup automático
skybridge workspace delete trading --backup

# Deletar sem backup (cuidado!)
skybridge workspace delete trading --force

# Prompt de confirmação:
# ⚠ Você tem certeza? Isso vai deletar workspace/trading/ completamente.
# Type 'yes' to confirm: yes
# ✓ Workspace trading deletado
```

### Via WebUI

1. Página **Workspaces**
2. Botão **"Deletar"** no workspace
3. Confirmar com checkbox de segurança
4. Opcional: fazer backup antes

---

## API Multi-Tenant

### Usando cURL

```bash
# Requisição com workspace específico
curl -H "X-Workspace: trading" \
  http://localhost:8000/api/jobs

# Requisição sem header (usa 'core' como padrão)
curl http://localhost:8000/api/jobs
```

### Management API (sem workspace)

```bash
# Listar todos os workspaces
curl http://localhost:8000/api/workspaces

# Criar novo workspace
curl -X POST http://localhost:8000/api/workspaces \
  -H "Content-Type: application/json" \
  -d '{"name": "dev", "path": "workspace/dev"}'

# Detalhes de um workspace
curl http://localhost:8000/api/workspaces/trading
```

---

## Worktrees dentro de Workspaces

### Criar worktree

```bash
# Worktree dentro do workspace core
skybridge worktree create feature-x --workspace core

# Resultado:
# workspace/core/worktrees/feature-x/
```

### Sincronizar configs para worktree

```bash
# Copiar .env do workspace para a worktree
skybridge workspace config sync core --to feature-x --include-env

# A worktree agora tem acesso às mesmas APIs
```

---

## Troubleshooting

### Erro: "Workspace not found"

**Causa:** Header `X-Workspace` com workspace inexistente

**Solução:**
```bash
# Verificar workspaces disponíveis
skybridge workspace list

# Usar workspace válido
curl -H "X-Workspace: core" http://localhost:8000/api/jobs
```

### Erro: ".env não encontrado"

**Causa:** Workspace criado mas `.env` não configurado

**Solução:**
```bash
# Copiar template
cp workspace/core/.env.example workspace/core/.env

# Editar com suas chaves
code workspace/core/.env
```

### Merge com conflitos

**Causa:** Mesma chave com valores diferentes em workspaces

**Solução:**
```bash
# O comando pede confirmação interativa
skybridge workspace config sync worktree --to core --merge

# ⚠ Conflito em OPENAI_API_KEY:
#   worktree: sk-abc...
#   core:     sk-xyz...
#   Escolha: (1) manter worktree, (2) manter core, (3) editar
# > 1
```

### Worktrees criadas fora de workspaces

**Causa:** Setup antigo (pré-ADR024)

**Solução:** Migrar worktrees antigas para dentro do workspace
```bash
# Mover worktree antiga para workspace core
mv ../skybridge-auto/skybridge-github-123 workspace/core/worktrees/

# Sincronizar configurações
skybridge workspace config sync core --to skybridge-github-123
```

---

## Boas Práticas

### 1. Nomenclatura de Workspaces

- `core` → Instância principal (obrigatório)
- `trading` → Bot de trading
- `dev` → Ambiente de desenvolvimento
- `<projeto>` → Nome do projeto externo

### 2. Segredos

- ✅ Cada workspace tem seu próprio `.env`
- ✅ Nunca commitar `.env` (já está no `.gitignore`)
- ✅ Usar `.env.example` como template
- ❌ NÃO compartilhar `.env` entre workspaces

### 3. Isolamento de Dados

- ✅ Jobs de `core` NÃO aparecem em `trading`
- ✅ Worktrees de `trading` ficam em `workspace/trading/worktrees/`
- ✅ Backup/restore afeta apenas um workspace

### 4. Desenvolvimento

- ✅ Criar worktree para cada feature/PR
- ✅ Sincronizar configs do workspace pai para a worktree
- ✅ Ao adicionar nova API key na worktree, fazer `sync --merge` de volta

---

## Checklist de Setup

- [x] Rodar Skybridge pela primeira vez (auto-cria `core`)
- [x] Configurar `workspace/core/.env` com suas API keys
- [x] Testar WebUI com seletor de workspace
- [x] Criar workspace de teste (`trading`)
- [x] Alternar entre workspaces via CLI
- [x] Sincronizar configs entre workspace e worktree
- [x] Fazer backup de um workspace
- [x] Testar API multi-tenant com header `X-Workspace`

---

## Exemplos de Uso

### Desenvolvimento de Feature

```bash
# 1. Criar worktree para feature
skybridge worktree create feature-auth --workspace core

# 2. Sincronizar configs
skybridge workspace config sync core --to feature-auth

# 3. Adicionar nova API key durante desenvolvimento
# Editar workspace/core/worktrees/feature-auth/.env
# Adicionar: NEW_AUTH_API_KEY=xyz

# 4. Levar nova chave de volta para o core
skybridge workspace config sync feature-auth --to core --merge

# 5. Feature completa, deletar worktree
skybridge worktree delete feature-auth
```

### Projeto Externo

```bash
# 1. Criar workspace para projeto externo
skybridge workspace create futura \
  --name "Futura Project" \
  --path "/c/repos/futura/workspace/futura"

# 2. Configurar .env específico
code /c/repos/futura/workspace/futura/.env

# 3. Usar workspace
skybridge workspace use futura

# 4. Criar worktrees dentro desse workspace
skybridge worktree create feature-x --workspace futura
```

---

## Referências

- **ADR024:** Workspaces Multi-Instância com Isolamento de Dados
- **CLI:** `skybridge workspace --help`
- **API:** `/api/workspaces` (management)

---

> "Isolamento é liberdade — cada instância no seu ritmo." – made by Sky 🚀
