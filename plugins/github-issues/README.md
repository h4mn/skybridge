# GitHub Issues Plugin

Automate GitHub issue resolution via webhook-driven autonomous agents.

## Install

```bash
# Copy to Claude plugins folder
cp -r github-issues ~/.claude/plugins/

# Windows
xcopy /E /I github-issues C:\Users\SEU_USUARIO\.claude\plugins\github-issues
```

## Usage

### Resolve Issue
```
/resolve-issue #<issue_number>

# Examples
/resolve-issue #225
/resolve-issue #123
```

## Issue Types

| Type | Timeout | Description |
|------|---------|-------------|
| `hello-world` | 60s | Simple hello world example |
| `bug-simple` | 300s (5min) | Simple bug fix |
| `bug-complex` | 600s (10min) | Complex bug fix |
| `refactor` | 900s (15min) | Code refactoring |
| `generic` | 600s (10min) | Default issue resolution |

## Workflow

1. **Analyze Issue**
   - Parse issue title, body, and labels
   - Detect issue type from keywords
   - Identify affected files/components

2. **Create Worktree**
   - Create isolated worktree: `skybridge-fix-<issue_number>`
   - Checkout target branch

3. **Execute Solution**
   - Read relevant files
   - Implement fix based on issue type
   - Create new files if needed

4. **Commit Changes**
   - Telegraphic commit: `fix(<component>): <description>`
   - Include issue reference

5. **Create PR**
   - Generate PR description with issue summary
   - Reference original issue (#<number>)

6. **Cleanup**
   - Remove worktree after successful push

## Integration with Skybridge

This plugin integrates with the Skybridge webhook system (PRD013):

```python
# GitHub webhook → Job → Agent Facade → resolve-issue skill
```

Ref: `docs/prd/PRD013-webhook-autonomous-agents.md`

---

> "Automated resolution = happy maintainers" – made by Sky 🤖
