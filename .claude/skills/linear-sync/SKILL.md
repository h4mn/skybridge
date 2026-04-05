---
name: linear-sync
description: Use when creating, updating, or searching Linear issues, or organizing roadmap with milestones and labels
---

# Linear Sync

## Overview

**Gerencia issues Linear com organização por labels e hierarquia.**

## Operations

### Buscar
```
linear_search(query="discord", status="Backlog", limit=5)
```

### Criar (1 ou batch)
```
linear_create(
  title: "Setup Discord Bot",
  priority: 2,
  labels: ["change:discord-bot", "scope:api"]
)
```

### Atualizar
```
linear_update(id="SKY-39", status="In Progress", comment="Iniciando...")
```

### Milestone
```
linear_milestone(name="Discord MVP", target="2026-05-01", issues=["SKY-39"])
```

## Organização

### Hierarquia
```
Milestone → Change → Phase → Task
```

### Labels
| Label | Uso | Exemplo |
|-------|-----|---------|
| `change:xxx` | Nome da feature | `change:discord-bot` |
| `scope:xxx` | Área técnica | `scope:api`, `scope:ui` |
| `priority:xxx` | Urgência | `priority:urgent`, `priority:high` |

### Convenção de Nomes
```
[CHANGE] Discord Bot MVP
  └── [PHASE-1] Setup
       └── [TASK] Ambiente Discord
```

## Sync Codebase-Roadmap

### Detectando Drift (Manual)

Ao revisar código vs Linear:
1. **Issue existe?** → Se não, criar
2. **Status correto?** → Atualizar se divergente
3. **Labels corretas?** → Ajustar se mudou escopo
4. **Comentários atualizados?** → Documentar decisões

### Checklist de Sincronização
```
[ ] Issue criada para a change
[ ] Labels aplicadas (change, scope, priority)
[ ] Status atualizado ao começar/terminar
[ ] Comentário com resumo ao finalizar
[ ] Milestone associado se aplicável
```

### Subissues para Fases
```
SKY-39 [CHANGE] Discord Bot
├── SKY-40 [PHASE-1] Setup
├── SKY-41 [PHASE-2] Core
└── SKY-42 [PHASE-3] Polish
```

## Quick Reference

| Ação | Comando |
|------|---------|
| Buscar | `linear_search(query, status?, limit?)` |
| Criar | `linear_create(title, priority?, labels?)` |
| Batch | `linear_create([{title, priority, labels}, ...])` |
| Atualizar | `linear_update(id, status?, comment?)` |
| Milestone | `linear_milestone(name, target, issues)` |

## Common Mistakes
- ❌ Criar issues sem label `change:xxx`
- ❌ Esquecer de atualizar status ao começar/terminar
- ❌ Não comentar decisões importantes na issue
- ❌ Milestone sem data alvo
- ❌ Usar emojis nos títulos de issues, milestones ou tasks

---

**Nota:** Esta skill é aberta para melhorias evolutivas. À medida que o processo amadurece, considere adicionar:
- Integração com OpenSpec para validação automática
- ADRs para rastreabilidade de decisões
- Custom Fields do Linear para dados estruturados
- Snapshots para detecção automática de drift

---
*made by Sky ✨*
