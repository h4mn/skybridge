# Inbox - Backlog de Ideias

## Overview

Sistema de captura rápida de ideias, inspirações e oportunidades de melhoria para o projeto Skybridge. Entradas são criadas como issues no projeto "Inbox" do Linear e processadas semanalmente.

## Workflow de Triagem

1. **Captura** → Ideia é registrada via `/inbox add <título>`
2. **Inbox** → Issue criada com expires em 60 dias
3. **Triagem Semanal** → Entradas são movidas/transformadas:
   - **Implementar** → Mover para projeto real ou criar issue com escopo
   - **Pesquisar** → Criar doc em `docs/research/` ou reference em `memory/`
   - **Arquivar** → Mover para status "Archived"
   - **Descartar** → Delete

## Como Usar

### Via Claude Code

```
/inbox add Adicionar suporte a Webhook no Paper Trading
```

### Via Discord (em desenvolvimento)

```
/inbox add Adicionar suporte a Webhook no Paper Trading
```

## Estrutura da Issue

Cada entrada do Inbox contém:

```markdown
**Fonte:** Claude Code | Discord #<canal>

---

**Ação sugerida:** Implementar | Pesquisar | Arquivar | Descartar
**Expires:** YYYY-MM-DD (60 dias)
```

## Labels

### fonte:*
- `fonte:discord` — Capturada via Discord slash command
- `fonte:claude-code` — Capturada via Claude Code skill
- `fonte:conversa` — Conversa presencial ou online
- `fonte:artigo` — Artigo, paper ou documentação
- `fonte:twitter` — Twitter/X
- `fonte:outro` — Outra fonte

### domínio:*
- `domínio:paper` — Paper Trading bot e arquitetura
- `domínio:discord` — Discord DDD, MCP e bots
- `domínio:autokarpa` — AutoKarpa e otimização de implementação
- `domínio:geral` — Geral, não específico de domínio

### ação:*
- `ação:implementar` — Requer implementação de código
- `ação:pesquisar` — Requer pesquisa e investigação
- `ação:arquivar` — Arquivar para referência futura
- `ação:descartar` — Descartar, não vale a pena

## Mapeamento Canais Discord → Domínios

| Canal/Padrão | Domínio |
|-------------|---------|
| `*-paper*`, `paper-trading`, `paper-dev` | paper |
| `*-discord*`, `discord-dev`, `discord-bots` | discord |
| `*-autokarpa*`, `autokarpa`, `autokarpa-dev` | autokarpa |
| (outro) | geral |

## Configuração

- **Projeto Linear:** Inbox - Backlog de Ideias (`02be2007-fd29-4f1c-8dc8-6b1d854a4a70`)
- **Expires:** 60 dias
- **Título máximo:** 200 caracteres (truncado com preservação)

## Arquivos

- **Discord Tool:** `src/core/discord/presentation/tools/inbox.py`
- **Claude Code Skill:** `.claude/skills/inbox/`
- **Specs:** `openspec/changes/inbox-specification/`

> "A persistência é o caminho do êxito" – made by Sky 🚀
