---
status: aprovada
data: 2026-01-24
aprovada_por: usuário
data_aprovacao: 2026-01-24
implementacao: feat/trello-webhook-reverso
---

# ADR022 — Fluxo Bidirecional GitHub ↔ Trello

**Status:** ✅ **APROVADA** - Em Implementação

**Data:** 2026-01-24
**Data de Aprovação:** 2026-01-24
**Branch de Implementação:** `feat/trello-webhook-reverso`

## Contexto

### Situação Atual

O Skybridge atualmente implementa **apenas o fluxo unidirecional GitHub → Trello**:

1. **GitHub webhook** é recebido quando uma issue é criada
2. **TrelloEventListener** cria um card no Trello (lista "Issues")
3. Quando o job termina, o card é atualizado com link do PR
4. **Trello → GitHub NÃO existe** - movimentações de cards não disparam ações

### Problema Identificado

O fluxo atual não permite controle granular do processo de desenvolvimento via Trello. O usuário não pode:

- Mover card para **Brainstorm** → Agente analisar e comentar
- Mover card para **A Fazer** → Agente começar a desenvolver
- Mover card para **Publicar** → Agente fazer PR

**Resultado:** Autonomia limitada a ~60%, pois o ciclo completo requer intervenção manual no GitHub.

## Decisão

**Implementar webhook server do Trello** para completar o fluxo bidirecional, permitindo que movimentações de cards disparem ações automáticas no GitHub.

### Fluxo Bidirecional Proposto

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUXO BIDIRECIONAL COMPLETO                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. GitHub webhook (issue criada) → Card na lista "Issues" ✅              │
│                                                                              │
│  2. Usuário move card para "💡 Brainstorm"                                  │
│     → Agente analisa e comenta no card                                      │
│                                                                              │
│  3. Usuário move card para "📋 A Fazer"                                      │
│     → Card vai para "🚧 Em Andamento" automaticamente                       │
│     → Agente desenvolve                                                     │
│                                                                              │
│  4. Agente termina → Card vai para "👁️ Em Revisão"                          │
│                                                                              │
│  5. Usuário move para "🚀 Publicar" → Agente faz PR                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mapeamento de Listas → Ações

| Lista Trello | Ação | autonomy_level |
|--------------|------|----------------|
| `Issues` (backlog) | Criação automática via GitHub webhook | - |
| `💡 Brainstorm` | Análise + comentário | `ANALYSIS` |
| `📋 A Fazer` | → `🚧 Em Andamento` + criar job | `DEVELOPMENT` |
| `🚧 Em Andamento` | Job em andamento | `DEVELOPMENT` |
| `👁️ Em Revisão` | Aguardando revisão humana | `REVIEW` |
| `🚀 Publicar` | Commit/push/PR | `PUBLISH` |

## Valor Incremental

| Métrica | Antes | Depois | Incremento |
|---------|-------|--------|------------|
| **Autonomia** | 60% | 80-90% | **+30% absoluto** |
| **Controle via Trello** | Parcial | Completo | **100%** |
| **Passos manuais** | 3-4 | 1-2 | **-50%** |

## DoD (Definition of Done)

- [x] ADR aprovada
- [ ] `TrelloWebhookServer` implementada
- [ ] `TrelloCardMovedListener` implementado
- [ ] `TrelloCardMovedToListEvent` criado
- [ ] `autonomy_level` em `JobOrchestrator`
- [ ] Regras por lista Trello implementadas
- [ ] WebSocket `/ws/console` para stream
- [ ] Testes E2E passando
- [ ] Documentação (QUICKSTART)

## Referências

- [PRD018 — Roadmap Autonomia](../prd/PRD018-roadmap-autonomia-incidente.md)
- [PRD020 — Implementação Fluxo Trello](../prd/PRD020-fluxo-bidirecional-trello.md)

---

> "O melhor processo é aquele que se adapta ao seu fluxo de trabalho, não o contrário" – made by Sky 🎯
