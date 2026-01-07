# Snapshot Handlers - Guia Prático para Sky (GPT Custom)

## O Que São Snapshots?

**Snapshot** = "foto" da estrutura de um domínio em um momento específico.
- **FileOps snapshot:** estrutura de arquivos (pastas, arquivos, extensões, tamanhos)
- **Tasks snapshot:** estado das tarefas/jobs
- **Health snapshot:** saúde do sistema

**Diff** = comparação entre dois snapshots, mostrando o que mudou.

---

## Handler: `snapshot.capture`

### Para Que Serve?

Captura uma visão estrutural de um domínio para:
- Documentar estado atual do código
- Criar baseline antes de mudanças
- Analisar evolução do projeto
- Detectar arquivos órfãos ou duplicados

### Como Usar

#### 1. Obter Ticket
```http
GET /ticket?method=snapshot.capture
Authorization: Bearer SEU_TOKEN
```

#### 2. Enviar Envelope
```http
POST /envelope
Authorization: Bearer SEU_TOKEN
Content-Type: application/json

{
  "ticket_id": "<ticket-do-passo-1>",
  "detail": {
    "context": "snapshot",
    "action": "capture",
    "subject": "fileops",
    "payload": {
      "target": "B:\\_repositorios\\skybridge",
      "depth": 5,
      "include_extensions": [".py", ".md"],
      "exclude_patterns": ["*/venv/*", "*/.git/*", "*/__pycache__/*"]
    }
  }
}
```

### Parâmetros do Payload

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `subject` | string | ✅ | Domínio: `fileops`, `tasks`, `health` |
| `target` | string | ✅ | Caminho para observar (para fileops) |
| `depth` | int | ❌ | Profundidade da captura (padrão: 5) |
| `include_extensions` | string[] | ❌ | Filtra apenas estas extensões |
| `exclude_patterns` | string[] | ❌ | Exclui padrões (glob) |
| `metadata` | object | ❌ | Tags customizadas (tag, description) |

### Resposta de Sucesso

```json
{
  "ok": true,
  "id": "abc123",
  "result": {
    "snapshot_id": "snap_20250128_153200_a3f9b1e2",
    "timestamp": "2025-01-28T15:32:00Z",
    "subject": "fileops",
    "metadata": {
      "total_files": 147,
      "total_dirs": 32,
      "total_size": 2048000,
      "git_hash": "abc123def",
      "git_branch": "main"
    },
    "structure": {
      "src": {
        "skybridge": { ... }
      }
    },
    "storage_path": "workspace/skybridge/snapshots/..."
  }
}
```

### Exemplos Práticos

#### Snapshot Completo do Projeto
```json
{
  "ticket_id": "...",
  "detail": {
    "context": "snapshot",
    "action": "capture",
    "subject": "fileops",
    "payload": {
      "target": ".",
      "depth": 10
    }
  }
}
```

#### Snapshot Apenas Python
```json
{
  "ticket_id": "...",
  "detail": {
    "context": "snapshot",
    "action": "capture",
    "subject": "fileops",
    "payload": {
      "target": "src",
      "depth": 5,
      "include_extensions": [".py"]
    }
  }
}
```

#### Snapshot com Tag (para marcar versão)
```json
{
  "ticket_id": "...",
  "detail": {
    "context": "snapshot",
    "action": "capture",
    "subject": "fileops",
    "payload": {
      "target": ".",
      "metadata": {
        "tag": "v1.0.0",
        "description": "Release inicial"
      }
    }
  }
}
```

---

## Handler: `snapshot.compare`

### Para Que Serve?

Compara dois snapshots do mesmo domínio para:
- Ver o que mudou entre dois commits
- Identificar arquivos adicionados/removidos
- Calcular delta de tamanho
- Gerar relatório de mudanças

### Como Usar

#### 1. Obter Ticket
```http
GET /ticket?method=snapshot.compare
Authorization: Bearer SEU_TOKEN
```

