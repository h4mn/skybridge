# PRD023 - Fluxo Bidirecional GitHub ↔ Trello

**Data:** 2026-01-24
**Status:** 🔄 Em Planejamento
**Versão:** 1.0
**ADR Relacionada:** ADR022 (aprovada)
**Branch:** `feat/trello-webhook-reverso`
**Worktree:** `B:\_repositorios\skybridge-trello-reverso`
**Deadline:** 2026-01-31 (7 dias)

---

## 📊 Resumo Executivo

Este PRD detalha a implementação do **fluxo bidirecional completo** entre GitHub e Trello. O fluxo atual (GitHub → Trello) já está implementado. Esta implementação adicionará o fluxo reverso (Trello → GitHub), permitindo controle completo do desenvolvimento via movimentação de cards no Trello.

**Objetivo Principal:** Implementar webhook server do Trello para alcançar autonomia de 80-90%.

---

## 🎯 Objetivos

### 1.1 Objetivo Principal

Implementar **fluxo Trello → GitHub** para completar autonomia, permitindo que movimentações de cards disparem ações automáticas.

### 1.2 Objetivos Específicos

1. ✅ **TrelloWebhookServer** para receber eventos do Trello
2. ✅ **TrelloCardMovedListener** para processar movimentações
3. ✅ **TrelloCardMovedToListEvent** (novo domain event)
4. ✅ **autonomy_level** em JobOrchestrator (ANALYSIS, DEVELOPMENT, REVIEW, PUBLISH)
5. ✅ **Regras por lista Trello** (Brainstorm, A Fazer, Em Revisão, Publicar)
6. ✅ **WebSocket `/ws/console`** para stream em tempo real

---

## 🔧 Mapeamento Listas → Ações

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LISTAS TRELLO → AÇÕES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  "Issues" (backlog)                                                         │
│    └─ Criado automaticamente via GitHub webhook ✅ JÁ IMPLEMENTADO          │
│                                                                              │
│  "💡 Brainstorm"                                                            │
│    ├─ autonomy_level = ANALYSIS                                             │
│    ├─ Agente lê workspace/codebase                                         │
│    ├─ Analisa e comenta no card                                            │
│    └─ SEM code changes                                                      │
│                                                                              │
│  "📋 A Fazer"                                                               │
│    ├─ Card movido automaticamente para "🚧 Em Andamento"                   │
│    ├─ autonomy_level = DEVELOPMENT                                         │
│    └─ Job criado para agente desenvolver                                   │
│                                                                              │
│  "🚧 Em Andamento" → Agente trabalhando                                     │
│  "👁️ Em Revisão" → Aguardando revisão humana                               │
│  "🚀 Publicar" → Executa commit/push/PR                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📅 Cronograma (7 dias)

### Dia 1: Estrutura + ADR

- [x] ADR022 criada e aprovada
- [ ] Criar estrutura de diretórios

### Dia 2-3: TrelloWebhookServer

- [ ] Criar `src/infra/trello/trello_webhook_server.py`
- [ ] Implementar `POST /webhooks/trello`
- [ ] Verificar signature HMAC-SHA1
- [ ] Emitir `TrelloCardMovedToListEvent`

### Dia 4: TrelloCardMovedListener

- [ ] Criar listener para `TrelloCardMovedToListEvent`
- [ ] Implementar lógica por lista Trello

### Dia 5: Regras de Negócio + Stream Console

- [ ] Modificar `JobOrchestrator` com `autonomy_level`
- [ ] Implementar modo ANALYSIS
- [ ] WebSocket `/ws/console`

### Dia 6: Integração e Testes

- [ ] Registrar webhook do Trello
- [ ] Testar E2E cada lista

### Dia 7: Documentação + Release

- [ ] Criar QUICKSTART
- [ ] Release 0.9.0

---

## ✅ DoD (Definition of Done)

- [ ] Webhook Trello recebe eventos
- [ ] Cards movem automaticamente
- [ ] Agente analisa em Brainstorm
- [ ] Agente desenvolve em Em Andamento
- [ ] Agente faz PR em Publicar
- [ ] WebSocket stream funciona

---

## 📊 Métricas de Sucesso

| Métrica | Antes | Depois | Alvo |
|---------|-------|--------|------|
| **Autonomia** | 60% | 80-90% | **+30%** |
| **Controle via Trello** | Parcial | Completo | **100%** |

---

> "Kanban não é apenas visual, é uma linguagem de trabalho universal" – made by Sky 📋
