---
name: task-helper
description: Auto-activates for Hadsteca task creation, management, template filling
version: 1.0.0
---

You have access to **Hadsteca Task System** knowledge.

## TRIGGERS
- User mentions "tarefas", "task", "tarefa Hadsteca"
- User wants to create/update task from clipboard/text
- User mentions "workspaces/futura/tarefas"
- User asks about task templates or formats

## KNOWLEDGE BASE

### Task Types
| Type | When to Use |
|------|-------------|
| `erro` | Bug fixes, errors, issues |
| `layout` | Report creation/modification |
| `feature` | New features, enhancements |
| `manutencao` | Refactor, cleanup, optimization |

### Structure (All Tasks)
1. **1. Request** - Problem/request context
2. **2. Analysis** - Evidence + technical checks
3. **3. Dev** - Human team fills
4. **4. Test** - Human team fills

### Layout Sub-Types
- `FIXO` - Hardcoded Delphi + SQL
- `DINAMICO` - ReportBuilder + SQL
- `PARAMETRIZAVEL` - User-configurable
- `DINAMICO_EDITAVEL` - Client can edit SQL

### File Locations
```
B:\_repositorios\Hadsteca\workspaces\futura\tarefas\
├── 3887501.md           # Simple task
└── 3887502/             # Workspace task
    ├── 3887502.md
    ├── code/
    ├── tests/
    └── docs/
```

### Key Fields
- **ID** = Task number (filename)
- **TYPE** = erro/layout/feature/manutencao
- **STATUS** = open/in_progress/done
- **SIGNATURE** = Always end with Sky signature

### When Task Has SQL
Generate SQL skeleton using `SQL_ExecuteBlockReturns.py` rules.

### When Task References Another
Add summary section with referenced task info.

## ACTIONS

When triggered:
1. Identify task type from context
2. Offer to create task using `/task` command
3. Gather required info interactively
4. Apply telegraphic template
5. Write to correct location

**Be helpful. Be brief. Get to done.**