#### 2. Enviar Envelope
```http
POST /envelope
Authorization: Bearer SEU_TOKEN
Content-Type: application/json

{
  "ticket_id": "<ticket-do-passo-1>",
  "detail": {
    "context": "snapshot",
    "action": "compare",
    "subject": "fileops",
    "payload": {
      "old_snapshot_id": "snap_20250127_100000_x1y2z3w4",
      "new_snapshot_id": "snap_20250128_153200_a3f9b1e2",
      "format": "markdown"
    }
  }
}
```

### Parâmetros do Payload

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `old_snapshot_id` | string | ✅ | ID do snapshot anterior |
| `new_snapshot_id` | string | ✅ | ID do snapshot posterior |
| `format` | string | ❌ | `json`, `markdown` ou `html` (padrão: json) |

### Resposta de Sucesso

```json
{
  "ok": true,
  "id": "abc123",
  "result": {
    "diff_id": "diff_20250128_153250_a3f9b1e2",
    "old_snapshot": "snap_20250127_100000_x1y2z3w4",
    "new_snapshot": "snap_20250128_153200_a3f9b1e2",
    "summary": {
      "added_files": 12,
      "removed_files": 3,
      "modified_files": 8,
      "added_dirs": 2,
      "removed_dirs": 0,
      "size_delta": 45120
    },
    "changes": [
      {
        "type": "added",
        "path": "src/new_feature.py"
      },
      {
        "type": "removed",
        "path": "old/deprecated.py"
      },
      {
        "type": "modified",
        "path": "README.md",
        "size_delta": 234
      }
    ],
    "report_path": "workspace/skybridge/diffs/..."
  }
}
```

### Formatos de Saída

| Formato | Descrição | Uso |
|---------|-----------|-----|
| `json` | Estruturado, processável | APIs, automação |
| `markdown` | Legível, formatado | Documentação, humanos |
| `html` | Visual, colorido | Relatórios web |

---

## Handler: `snapshot.list`

### Para Que Serve?

Lista todos os snapshots existentes para um domínio, permitindo:
- Descobrir snapshots disponíveis para comparação
- Ver histórico de capturas
- Identificar snapshots com tags específicas

### Como Usar

#### 1. Obter Ticket
```http
GET /ticket?method=snapshot.list
Authorization: Bearer SEU_TOKEN
```

#### 2. Enviar Envelope
```http
POST /envelope
Authorization: Bearer SEU_TOKEN
Content-Type: application/json

{
  "ticket_id": "<ticket-do-passo-1>",
  "detail": {
    "context": "snapshot",
    "action": "list",
    "subject": "fileops"
  }
}
```

### Parâmetros do Payload

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `subject` | string | ✅ | Domínio: `fileops`, `tasks`, `health` |

### Resposta de Sucesso

```json
{
  "ok": true,
  "id": "abc123",
  "result": {
    "subject": "fileops",
    "total": 5,
    "snapshots": [
      {
        "snapshot_id": "snap_20250128_153200_a3f9b1e2",
        "timestamp": "2025-01-28T15:32:00Z",
        "target": "B:\\_repositorios\\skybridge",
        "tag": "v1.0.0"
      },
      {
        "snapshot_id": "snap_20250127_100000_x1y2z3w4",
        "timestamp": "2025-01-27T10:00:00Z",
        "target": "B:\\_repositorios\\skybridge",
        "tag": ""
      },
      {
        "snapshot_id": "snap_20250126_153000_b2c3d4e5",
        "timestamp": "2025-01-26T15:30:00Z",
        "target": "B:\\_repositorios\\skybridge",
        "tag": "before-refactor"
      }
    ]
  }
}
```

### Observações

- Snapshots são retornados **ordenados por timestamp** (mais recente primeiro)
- O campo `tag` é vazio (`""`) se o snapshot não foi taggeado
- Use os `snapshot_id` retornados para comparar via `snapshot.compare`

---

## Workflow Típico: Analisar Mudanças

### Cenário A: "Quero ver o que mudou desde ontem" (Criando Novos Snapshots)

