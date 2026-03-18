# PRD024: Kanban - Cards Vivos com Sincronização Trello

**Status:** 🟡 Em Andamento (80% completo)
**Data:** 2026-02-04
**Autor:** Sky
**Versão:** 2.1
**Depende de:** ADR024 (Workspace isolation)

---

## 1. Visão Geral

### 1.1 Problema

Atualmente o Skybridge não possui um Kanban board para visualizar e gerenciar o fluxo de trabalho dos agentes autônomos. A equipe precisa de uma forma visual de acompanhar issues, tarefas e progresso dos jobs.

### 1.2 Solução

Implementar **Kanban Board completo** com:
- Fonte única da verdade em `kanban.db` (SQLite)
- Sincronização bidirecional com Trello
- "Cards vivos" que mostram quando agentes estão processando
- Suporte a múltiplos workspaces (ADR024)
- Histórico completo de movimentos e eventos do card

### 1.3 Proposta de Valor

| Benefício | Descrição |
|-----------|-----------|
| Visualização clara | Acompanhar estado de cada issue/task |
| Cards vivos | Ver em tempo real quando agente está processando |
| Integração Trello | Sincronização automática bidirecional |
| Multi-workspace | Kanban isolado por workspace |
| Histórico de eventos | Rastrear movimentos, mudanças de status e processamento |

---

## 2. Requisitos

### 2.1 Requisitos Funcionais

| ID | Requisito | Prioridade | Status |
|----|-----------|------------|--------|
| RF-001 | Visualizar cards organizados em 6 colunas | Alta | ✅ |
| RF-002 | Criar cards manualmente | Média | 🔲 |
| RF-003 | Mover cards entre colunas via drag & drop | Alta | ✅ |
| RF-004 | Reordenar cards dentro da mesma coluna | Média | 🔲 |
| RF-005 | Editar dados de cards existentes | Alta | ✅ |
| RF-006 | Deletar cards | Alta | ✅ |
| RF-007 | Visualizar detalhes completos do card em modal | Alta | ✅ |
| RF-008 | Visualizar histórico completo de eventos do card | Alta | ✅ |
| RF-009 | Cards em processamento com destaque visual (borda pulsante) | Alta | ✅ |
| RF-010 | Cards em processamento no topo da coluna | Alta | ✅ |
| RF-011 | Barra de progresso durante processamento | Alta | ✅ |
| RF-012 | Sincronização automática com Trello (bidirecional) | Média | ✅ |
| RF-013 | Atualizações em tempo real via SSE | Alta | ✅ |
| RF-014 | Isolamento completo entre workspaces | Alta | ✅ |
| RF-015 | Filtrar cards por lista e status | Média | ✅ |

### 2.2 Requisitos Não-Funcionais

---

## 🚨🚨🚨 REGRAS CRÍTICAS - CARDS VIVOS 🚨🚨🚨

### ⚠️⚠️⚠️ NÃO DEVE EXISTIR LISTA PADRÃO!!! ⚠️⚠️⚠️

**PROIBIDO**: Ao criar/mover cards, **NUNCA** usar lista padrão/fallback.

```python
# ❌ PROIBIDO - VIOLAÇÃO CRÍTICA
if list_id is None:
    list_id = DEFAULT_LIST_ID  # PROIBIDO!!!
```

**CORRETO**: Erro claro exigindo lista explícita.

```python
# ✅ CORRETO
if list_id is None:
    return Result.err(
        "list_id OBRIGATÓRIO. "
        "NÃO existe lista padrão. "
        "Especifique: issues, backlog, todo, progress, review, publish"
    )
```

### ⚠️⚠️⚠️ NEM ERRO SILENCIOSO!!! ⚠️⚠️⚠️

**PROIBIDO**: Silenciar erro ao mover card para lista inexistente.

- Se lista não existe → **ERROR** (log + return)
- Se trello_list_id é None → **ERROR** (se requerido)
- Se status não mapeável → **ERROR**

```python
# ❌ PROIBIDO
try:
    move_card(card_id, list_id)
except ListNotFoundError:
    logger.info("Lista não encontrada, usando A Fazer")
    move_card(card_id, TODO_LIST)  # PROIBIDO!!!

# ✅ CORRETO
result = move_card(card_id, list_id)
if result.is_err:
    logger.error(f"[KANBAN] Falha ao mover: {result.error}")
    return Result.err(f"Lista não existe: {result.error}")
```

