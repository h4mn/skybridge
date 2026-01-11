# PR: Webhook Autonomous Agents + Snapshot Service + AI Agent Interface

## Summary

Implementa 3 funcionalidades principais que transformam a Skybridge em plataforma capaz de receber webhooks do GitHub e automaticamente criar agentes AI para resolver issues.

## Features

### 1. Snapshot Service (2025-12-28)
**Base:** PRD011, ADR015, SPEC007, ADR017

Serviço transversal de observabilidade estrutural:
- `platform/observability/snapshot/` - Captura e comparação de estados
- 4 extratores: fileops, git, health, tasks
- Sky-RPC handlers: `snapshot.capture`, `snapshot.compare`, `snapshot.list`
- Workspace em `workspace/skybridge/` com retenção configurável
- GitExtractor para validação de worktrees

### 2. AI Agent Interface (2026-01-10)
**Base:** SPEC008

Contrato técnico para agentes AI autônomos:
- `AgentFacade` - Interface abstrata para múltiplos agentes (Claude, Roo)
- `ClaudeCodeAdapter` - Implementação Claude Code CLI
- Protocolo XML bidirecional agente ↔ Skybridge
- Inferência de linguagem natural (proibido heurísticas)
- Timeouts configuráveis por skill
- Agent state management (CREATED → RUNNING → COMPLETED)

### 3. Webhook Autonomous Agents (2026-01-10)
**Base:** PRD013

Sistema completo de webhooks:
- `POST /webhooks/github` - Endpoint com signature verification (HMAC SHA-256)
- `WebhookProcessor` - Processa webhook → cria job
- `JobOrchestrator` - Executa job → cria worktree → captura snapshot → executa agente
- `WorktreeManager` - Gerencia ciclo de vida de worktrees
- Background worker integrado ao FastAPI lifespan
- Skill `/resolve-issue` documentada em `.agents/skills/`

## Architecture (DDD)

```
src/skybridge/
├── platform/observability/snapshot/   # Feature #1
├── core/contexts/webhooks/
│   ├── domain/                         # Feature #3
│   ├── application/
│   └── infrastructure/agents/          # Feature #2
└── infra/contexts/webhooks/adapters/
```

## Tests

- 50 testes para Webhook system (domain, adapters, application, integration)
- 38 testes para Agent infrastructure (TDD)
- Scripts de teste: `test_webhook.py`, `test_webhook_helloworld.py`

## Scripts

- `scripts/snapshot_capture.py` - Captura/compara snapshots
- `scripts/check_webhook_handler.py` - Testa handler
- `scripts/generate_webhook_secret.py` - Gera segredos HMAC

## Documentation

- PRD011, PRD013, SPEC007, SPEC008
- ADR015, ADR017, ADR018
- Reports: bounded-context-analysis, claude-code-cli-infra, knowledge-layer-rag

## Version

Bump: 0.2.5 → 0.3.0

## Breaking Changes

None. This is a net-new feature addition.

---

> "Webhooks trigger autonomous agents to resolve issues automatically" – made by Sky 🤖
