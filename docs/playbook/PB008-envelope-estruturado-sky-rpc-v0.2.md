---
status: proposta
data: 2025-12-27
relacionado:
  - PRD008-Sky-RPC-v0.2-envelope-estruturado.md
  - SPEC002-Sky-RPC-v0.2.md
  - ADR003-Glossário, Arquiteturas e Padrões Oficiais.md
---

# PB008 — Uso do Envelope Estruturado Sky-RPC v0.2

## 0) Propósito

Guia prático para desenvolvedores e integradores utilizarem o envelope estruturado do Sky-RPC v0.2, com exemplos concretos por **Bounded Context** (`fileops`, `tasks`) e casos de uso reais.

---

## 1) Visão do Envelope Estruturado

### 1.1 Estrutura

```yaml
detail:
  context:    # Contexto da operação (ex.: fileops.read)
  subject:    # Entidade-alvo (opcional)
  action:     # Ação específica
  payload:    # Dados da execução (min 1 propriedade)
```

### 1.2 Mapping para Bounded Contexts

| Context | Prefixo | Ações típicas |
|---------|---------|---------------|
| `fileops` | `fileops.` | `read`, `write`, `delete`, `list`, `move`, `copy` |
| `tasks` | `tasks.` | `create`, `update`, `promote`, `archive`, `list` |
| `health` | `health.` | `ping`, `status`, `version` |

---

## 2) FileOps Context — Usecases

### UC1 — Leitura Simples de Arquivo

**Cenário:** Ler conteúdo de um arquivo.

**Request:**
```json
{
  "ticket_id": "a3f9b1e2",
  "detail": {
    "context": "fileops.read",
    "subject": "README.md",
    "action": "read",
    "payload": {}
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "a3f9b1e2",
  "result": {
    "path": "README.md",
    "content": "# Skybridge...",
    "size": 1234,
    "encoding": "utf-8"
  }
}
```

---

### UC2 — Leitura com Encoding e Limites

**Cenário:** Ler arquivo com encoding específico e limite de linhas.

**Request:**
```json
{
  "ticket_id": "a3f9b1e2",
  "detail": {
    "context": "fileops.read",
    "subject": "logs/app.log",
    "action": "read",
    "payload": {
      "encoding": "utf-8",
      "line_limit": 100,
      "offset": 0
    }
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "a3f9b1e2",
  "result": {
    "path": "logs/app.log",
    "content": "[primeiras 100 linhas...]",
    "total_lines": 5420,
    "truncated": true
  }
}
```

---

### UC3 — Escrita de Arquivo

**Cenário:** Criar/sobrescrever arquivo com conteúdo.

**Request:**
```json
{
  "ticket_id": "b4c2d3f4",
  "detail": {
    "context": "fileops.write",
    "subject": "config/production.yaml",
    "action": "write",
    "payload": {
      "content": "server:\n  port: 8080\n",
      "encoding": "utf-8",
      "create_dirs": true,
      "backup": true
    }
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "b4c2d3f4",
  "result": {
    "path": "config/production.yaml",
    "bytes_written": 42,
    "backup_path": "config/production.yaml.bak"
  }
}
```

---

### UC4 — Listagem com Filtros

**Cenário:** Listar arquivos com filtros de extensão e ordenação.

**Request:**
```json
{
  "ticket_id": "c5d3e4f5",
  "detail": {
    "context": "fileops.list",
    "subject": "src/",
    "action": "list",
    "payload": {
      "pattern": "*.py",
      "recursive": true,
      "order_by": "modified",
      "order_desc": true,
      "limit": 50
    }
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "c5d3e4f5",
  "result": {
    "base_path": "src/",
    "files": [
      { "name": "main.py", "size": 2048, "modified": "2025-12-27T10:30:00Z" },
      { "name": "utils.py", "size": 1024, "modified": "2025-12-27T09:15:00Z" }
    ],
    "total": 42,
    "truncated": false
  }
}
```

---

### UC5 — Deleção com Confirm

**Cenário:** Deletar arquivo com confirmação de segurança.