---

### 2.2 Requisitos Não-Funcionais

| ID | Requisito | Especificação |
|----|-----------|---------------|
| RNF-001 | Performance | Rendering < 2s, SSE latency < 100ms |
| RNF-002 | Disponibilidade | SSE com reconexão automática |
| RNF-003 | Usabilidade | Drag & drop fluido (60fps) |
| RNF-004 | Consistência | kanban.db como fonte única da verdade |
| RNF-005 | Segurança | Isolamento total entre workspaces |
| RNF-006 | Compatibilidade | React Bootstrap + @dnd-kit |
| RNF-007 | Testabilidade | Cobertura de testes > 80% |

### 2.3 Casos de Uso

#### UC-001: Visualizar Kanban Board
**Ator:** Usuário, Agente Autônomo
**Pré-condições:** Workspace ativo, kanban.db inicializado
**Fluxo Principal:**
1. Usuário acessa página `/kanban`
2. Sistema carrega 6 colunas configuradas
3. Sistema exibe cards ordenados (vivos primeiro)
4. Usuário visualiza estado atual de todas as tarefas

#### UC-002: Mover Card entre Colunas
**Ator:** Usuário
**Fluxo Principal:**
1. Usuário arrasta card da coluna A para coluna B
2. Sistema chama `PATCH /api/kanban/cards/{id}` com `list_id=B`
3. Backend atualiza kanban.db e card_history
4. SSE emite evento `card_updated`
5. Todos os clientes conectados atualizam UI

#### UC-003: Agente Processa Card (Card Vivo)
**Ator:** JobOrchestrator
**Fluxo Principal:**
1. JobOrchestrator inicia job
2. Emite `JobStartedEvent`
3. KanbanJobEventHandler atualiza card: `being_processed=True`, `position=0`
4. SSE emite evento `card_updated`
5. Frontend exibe card com borda pulsante + badge

### 2.4 Regras de Negócio

| ID | Regra | Descrição |
|----|-------|-----------|
| RN-001 | Ordenação de Cards | Cards vivos sempre primeiro, depois por `position` ASC |
| RN-002 | Position Zero | Card em processamento deve ter `position=0` |
| RN-003 | Conflito de Edição | Última escrita vence |
| RN-004 | Workspace Isolation | Cada workspace tem seu próprio kanban.db |
| RN-005 | Histórico Imutável | Entradas de card_history nunca são editadas |
| RN-006 | Auto-Histórico | CRUD em cards cria entradas de histórico automaticamente |

### 2.5 User Stories

| ID | Story | Prioridade |
|----|-------|------------|
| US-001 | Como usuário, quero visualizar cards em um quadro Kanban | Alta |
| US-002 | Como usuário, quero mover cards entre colunas | Alta |
| US-003 | Como agente, quero marcar cards como "em processamento" | Alta |
| US-004 | Como usuário, quero ver cards sendo processados em tempo real | Alta |
| US-005 | Como usuário, quero consultar o histórico de movimentos | Média |
| US-006 | Como usuário, quero criar cards manualmente | Média |
| US-007 | Como desenvolvedor, quero Kanban isolado por workspace | Alta |

---

## 3. Definition of Done (DoD)

### 3.1 DoD Geral (Aplicável a Todas as Tasks)

| Critério | Descrição |
|----------|-----------|
| **Código** | Implementado seguindo padrões do projeto (TDD estrito) |
| **Testes** | Testes unitários + integração escreitos ANTES da implementação |
| **Qualidade** | Código review aprovado, sem issues críticas |
| **Documentação** | PRD atualizado, comentários em código complexo |
| **Build** | `npm run build` funciona sem erros ou warnings |
| **CI/CD** | Pipeline passando (lint, testes, build) |

### 3.2 DoD por Tipo de Task

#### Backend Tasks
- [ ] Testes TDD escritos ANTES da implementação (Red → Green → Refactor)
- [ ] Testes de integração com banco de dados
- [ ] Testes de API via TestClient
- [ ] Schema SQL validado
- [ ] Error handling implementado
- [ ] Logs apropriados em pontos chave

#### Frontend Tasks
- [ ] Testes unitários com Vitest
- [ ] Componente testado com @testing-library/react
- [ ] TypeScript sem erros (`tsc --noEmit`)
- [ ] Acessibilidade (ARIA labels onde aplicável)
- [ ] Responsividade testada
- [ ] Loading states e error handling

