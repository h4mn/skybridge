# Study: PR Automation Skill for Skybridge Agents

**Status:** Estudo Preliminar
**Date:** 2026-01-11
**Author:** Sky

---

## 1. Objective

Define a reusable skill/pattern for automating PR creation workflow in Skybridge, based on the observed sequence used for `docs/webhook-autonomous-agents` branch.

---

## 2. Observed Pattern (This Session)

### Step 1: Status Assessment
```bash
# Show current branch, status, worktree
git branch --show-current
git status --short
git worktree list
```

### Step 2: Organize Features Temporally
- Identify 3 main features by date and dependency
- Order: Base → Integration → Application
- This case: Snapshot (2025-12-28) → Agent Interface (2026-01-10) → Webhooks (2026-01-10)

### Step 3: Generate PR Summary
- Create `PR_DESCRIPTION.md` with:
  - Summary of features
  - Architecture diagram
  - Version bump justification
  - Breaking changes notice

### Step 4: Create Telegraphic Commits
```bash
# Commit 1: Feature #1 (base)
git add <files>
git commit -m "feat(snapshot): ADR015, ADR017, PRD011, SPEC007"

# Commit 2: Feature #2 (integration)
git add <files>
git commit -m "feat(agent-interface): SPEC008 + agent infrastructure"

# Commit 3: Feature #3 (application)
git add <files>
git commit -m "feat(webhooks): autonomous agents system (PRD013)"

# Commit 4-7: Docs, tests, integration, cleanup
...
```

### Step 5: Version Bump
```bash
# Update VERSION file (Single Source of Truth)
SKYBRIDGE_VERSION=0.2.5 → 0.3.0
KERNEL_API_VERSION=0.2.5 → 0.3.0
OPENAPI_CONTRACT_VERSION=0.2.5 → 0.3.0

git add VERSION
git commit -m "chore(release): bump version to 0.3.0"
```

### Step 6: Verify/Sync Main Repository
```bash
cd ../skybridge
git fetch origin
git log --oneline --all --graph

# If main is behind:
git merge origin/main
# If main is ahead (rare):
git push origin main
```

### Step 7: Create PR
```bash
# Push to origin
git push origin docs/webhook-autonomous-agents

# Create PR via MCP or gh
gh pr create --title "feat: Webhook Autonomous Agents + Snapshot Service + AI Agent Interface" \
  --body-file PR_DESCRIPTION.md \
  --base main
```

### Step 8: Finalize Worktree/Branch
```bash
# After PR is merged:
git checkout main
git worktree remove ../skybridge-docs-webhook-agents
git branch -d docs/webhook-autonomous-agents
```

---

## 3. Proposed Skill: `/create-pr`

### Input Schema
```json
{
  "features": [
    {
      "name": "Snapshot Service",
      "date": "2025-12-28",
      "description": "Platform observability service",
      "files": ["docs/adr/ADR015*", "..."]
    },
    {
      "name": "AI Agent Interface",
      "date": "2026-01-10",
      "description": "Agent contract for AI subprocesses",
      "files": ["docs/spec/SPEC008*", "..."]
    }
  ],
  "version_bump": {
    "from": "0.2.5",
    "to": "0.3.0",
    "reason": "minor - feature additions"
  },
  "pr_title": "feat: Webhook Autonomous Agents + Snapshot Service + AI Agent Interface",
  "base_branch": "main"
}
```

### Execution Steps (Agent Thinking)
```
Thinking 1: "Assessing current git status..."
Thinking 2: "Organizing features by temporal order and dependency..."
Thinking 3: "Generating PR_DESCRIPTION.md with feature summary..."
Thinking 4: "Creating telegraphic commits grouped by feature..."
Thinking 5: "Bumping VERSION file (Single Source of Truth)..."
Thinking 6: "Verifying main repository status..."
Thinking 7: "Pushing and creating PR..."
Thinking 8: "Finalizing worktree cleanup..."
```

### Output
```json
{
  "success": true,
  "pr_url": "https://github.com/h4mn/skybridge/pull/XXX",
  "branch_merged": false,
  "worktree_removed": false,
  "commits_created": 8,
  "files_changed": 72,
  "message": "PR created successfully, ready for review"
}
```

---

## 4. Automation Opportunities

### Fully Automatable
- [ ] Status assessment (`git status`, `git log`)
- [ ] Temporal ordering (parse file dates, doc headers)
- [ ] PR description generation (template with feature list)
- [ ] Telegraphic commits (group files by feature)
- [ ] Version bump (update VERSION file)
- [ ] PR creation via MCP GitHub

### Human-in-the-Loop
- [ ] Commit message refinement (agent suggests, human approves)
- [ ] PR description review (human edits before publish)
- [ ] Merge decision (human approves)

---

## 5. Key Patterns Observed

### Commit Message Pattern
```
<scope>(<component>): <brief description>

- Details bullet 1
- Details bullet 2
- References: PRD0XX, SPEC0XX, ADR0XX
```

### Version Bump Pattern
- **Major (X.0.0):** Breaking changes
- **Minor (0.X.0):** Feature additions
- **Patch (0.0.X):** Bug fixes

### Telegraphic Style
- Short, descriptive subjects
- Imperative mood ("add", "feat", "fix")
- Scope prefixes: `feat()`, `docs()`, `chore()`, `test()`

---

## 6. Next Steps

1. **SPEC009:** Define `/create-pr` skill contract
2. **Implement:** Create agent handler for PR automation
3. **Test:** Run on similar branch (e.g., `feature/mcp-server`)
4. **Refine:** Adjust based on feedback
5. **Document:** Add to `.agents/skills/create-pr/SKILL.md`

---

## 7. References

- **PRD013:** Webhook Autonomous Agents
- **SPEC008:** AI Agent Interface
- **ADR012:** Versionamento Strategy
- **This Session:** `docs/webhook-autonomous-agents` branch (8 commits, 72 files)

---

> "Automating the automation meta-cycle is the final frontier" – made by Sky 🤖
