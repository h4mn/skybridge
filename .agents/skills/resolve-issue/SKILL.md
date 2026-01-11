---
name: resolve-issue
description: Resolve GitHub issue automatically in isolated worktree
version: 1.0.0
---

# Resolve GitHub Issue

This skill automatically resolves GitHub issues by creating isolated worktrees, implementing fixes, and creating pull requests.

## When to use

This skill should be activated when:
- User explicitly invokes: `/resolve-issue <issue_number>`
- Background worker processes `issues.opened` webhook event
- Issue has labels: `good-first-issue`, `bug`, `enhancement`

## Context Provided

The agent will receive:
- `worktree_path`: Path to isolated worktree (ex: `../skybridge-github-225`)
- `issue_number`: GitHub issue number (ex: `225`)
- `issue_title`: Issue title (ex: "Fix: alinhar versões da CLI e API")
- `issue_body`: Issue description (markdown formatted)
- `repo_name`: Repository name (ex: "h4mn/skybridge")

## What to do

### 1. Analyze the Issue

Read the issue details carefully:
- Understand the problem or feature request
- Identify the scope (is it trivial vs complex?)
- Look for clues in labels, comments, or issue template

### 2. Explore the Codebase

Use the Read tool to examine relevant files:
- Search for related code using Grep
- Understand existing patterns and conventions
- Look for similar implementations

### 3. Implement the Solution

Make necessary code changes:
- Follow existing code style and patterns
- Add tests if appropriate
- Ensure no regressions

### 4. Test the Changes

Run existing tests to ensure no regressions:
- `pytest` or `poetry run pytest`
- Test the specific fix/feature
- Verify edge cases

### 5. Commit and Push

Stage and commit changes:
```bash
git add .
git commit -m "fix: resolve issue #N - <brief description>"
git push
```

### 6. Create Pull Request

Use gh CLI to create PR:
```bash
gh pr create --title "Fix #N" --body "Resolves #N"
```

Include relevant issue details in PR description:
- Link to issue
- Summary of changes
- Testing performed

### 7. Validate Worktree

Call `safe_worktree_cleanup` before finishing:
```python
from skybridge.core.contexts.agents.worktree_validator import safe_worktree_cleanup

result = safe_worktree_cleanup(worktree_path, dry_run=True)
if result["can_remove"]:
    # Worktree is clean, recommend cleanup
    print("Worktree clean and ready for removal")
else:
    # Worktree has uncommitted changes
    print(f"Warning: {result['message']}")
```

## Example

```bash
# User invokes:
/resolve-issue 225

# Agent receives context:
worktree_path="../skybridge-github-225"
issue_number=225
issue_title="Fix: alinhar versões da CLI e API com ADR012"
issue_body="## Problema\nAs versões não estão centralizadas..."
repo_name="h4mn/skybridge"

# Agent executes steps 1-7 above...
```

## Success Criteria

- Issue is resolved with working code
- Changes are committed and pushed to branch
- Pull request is created with proper formatting
- Worktree is clean and ready for cleanup
- All tests pass

## Safety Checks

- **Dry-run before cleanup**: Always call `safe_worktree_cleanup(worktree_path, dry_run=True)` before recommending removal
- **Validate changes**: Run tests before committing
- **Follow conventions**: Match existing code style and patterns
- **Communicate clearly**: Explain what was changed and why

## Limitations

This skill works best for:
- Trivial bugs (typos, simple fixes)
- Version updates
- Configuration changes
- Documentation improvements

For complex issues, the agent should:
- Ask for clarification
- Break down into smaller tasks
- Recommend human review

## Integration with PRD013

This skill is part of the Webhook-Driven Autonomous Agents system (PRD013):
- Triggered by GitHub webhook: `issues.opened`
- Executes in isolated worktree
- Creates PR automatically
- Validates cleanup before removal

---

> "Autonomy requires responsibility - validate before cleanup" – made by Sky 🚀