#### API Endpoints
- [ ] OpenAPI/Swagger documentado
- [ ] Header `X-Workspace` respeitado
- [ ] Status codes corretos (200, 201, 204, 400, 404, 500)
- [ ] Validação de entrada (Pydantic)
- [ ] Tratamento de erros

#### Integração SSE
- [ ] Reconexão automática implementada
- [ ] Cleanup em `useEffect` return
- [ ] Error boundary para erros de conexão
- [ ] Testes de integração com EventBus

### 3.3 DoD Específico por Task

#### Task 8: Modal de Detalhes + Histórico ✅
- [x] CardModal.tsx criado com detalhes completos
- [x] Histórico exibido em timeline visual
- [x] API `getCardHistory()` implementada
- [x] 17 testes frontend passando
- [x] 7 testes backend de histórico passando
- [x] TypeScript sem erros
- [x] Build funcionando

#### Task 9: Modal de Criação de Card 🔲
- [ ] CreateCardModal.tsx criado
- [ ] Formulário com campos: título (obrigatório), descrição, lista, labels, due_date
- [ ] Validação de formulário
- [ ] POST /api/kanban/cards funcional
- [ ] Testes unitários do componente
- [ ] Testes de integração da API
- [ ] Feedback visual de sucesso/erro

#### Task 10: Reordenação de Cards 🔲
- [ ] Drag & drop vertical dentro da coluna (@dnd-kit sortable)
- [ ] PATCH /api/kanban/cards/{id} aceita `position`
- [ ] Backend persiste nova ordem no banco
- [ ] SSE emite card_updated após reordenação
- [ ] Testes de reordenação
- [ ] Performance O(1) para atualização de posição

---

## 4. Arquitetura

### 4.1 Colunas do Kanban

| Coluna | ID | Agent Type |
|--------|-----|------------|
| Issues | `issues` | - |
| Brainstorm | `brainstorm` | `analyze-issue` |
| A Fazer | `a-fazer` | - |
| Em Andamento | `em-andamento` | `resolve-issue` |
| Em Revisão | `em-revisao` | `review-issue` |
| Publicar | `publicar` | `publish-issue` |

### 4.2 Fonte Única da Verdade

```
┌─────────────┐
│ kanban.db   │ ← FONTE ÚNICA DA VERDADE
│ (SQLite)    │
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ Trello API  │   │   WebUI     │
│ (espelho)   │   │  (espelho)  │
└─────────────┘   └─────────────┘
```

### 4.3 Workspace Isolation (ADR024)

```
workspace/
├── core/data/kanban.db
├── trading/data/kanban.db
└── other-workspace/data/kanban.db
```

---

## 5. Cards Vivos

### 5.1 Modelo de Dados

```python
@dataclass
class KanbanCard:
    being_processed: bool = False
    processing_started_at: Optional[datetime] = None
    processing_job_id: Optional[str] = None
    processing_step: int = 0
    processing_total_steps: int = 0

    @property
    def processing_progress_percent(self) -> float:
        if self.processing_total_steps == 0:
            return 0.0
        return (self.processing_step / self.processing_total_steps) * 100
```

### 5.2 Ordenação SQL

```sql
ORDER BY being_processed DESC, position ASC, created_at DESC
```

---

## 6. Integração JobOrchestrator → Kanban

### 6.1 Domain Events

| Evento | Ação no Kanban |
|--------|----------------|
| `JobStartedEvent` | `being_processed=True`, `position=0` |
| `JobCompletedEvent` | `being_processed=False` |
| `JobFailedEvent` | `being_processed=False` |

### 6.2 Mapeamento Agent Type → Lista

```python
AGENT_TYPE_TO_LIST = {
    "analyze-issue": "brainstorm",
    "resolve-issue": "em-andamento",
    "review-issue": "em-revisao",
    "publish-issue": "publicar",
    "none": "issues",
}
```

---

## 7. Histórico de Cards

### 7.1 Eventos Rastreados

| Evento | Metadados |
|--------|------------|
| `created` | `title`, `to_list_id` |
| `moved` | `from_list_id`, `to_list_id` |
| `processing_started` | `processing_job_id`, `step`, `total_steps` |
| `processing_completed` | `step`, `total_steps` |
| `updated` | `updated_fields` |
| `deleted` | `title` |

### 7.2 Schema SQL