**Request:**
```json
{
  "ticket_id": "d6e4f5g6",
  "detail": {
    "context": "fileops.delete",
    "subject": "temp/cache.json",
    "action": "delete",
    "payload": {
      "confirm": true,
      "permanent": false,
      "reason": "limpeza de cache"
    }
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "d6e4f5g6",
  "result": {
    "deleted": true,
    "trash_path": ".trash/temp/cache.json",
    "recovery_until": "2025-12-30T23:59:59Z"
  }
}
```

---

## 3) Tasks Context — Usecases

### UC6 — Criar Tarefa Simples

**Cenário:** Criar nova tarefa.

**Request:**
```json
{
  "ticket_id": "e7f5g6h7",
  "detail": {
    "context": "tasks.create",
    "action": "create",
    "payload": {
      "title": "Implementar envelope estruturado",
      "description": "Seguir PRD008",
      "priority": "high",
      "tags": ["backend", "sky-rpc"]
    }
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "e7f5g6h7",
  "result": {
    "task_id": "task_abc123",
    "status": "pending",
    "created_at": "2025-12-27T10:30:00Z",
    "event_id": "evt_001"
  }
}
```

---

### UC7 — Atualizar Tarefa

**Cenário:** Atualizar status e adicionar nota.

**Request:**
```json
{
  "ticket_id": "f8g6h7i8",
  "detail": {
    "context": "tasks.update",
    "subject": "task_abc123",
    "action": "update",
    "payload": {
      "status": "in_progress",
      "add_note": "Iniciando implementação do parser",
      "assignee": "dev@example.com"
    }
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "f8g6h7i8",
  "result": {
    "task_id": "task_abc123",
    "previous_status": "pending",
    "new_status": "in_progress",
    "note_id": "note_xyz789",
    "updated_at": "2025-12-27T11:00:00Z"
  }
}
```

---

### UC8 — Promover Tarefa

**Cenário:** Promover tarefa para backlog do sprint.

**Request:**
```json
{
  "ticket_id": "g9h7i8j9",
  "detail": {
    "context": "tasks.promote",
    "subject": "task_abc123",
    "action": "promote",
    "payload": {
      "target": "sprint_backlog",
      "sprint_id": "sprint_42",
      "estimate_points": 5
    }
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "g9h7i8j9",
  "result": {
    "task_id": "task_abc123",
    "promoted_from": "icebox",
    "promoted_to": "sprint_backlog",
    "sprint_id": "sprint_42",
    "position": 3
  }
}
```

---

### UC9 — Listar com Filtros Avançados

**Cenário:** Buscar tarefas por múltiplos critérios.

**Request:**
```json
{
  "ticket_id": "h0i8j9k0",
  "detail": {
    "context": "tasks.list",
    "action": "list",
    "payload": {
      "status": ["pending", "in_progress"],
      "tags": ["sky-rpc", "v0.2"],
      "assignee": "dev@example.com",
      "priority": "high",
      "limit": 20,
      "sort_by": "created_at",
      "sort_desc": true
    }
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "h0i8j9k0",
  "result": {
    "tasks": [
      {
        "task_id": "task_abc123",
        "title": "Implementar envelope estruturado",
        "status": "in_progress",
        "priority": "high",
        "tags": ["backend", "sky-rpc", "v0.2"]
      }
    ],
    "total": 8,
    "page": 1,
    "per_page": 20
  }
}
```

---

### UC10 — Arquivar Tarefa

**Cenário:** Arquivar tarefa concluída.

**Request:**
```json
{
  "ticket_id": "i1j9k0l1",
  "detail": {
    "context": "tasks.archive",
    "subject": "task_abc123",
    "action": "archive",
    "payload": {
      "reason": "Concluído e validado",
      "keep_events": true,
      "archive_to": "done/2025-12"
    }
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "i1j9k0l1",
  "result": {
    "task_id": "task_abc123",
    "archived_at": "2025-12-27T15:00:00Z",
    "archive_path": "done/2025-12/task_abc123.json",
    "events_count": 12
  }
}
```

---

## 4) Health Context — Usecases

### UC11 — Health Check Básico

**Cenário:** Verificar se o serviço está responsivo.

**Request:**
```json
{
  "ticket_id": "j2k0l1m2",
  "detail": {
    "context": "health.ping",
    "action": "ping",
    "payload": {}
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "j2k0l1m2",
  "result": {
    "status": "healthy",
    "timestamp": "2025-12-27T15:30:00Z",
    "uptime_seconds": 86400
  }
}
```

