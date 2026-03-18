---
name: task
description: Create Hadsteca task (telegraphic)
allowed-tools: [Read, Write, Edit, AskUserQuestion]
---

## TELEGRAPHIC TASK BUILDER

**Usage:**
```
/task                           # Interactive mode
/task <id> <type> <title>       # Quick create
/task list                      # List tasks
/task export <id>               # Export task
```

**Types:** `erro` | `layout` | `feature` | `manutencao`

**Quick Create Examples:**
```
/task 3887501 erro "Login não funciona"
/task 3887502 layout "Relatório de vendas"
/task 3887503 feature "Notificação por email"
/task 3887504 manutencao "Refatorar UserService"
```

---

## TASK TEMPLATE (Telegraphic)

```markdown
# [TITLE]

**ID:** [ID]
**TYPE:** [erro|layout|feature|manutencao]
**STATUS:** [open|in_progress|done]

## 1. Request

**Original:**
```
[paste request here]
```

**Env:**
- Sys: [System]
- Ver: [Version]
- Client: [Client if applicable]
- Path: [Menu > Screen > Function]

**Problem:**
[One-line problem description]

**Situations:**

| Sit | Action | Problem |
|-----|--------|---------|
| 1 | [step] | [issue] |
| 2 | [step] | [issue] |

**Expected:**
[What success looks like]

---

## 2. Analysis

**Evidence:**
- [ ] Screenshot reviewed
- [ ] Logs analyzed
- [ ] Database checked
- [ ] Code inspected

**Technical:**

| Area | Check | Status |
|------|-------|--------|
| [Category1] | [what] | [ ] |
| [Category2] | [what] | [ ] |

**Hypotheses:**
1. **[H1]** [description]
2. **[H2]** [description]

**Verify:**
- [ ] [check1]
- [ ] [check2]

---

## 3. Dev

*Humanos fill this*

---

## 4. Test

*Humanos fill this*

---

> "Assinatura com frase" – made by Sky
```

---

## LAYOUT SUB-TYPES

**Creation:**
```
/task 3887501 layout "Sales Report" CREATE
```

**Alteration:**
```
/task 3887501 layout "Sales Report" ALTER
```

**Layout Types:**
- `FIXO` = Delphi hardcoded SQL
- `DINAMICO` = ReportBuilder SQL
- `PARAMETRIZAVEL` = User-configurable
- `DINAMICO_EDITAVEL` = SQL editable by client

---

## WORKSPACE MODE

**Simple:** `3887501.md` (in `/tarefas/`)
**Workspace:** `3887501/3887501.md` (with `/code`, `/tests`, `/docs`)

Auto-detect based on task complexity.

---

## PROCESS

1. Ask user for type (if not provided)
2. Gather required info interactively
3. Generate file at `tarefas_path`
4. Open in VSCode
5. Confirm completion

**Keep it brief. Get to done.**

> "Brevity is the soul of task creation." – Sky