```sql
CREATE TABLE IF NOT EXISTS card_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL,
    event TEXT NOT NULL,
    from_list_id TEXT,
    to_list_id TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);
```

---

## 8. Backend API

### 8.1 Endpoints

```python
# Boards
GET    /api/kanban/boards
POST   /api/kanban/boards
GET    /api/kanban/boards/{id}

# Lists
GET    /api/kanban/lists
POST   /api/kanban/lists

# Cards
GET    /api/kanban/cards           # ?list_id=X&being_processed=Y
POST   /api/kanban/cards
GET    /api/kanban/cards/{id}
PATCH  /api/kanban/cards/{id}
DELETE /api/kanban/cards/{id}

# History
GET    /api/kanban/cards/{id}/history

# SSE
GET    /api/kanban/events

# Sync
POST   /api/kanban/sync/from-trello
```

---

## 9. Frontend Components

### 9.1 Estrutura

```
apps/web/src/components/Kanban/
├── KanbanBoard.tsx          # Quadro com colunas
├── KanbanColumn.tsx         # Coluna com cards
├── KanbanCard.tsx           # Card individual
├── CardModal.tsx            # Modal de detalhes + histórico
├── useKanbanSSE.ts          # Hook SSE
└── __tests__/
    ├── CardModal.test.tsx   # 17 testes ✅
    ├── KanbanBoard.test.tsx # 16 testes ✅
    └── workspace-isolation.test.tsx # 7 testes ✅
```

### 9.2 CSS - Cards Vivos

```css
.kanban-card-alive {
  animation: pulse-border 2s ease-in-out infinite;
  border: 2px solid #3b82f6;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}

@keyframes pulse-border {
  0%, 100% { border-color: #3b82f6; }
  50% { border-color: #60a5fa; box-shadow: 0 0 20px rgba(59, 130, 246, 0.8); }
}
```

---

## 10. Roadmap de Implementação

| ID | Task | Status |
|----|------|--------|
| 1 | Schema kanban.db + SQLite adapter | ✅ |
| 2 | TrelloSyncService bidirecional | ✅ |
| 3 | JobOrchestrator → Kanban (cards vivos) | ✅ |
| 4 | API endpoints Kanban (CRUD) | ✅ |
| 5 | Drag & drop frontend (@dnd-kit) | ✅ |
| 6 | Cards vivos visual (CSS + progress) | ✅ |
| 7 | SSE para atualizações em tempo real | ✅ |
| 8 | Modal de detalhes + Histórico | ✅ |
| 9 | Modal de criação de card | 🔲 |
| 10 | Reordenação de cards dentro da coluna | 🔲 |

---

## 11. Testes

### 11.1 Cobertura Atual

**Backend:** 70 testes ✅
- `test_sqlite_kanban_adapter.py` - 20 testes
- `test_trello_sync_service.py` - 10 testes
- `test_kanban_job_event_handler.py` - 5 testes
- `test_kanban_api.py` - 13 testes
- `test_kanban_sse.py` - 5 testes
- `test_kanban_sse_integration.py` - 3 testes
- `test_kanban_event_bus.py` - 7 testes
- Testes de histórico - 7 testes

**Frontend:** 148 testes ✅
- `CardModal.test.tsx` - 17 testes
- `KanbanBoard.test.tsx` - 16 testes
- `workspace-isolation.test.tsx` - 7 testes
- Demais testes do projeto - 108 testes

**TOTAL: 218 testes passando**

---

## 12. Próximos Passos

### 12.1 Task 9: Modal de Criação de Card

**Objetivo:** Permitir criação manual de cards

**DoD:**
- [ ] CreateCardModal.tsx criado
- [ ] Formulário validado
- [ ] POST /api/kanban/cards funcional
- [ ] Testes unitários e integração

### 12.2 Task 10: Reordenação de Cards

**Objetivo:** Permitir reordenar cards dentro da coluna

**DoD:**
- [ ] Drag & drop vertical funcional
- [ ] Position persistido no banco
- [ ] SSE emite eventos
- [ ] Testes de reordenação

---

## 13. Referências

- **ADR024:** Workspace isolation via X-Workspace header
- **PRD018:** Domain Events (JobStarted, JobCompleted, JobFailed)
- **SPEC009:** Orquestração Multi-Agente
- **@dnd-kit:** Biblioteca de drag & drop

---

> "Testes são a especificação que não mente" – made by Sky 🚀
