# Task Builder Plugin

Create Hadsteca tasks with **telegraphic templates**.

## Install

```bash
# Copy to Claude plugins folder
cp -r task-builder ~/.claude/plugins/

# Windows
xcopy /E /I task-builder C:\Users\SEU_USUARIO\.claude\plugins\task-builder
```

## Usage

### Interactive
```
/task
```

### Quick Create
```
/task <id> <type> <title>

/task 3887501 erro "Login não funciona"
/task 3887502 layout "Relatório de vendas"
/task 3887503 feature "Notificação por email"
```

### List & Export
```
/task list
/task export 3887501
```

## Task Types

| Type | Use For |
|------|---------|
| `erro` | Bug fixes |
| `layout` | Reports (CREATE/ALTER) |
| `feature` | New features |
| `manutencao` | Refactor/cleanup |

## Layout Sub-Types

| Type | Description |
|------|-------------|
| `FIXO` | Delphi hardcoded |
| `DINAMICO` | ReportBuilder |
| `PARAMETRIZAVEL` | User-configurable |
| `EDITAVEL` | Client-editable SQL |

## Template Structure (Telegraphic)

```markdown
# [TITLE]

**ID:** [ID]
**TYPE:** [type]
**STATUS:** open

## 1 Request
## 2 Analysis
## 3 Dev      <- Humanos
## 4 Test     <- Humanos

> "Signature" – made by Sky
```

## Settings

Edit `.claude/plugin-name.local.md`:

```yaml
tarefas_path: B:/_repositorios/Hadsteca/workspaces/futura/tarefas
default_type: erro
```

## File Output

**Simple:** `tarefas/3887501.md`
**Workspace:** `tarefas/3887501/3887501.md` + code/tests/docs

---

> "Brevity is the soul of task creation." – made by Sky [📋]