---

### UC12 — Health Check Detalhado

**Cenário:** Verificar saúde de componentes específicos.

**Request:**
```json
{
  "ticket_id": "k3l1m2n3",
  "detail": {
    "context": "health.status",
    "action": "check",
    "payload": {
      "components": ["database", "eventstore", "filesystem"],
      "timeout_ms": 5000
    }
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": "k3l1m2n3",
  "result": {
    "overall": "healthy",
    "components": {
      "database": { "status": "healthy", "latency_ms": 12 },
      "eventstore": { "status": "healthy", "latency_ms": 8 },
      "filesystem": { "status": "healthy", "latency_ms": 2 }
    }
  }
}
```

---

## 5) Padrões de Payload por Context

### 5.1 FileOps Payload Schema

```yaml
fileops.read:
  encoding?: string    # utf-8, latin-1, base64
  line_limit?: int
  offset?: int
  format?: string     # raw, json, yaml

fileops.write:
  content: string
  encoding?: string
  create_dirs?: bool
  backup?: bool
  overwrite?: bool

fileops.list:
  pattern?: string    # glob pattern
  recursive?: bool
  order_by?: string   # name, size, modified
  order_desc?: bool
  limit?: int

fileops.delete:
  confirm: bool
  permanent?: bool
  reason?: string
```

### 5.2 Tasks Payload Schema

```yaml
tasks.create:
  title: string
  description?: string
  priority?: string   # low, medium, high, critical
  tags?: string[]
  assignee?: string
  due_date?: string   # ISO 8601

tasks.update:
  status?: string     # pending, in_progress, done, blocked
  add_note?: string
  assignee?: string
  priority?: string

tasks.promote:
  target: string      # sprint_backlog, icebox, archive
  sprint_id?: string
  estimate_points?: int

tasks.list:
  status?: string[]
  tags?: string[]
  assignee?: string
  priority?: string
  limit?: int
  sort_by?: string
  sort_desc?: bool
```

---

## 6) Boas Práticas

### 6.1 Quando omitir `subject`

- **Omita** quando não há entidade específica (ex: `tasks.list` sem filtro)
- **Use** quando operar sobre entidade específica (ex: `fileops.read` de "README.md")

### 6.2 Quando `payload` vazio é aceitável

```json
{
  "detail": {
    "context": "fileops.read",
    "subject": "config.json",
    "action": "read",
    "payload": {}  // OK - defaults aplicados
  }
}
```

### 6.3 Validação de `minProperties: 1`

```json
// ❌ ERRO - payload vazio
"payload": {}

// ✅ OK - pelo menos uma propriedade
"payload": { "encoding": "utf-8" }
```

### 6.4 Compatibilidade Legada

**v0.1 (ainda suportado):**
```json
{
  "ticket_id": "abc",
  "detalhe": "README.md"
}
```

**v0.2 (recomendado):**
```json
{
  "ticket_id": "abc",
  "detail": {
    "context": "fileops.read",
    "subject": "README.md",
    "action": "read",
    "payload": {}
  }
}
```

---

## 7) Troubleshooting

### Erro 4220 — Campo obrigatório faltando

```json
{
  "code": 4220,
  "message": "Missing required field: payload",
  "data": { "field": "payload" }
}
```

**Solução:** Adicione `payload` com pelo menos uma propriedade.

### Erro 4221 — Payload vazio

```json
{
  "code": 4221,
  "message": "Payload cannot be empty (minProperties: 1)"
}
```

**Solução:** Adicione pelo menos uma propriedade em `payload`.

---

## 8) Checklist de Implementação

Para desenvolvedores implementando novos handlers:

- [ ] Definir `context` com padrão `<dominio>.<acao>`
- [ ] Documentar campos aceitos em `payload`
- [ ] Validar `minProperties: 1` em payload
- [ ] Retornar erro `4221` se payload vazio
- [ ] Adicionar exemplo em OpenAPI
- [ ] Testar com envelope legado e estruturado

---

> "Exemplo vale mais que mil palavras; código vale mais que mil exemplos." – made by Sky 📚
