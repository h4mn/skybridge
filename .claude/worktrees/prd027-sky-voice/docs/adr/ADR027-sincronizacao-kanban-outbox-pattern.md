---
status: proposta
data: 2026-02-14
aprovada_por: usuário
data_aprovacao: pendente
implementacao: feat/kanban-outbox-sync
---

# ADR027 — Sincronização Kanban: Outbox Pattern + py-trello

**Status:** 📝 **PROPOSTA** — Substitui ADR020 padrão antigo

**Data:** 2026-02-14
**Data de Aprovação:** Pendente
**Branch de Implementação:** `feat/kanban-outbox-sync`

## Contexto

### Situação Atual

**ADR020** (2025-01-17) define integração GitHub → Trello (unidirecional):
- Assume IDs de listas como constantes (ENV VARS)
- Chamadas síncronas à API Trello
- Sem garantia de consistência

**Problemas identificados:**
1. **IDs mudam em testes** — `id` (SQLite) e `trello_list_id` (Trello) podem mudar
2. **Sem transacionalidade** — Falha no meio não é retonável
3. **Sem re-tentativas** — Erros são finais
4. **Hardcoded strings** — 120+ ocorrências de "Em Andamento"

### Proposta de Mudança

**Profissionais usam Outbox Pattern** para sincronização entre sistemas:
- Tabela `sync_outbox` ao lado de mudanças
- Processador assíncrono lê eventos e sincroniza
- IDs mapeados dinamicamente no banco
- Re-tentativas automáticas com status tracking

## Decisão

**Implementar Outbox Pattern + py-trello** para sincronização Kanban.

### Abordagem Profissional

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ OUTBOX PATTERN - Sincronização Kanban Skybridge                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Transação no Banco Local                                           │
│     ┌────────────────────────────────────────────────────────────────┐        │
│     │ BEGIN TRANSACTION                                                │        │
│     │   INSERT INTO lists (id, name, trello_list_id)                │        │
│     │   INSERT INTO sync_outbox (event_type, local_id, slug, ...)   │        │
│     │ COMMIT                                                           │        │
│     └────────────────────────────────────────────────────────────────┘        │
│                                                                              │
│  2. Processador Assíncrono (background)                                   │
│     ┌────────────────────────────────────────────────────────────────┐        │
│     │ SELECT * FROM sync_outbox WHERE status = 'pending'            │        │
│     │ Para cada evento:                                              │        │
│     │   - POST /cards/123 (py-trello)                                │        │
│     │   - UPDATE sync_outbox SET status = 'synced'                     │        │
│     │   - Se falhar: status = 'failed', retries++                    │        │
│     └────────────────────────────────────────────────────────────────┘        │
│                                                                              │
│  3. Identificador Único: SLUG (constante de negócio)                   │
│     - Slug NUNCA muda: "progress", "todo", "review"                 │
│     - IDs SEMPRE do banco (nunca hardcoded)                              │
│     - ENV VAR: SKYBRIDGE_KANBAN_SLUG_LIST=issues,backlog,todo,progress,review,publish │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tabelas de Sincronização

#### sync_outbox
```sql
CREATE TABLE sync_outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,         -- "list_created", "card_moved", "card_updated"
    entity_type TEXT NOT NULL,         -- "list", "card"
    local_id TEXT NOT NULL,
    external_id TEXT,                   -- Trello ID após sincronização
    slug TEXT,                        -- Slug de negócio (constante)
    payload JSON,                      -- Dados para API Trello
    status TEXT DEFAULT 'pending',       -- "pending", "synced", "failed"
    retries INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);
```

#### list_id_mapping
```sql
CREATE TABLE list_id_mapping (
    slug TEXT PRIMARY KEY,              -- "progress", "todo", etc.
    local_id TEXT NOT NULL,              -- SQLite ID (dinâmico)
    trello_list_id TEXT,                 -- Trello ID (dinâmico)
    last_sync_at TIMESTAMP,
    sync_status TEXT,                    -- "pending", "synced", "error"
    error_message TEXT
);
```

## Single Source of Truth

| Onde? | O que? | Estável? |
|---------|---------|-----------|
| **ENV VAR** | `SKYBRIDGE_KANBAN_SLUG_LIST` | ✅ Sim (constante de negócio) |
| **kanban.db** | `lists.id`, `lists.trello_list_id` | ❌ Não (IDs mudam) |
| **Domain** | `KanbanListsConfig` | ✅ Sim (definições) |

## Valor Incremental

| Métrica | Antes | Depois | Incremento |
|---------|-------|--------|------------|
| **Consistência** | Sem garantia | Transacional | **∞** |
| **IDs mudam?** | Quebra sistema | Outbox retona | **∞** |
| **Re-tentativas** | Manual | Automático | **∞** |
| **Hardcoded** | 120+ strings | Slug-based | **∞** |
| **Profissionalismo** | Amador | Best Practice | **∞** |

## DoD (Definition of Done)

- [ ] ADR aprovada
- [ ] Tabelas `sync_outbox` e `list_id_mapping` criadas
- [ ] `OutboxProcessor` implementado
- [ ] py-trello integrado
- [ ] `get_list_by_slug()` no adapter
- [ ] ENV VAR única implementada
- [ ] Todos os 120+ "Em Andamento" refatorados
- [ ] Testes E2E passando
- [ ] Documentação (QUICKSTART)

## Referências

- Substitui: [ADR020 — Integração Trello](../adr/ADR020-integracao-trello.md)
- Complementa: [ADR022 — Fluxo Bidirecional](../adr/ADR022-fluxo-bidirecional-github-trello.md)
- [Outbox Pattern — Decodable](https://www.decodable.co/blog/revisiting-the-outbox-pattern)
- [py-trello — GitHub](https://github.com/sarumont/py-trello)

---

> "Consistência não é opcional, é fundamento" – made by Sky 🏗️