```bash
# 1. Capturar snapshot antes das mudanças
GET /ticket?method=snapshot.capture
POST /envelope { "subject": "fileops", "payload": {"target": ".", "metadata": {"tag": "before-refactor"}} }
# → snapshot_id: "snap_before"

# ... (mudanças são feitas no código) ...

# 2. Capturar snapshot depois das mudanças
GET /ticket?method=snapshot.capture
POST /envelope { "subject": "fileops", "payload": {"target": ".", "metadata": {"tag": "after-refactor"}} }
# → snapshot_id: "snap_after"

# 3. Comparar os dois
GET /ticket?method=snapshot.compare
POST /envelope {
  "old_snapshot_id": "snap_before",
  "new_snapshot_id": "snap_after",
  "format": "markdown"
}
```

### Cenário B: "Quero comparar os dois snapshots mais recentes" (Usando Existentes)

```bash
# 1. Listar snapshots disponíveis
GET /ticket?method=snapshot.list
POST /envelope { "subject": "fileops" }
# → Retorna: snap_20250128_153200, snap_20250127_100000, snap_20250126_153000

# 2. Pegar os dois mais recentes e comparar
GET /ticket?method=snapshot.compare
POST /envelope {
  "old_snapshot_id": "snap_20250127_100000",
  "new_snapshot_id": "snap_20250128_153200",
  "format": "markdown"
}
```

### Cenário C: "Quero encontrar um snapshot marcado com tag específica"

```bash
# 1. Listar snapshots
GET /ticket?method=snapshot.list
POST /envelope { "subject": "fileops" }

# 2. Procurar na resposta por tag: "v1.0.0"
# → Encontra: snap_20250128_153200 com tag "v1.0.0"

# 3. Usar o snapshot_id encontrado para comparar
```

---

## Dicas para Sky (GPT Custom)

### Quando Usar Snapshot?

- **Antes de refatorar:** Crie baseline
- **Depois de implementar:** Compare para ver impacto
- **Para discovery:** Mapear estrutura de código legado
- **Para auditoria:** Verificar o que foi adicionado/removido

### Melhores Práticas

1. **Sempre use tags** para snapshots importantes:
   ```json
   "metadata": {"tag": "before-refactor", "description": "Estado antes de refatorar X"}
   ```

2. **Exclua ruído** (venv, node_modules, __pycache__):
   ```json
   "exclude_patterns": ["*/venv/*", "*/node_modules/*", "*/__pycache__/*"]
   ```

3. **Use depth apropriado:**
   - `depth=3`: Superficial (apenas estrutura de alto nível)
   - `depth=5`: Normal (padrão)
   - `depth=10`: Profundo (todos os subdiretórios)

4. **Combine com fileops.read:**
   - Use snapshot para identificar arquivos interessantes
   - Use fileops.read para ler conteúdo específico

### Exemplo de Relatório para Usuário

```
📸 SNAPSHOT: Estrutura do Projeto

Executado: 2025-01-28T15:32:00Z
Subject: fileops
Target: B:\_repositorios\skybridge

📊 ESTATÍSTICAS:
- Arquivos: 147
- Diretórios: 32
- Tamanho total: 2.05 MB
- Branch: main

📁 ESTRUTURA PRINCIPAL:
src/skybridge/
  ├── core/ (45 arquivos .py)
  ├── platform/ (38 arquivos .py)
  ├── infra/ (12 arquivos .py)
  └── kernel/ (8 arquivos .py)

docs/ (42 arquivos .md)

💡 OBSERVAÇÕES:
- Maior concentração em core/
- Documentação extensa em docs/
- Nenhum arquivo de teste encontrado (investigar)
```

---

## Troubleshooting

### Erro: "target is required for fileops"
**Solução:** Sempre especifique `target` no payload quando subject=`fileops`

### Erro: "Unsupported subject: xyz"
**Solução:** Subjects válidos são: `fileops`, `tasks`, `health`

### Erro: "Snapshots need to be from same subject"
**Solução:** Para comparar, ambos snapshots devem ter o mesmo subject

### Snapshot demora muito
**Solução:** Reduza `depth` ou adicione mais `exclude_patterns`

---

> "Quem não conhece seu passado, está condenado a repeti-lo." – made by Sky 📸
