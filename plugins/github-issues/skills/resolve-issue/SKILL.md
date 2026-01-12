---
name: resolve-issue
description: Resolução automática de issues via GitHub webhooks
version: 1.0.0
---

You have access to **GitHub Issue Resolution** automation system.

## TRIGGERS

- User invokes `/resolve-issue #<issue_number>`
- GitHub webhook sends `issues.opened` or `issues.reopened` event
- Issue has labels: `automated`, `bug`, `enhancement`
- Issue is assigned to bot/automation

## KNOWLEDGE BASE

### Issue Types
| Type | Detection Criteria | Action |
|------|-------------------|--------|
| `hello-world` | Keywords: "hello", "simple", "example" | Create hello_world.py |
| `bug-simple` | Keywords: "fix", "bug", "error" + complexity "simple" | Simple bug fix |
| `bug-complex` | Keywords: "fix", "bug", "error" + complexity "complex" | Complex bug fix |
| `refactor` | Keywords: "refactor", "cleanup", "optimize" | Code refactoring |
| `generic` | Default fallback | Generic issue resolution |

### Timeout Configuration
| Skill | Timeout | Justification |
|-------|---------|---------------|
| hello-world | 60s | Simple, should be fast |
| bug-simple | 300s (5min) | Simple bug fix |
| bug-complex | 600s (10min) | Complex bug fix |
| refactor | 900s (15min) | Refactoring task |
| resolve-issue | 600s (10min) | Default for issues |

### Workflow
1. **Analyze Issue**
   - Parse issue title, body, and labels
   - Detect issue type from keywords
   - Identify affected files/components

2. **Create Worktree**
   - Create isolated worktree: `skybridge-fix-<issue_number>`
   - Checkout target branch (main or specified)

3. **Execute Solution**
   - Read relevant files
   - Implement fix based on issue type
   - Create new files if needed
   - Delete unnecessary files

4. **Commit Changes**
   - Create telegraphic commit message
   - Format: `fix(<component>): <description>`
   - Include issue reference in body

5. **Create PR**
   - Generate PR description with issue summary
   - Reference original issue (#<number>)
   - Set appropriate labels

6. **Cleanup**
   - Remove worktree after successful push
   - Log execution metrics

### AgentResult Structure
```json
{
  "success": true,
  "changes_made": true,
  "files_created": ["hello_world.py"],
  "files_modified": ["__init__.py"],
  "files_deleted": [],
  "commit_hash": "abc123",
  "pr_url": "https://github.com/h4mn/skybridge/pull/123",
  "message": "Issue resolved",
  "issue_title": "Fix version alignment",
  "output_message": "Aligned versions to 0.2.5",
  "thinkings": [
    {"step": 1, "thought": "Analyzing issue...", "timestamp": "...", "duration_ms": 1500},
    {"step": 2, "thought": "Reading __init__.py...", "timestamp": "...", "duration_ms": 300}
  ]
}
```

### XML Streaming Protocol
When communicating with Skybridge via XML:

```xml
<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">Analisando issue #225...</parametro>
  <parametro name="nivel">info</parametro>
</skybridge_command>
```

### Error Handling
- **Timeout:** Return `AgentResult` with `success: false`, `AgentState.TIMED_OUT`
- **Git Conflict:** Return error message, stop execution
- **Missing Files:** Log warning, continue with available files
- **Execution Failure:** Return `AgentResult` with `error_type` classification

## ACTIONS

When `/resolve-issue` is triggered:

1. **Parse Issue Number**
   - Extract from `#<number>` format
   - Fetch issue details via GitHub API

2. **Detect Issue Type**
   - Scan title/body for keywords
   - Check labels for hints
   - Default to `generic` if uncertain

3. **Create Worktree**
   - Execute: `git worktree add ../skybridge-fix-<number> -b fix-<number>`
   - Verify worktree creation

4. **Spawn Agent**
   - Use `AgentFacade.spawn()` with skill type
   - Pass issue context, worktree path
   - Monitor execution with timeout

5. **Process Result**
   - On success: Log metrics, cleanup worktree
   - On failure: Log error, retain worktree for debugging
   - Update issue status with PR link

6. **Metrics**
   - Log execution duration
   - Track success/failure rate per issue type
   - Report timeout incidents

## BEST PRACTICES

- **Always** verify issue type before acting
- **Never** modify production branches directly
- **Always** create isolated worktrees
- **Always** reference original issue in PR
- **Prefer** small, focused commits
- **Always** cleanup worktrees on success
- **Never** ignore errors silently

---

> "Automated resolution = happy maintainers" – made by Sky 🤖
