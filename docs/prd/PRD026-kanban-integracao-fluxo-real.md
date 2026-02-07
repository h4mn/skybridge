# PRD026: Integração Kanban com Fluxo Real da Skybridge

**Status:** 🚧 Nova Proposta
**Data:** 2026-02-04
**Autor:** Sky
**Versão:** 1.0
**Tipo:** Crítico - Correção de Arquitetura
**Depende de:** PRD013, PRD016, PRD019, PRD024
**Bloqueia:** Visualização real do trabalho da Skybridge

---

## 1. Resumo Executivo

### 1.1 Problema Identificado

O **Kanban (PRD024)** foi implementado como uma **estrutura isolada**, sem integração com o fluxo real da Skybridge. O kanban.db existe, os componentes frontend existem, mas **nada reflete o que a Skybridge está realmente fazendo**.

**Sintoma principal:**
- Webhook chega → Job é criado → Agent trabalha → PR é criada
- **Kanban mostra:** vazio, estático, desconectado da realidade

### 1.2 Causa Raiz

O `KanbanJobEventHandler` existe mas **NÃO está registrado no EventBus**. Quando Domain Events são emitidos (`JobStartedEvent`, `JobCompletedEvent`, `JobFailedEvent`), o Kanban não os recebe.

```
JobOrchestrator → emit(JobStartedEvent) → EventBus → [NINGUÉM OUVINDO!]
                                                    ↓
                                              kanban.db SILENCIOSO
```

### 1.3 Proposta de Solução

**Integrar o Kanban ao fluxo real da Skybridge** através de 6 fases críticas:

| Fase | Descrição | Esforço | Prioridade |
|------|-----------|---------|------------|
| **F1** | Conectar KanbanJobEventHandler ao EventBus | 8h | 🔴 Crítica |
| **F2** | Auto-inicializar kanban.db no startup | 4h | 🔴 Crítica |
| **F3** | Criar cards quando webhook chega | 6h | 🔴 Crítica |
| **F4** | Marcar cards como "vivos" durante processamento | 6h | 🔴 Crítica |
| **F5** | Mover cards quando job completa/falha | 8h | 🟡 Importante |
| **F6** | Sincronização Trello ↔ kanban.db | 16h | 🟡 Importante |

**Esforço Total:** 48 horas (6 dias)

---

## 2. Contexto e Justificativa

### 2.1 Por que isso é crítico?

A PRD024 definiu o Kanban como "fonte única da verdade" para visualizar o trabalho da Skybridge. Mas a implementação atual **não está conectada à fonte dos eventos**.

**Consequências:**
1. **Visibilidade zero:** Stakeholders não conseguem ver o que a Skybridge está fazendo
2. **Falta de confiança:** Sem dados reais, o Kanban parece um "demo fake"
3. **Decisões baseadas em dados incorretos:** O quadro não reflete a realidade
4. **Work duplicado:** Time olha Trello/GitHub em vez do Kanban da Skybridge

### 2.2 Motivação do Usuário

> *"precisamos alterar os requisitos e DoD, porque pra mim não é terminado se eu não visualizar no kanban a verdade (prd013, prd016, prd019, prd020 e prd023), qual foi a motivação de criar o kanban? não estou vendo a skybridge em funcionamento, não importa se decidi que os dados deveriam ir para um .db que ficou morto sem alimentação do que a skybridge está fazendo"*

---

## 3. Arquitetura Proposta

### 3.1 Fluxo Atual (Quebrado)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO ATUAL - KANBAN ISOLADO                             │
│                                                                              │
│  GitHub Webhook                                                              │
│       ↓                                                                      │
│  WebhookProcessor → JobQueue                                                │
│       ↓                                                                      │
│  JobOrchestrator → emit(JobStartedEvent) → EventBus                          │
│       ↓                                          ↓                           │
│  Agent trabalha...                   [TrelloEventListener] → Trello API       │
│       ↓                                          ↓                           │
│  emit(JobCompletedEvent) → EventBus        (CRIA card no Trello)           │
│       ↓                                                                      │
│  Git commit + PR                                                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  kanban.db (SILENCIOSO - NADA ACONTECE)                                │ │
│  │  - Cards não são criados                                                │ │
│  │  - Cards não são marcados como "vivos"                                  │ │
│  │  - Cards não são movidos                                                │ │
│  │  - Histórico não é populado                                             │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Fluxo Proposto (Integrado)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO PROPOSTO - KANBAN INTEGRADO                         │
│                                                                              │
│  GitHub Webhook                                                              │
│       ↓                                                                      │
│  WebhookProcessor                                                            │
│       ↓                                                                      │
│  emit(IssueReceivedEvent) ─────────────────────────────────┐               │
│       ↓                                                    │               │
│  JobQueue.enqueue()                                      │               │
│       ↓                                                    ↓               │
│  ┌─────────────────────────────────────────────────────────┴───────┐      │
│  │                    EventBus (Central)                       │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│       │                              │                             │           │
│       ↓                              ↓                             ↓           │
│  [TrelloEventListener]    [KanbanJobEventHandler]      [Outros...]        │
│       │                              │                             │           │
│       ↓                              ↓                             ↓           │
│  Trello API               kanban.db (FONTES DA VERDADE)                      │
│                                      │                             │           │
│                                      ↓                             ↓           │
│                               ┌─────────────────────────────┴───────────┐      │
│                               │        WebUI Kanban (SSE)              │      │
│                               │  - Cards criados automaticamente      │      │
│                               │  - Cards vivos pulsam azul           │      │
│                               │  - Histórico em tempo real           │      │
│                               └──────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Domain Events → Kanban Actions

| Domain Event | Emitido Por | Ação no Kanban | Handler |
|--------------|------------|----------------|---------|
| `IssueReceivedEvent` | `WebhookProcessor` | Criar card na lista "Issues" | `handle_issue_received()` |
| `JobStartedEvent` | `JobOrchestrator` | Marcar card como "vivo" + mover para lista correta | `handle_job_started()` |
| `JobCompletedEvent` | `JobOrchestrator` | Mover para "Em Revisão" + desmarcar "vivo" | `handle_job_completed()` |
| `JobFailedEvent` | `JobOrchestrator` | Mover para "Issues" + desmarcar "vivo" + label erro | `handle_job_failed()` |
| `PRCreatedEvent` | `GitService` | Guardar `pr_url` no card | `handle_pr_created()` |

---

## 4. Requisitos Funcionais

### 4.1 Fase 1: Conectar KanbanJobEventHandler ao EventBus

**Prioridade:** 🔴 Crítica
**Esforço:** 8 horas

#### RF-001: KanbanJobEventHandler deve ser registrado no EventBus
- **Descrição:** Durante o startup da aplicação, o `KanbanJobEventHandler` deve se inscrever nos eventos de domínio
- **Arquivo:** `runtime/bootstrap/app.py`
- **Entrada:** EventBus global
- **Saída:** Handler registrado e ouvindo eventos
- **Critérios de Aceite:**
  - [ ] `KanbanJobEventHandler.start()` é chamado no lifespan
  - [ ] `event_bus.subscribe(JobStartedEvent, handler.handle_job_started)`
  - [ ] `event_bus.subscribe(JobCompletedEvent, handler.handle_job_completed)`
  - [ ] `event_bus.subscribe(JobFailedEvent, handler.handle_job_failed)`
  - [ ] Log confirma registro: "KanbanJobEventHandler iniciado"

#### RF-002: KanbanJobEventHandler.handle_job_started() deve atualizar kanban.db
- **Descrição:** Quando `JobStartedEvent` é recebido, o handler deve criar/atualizar card como "vivo"
- **Arquivo:** `core/kanban/application/kanban_job_event_handler.py`
- **Critérios de Aceite:**
  - [ ] Busca card existente por `issue_number`
  - [ ] Se card existe: atualiza `being_processed=True`, `position=0`, `processing_job_id`
  - [ ] Se card não existe: cria novo card com `being_processed=True`
  - [ ] Card é movido para lista correta (baseada em `agent_type`)
  - [ ] SSE emite evento `card_updated`

#### RF-003: Suporte a múltiplos workspaces
- **Descrição:** Cada workspace deve ter seu próprio `KanbanJobEventHandler`
- **Arquivo:** `runtime/bootstrap/app.py`
- **Critérios de Aceite:**
  - [ ] Para cada workspace ativo, criar instância de `KanbanJobEventHandler`
  - [ ] Usar `kanban.db` específico do workspace (`workspace/{id}/data/kanban.db`)
  - [ ] Events são isolados por workspace

---

### 4.2 Fase 2: Auto-inicializar kanban.db

**Prioridade:** 🔴 Crítica
**Esforço:** 4 horas

#### RF-004: KanbanInitializer deve ser executado no startup
- **Descrição:** kanban.db deve ser criado automaticamente se não existir
- **Arquivo:** `runtime/bootstrap/app.py`
- **Critérios de Aceite:**
  - [ ] Durante criação do workspace core, verificar se `kanban.db` existe
  - [ ] Se não existe, executar `KanbanInitializer.initialize()`
  - [ ] 6 listas padrão são criadas (Issues, Brainstorm, A Fazer, Em Andamento, Em Revisão, Publicar)
  - [ ] Log confirma inicialização: "kanban.db auto-inicializado"

#### RF-005: board-1 deve ser criado automaticamente
- **Descrição:** Board padrão deve existir antes de qualquer operação
- **Arquivo:** `core/kanban/application/kanban_initializer.py`
- **Critérios de Aceite:**
  - [ ] Board "board-1" é criado com nome "Skybridge"
  - [ ] 6 listas são criadas e associadas ao board
  - [ ] Posições das listas são definidas (0-5)

---

### 4.3 Fase 3: Criar Cards quando Webhook Chega

**Prioridade:** 🔴 Crítica
**Esforço:** 6 horas

#### RF-006: IssueReceivedEvent deve criar card no Kanban
- **Descrição:** Quando webhook do GitHub chega, card deve ser criado na lista "Issues"
- **Arquivo:** `core/kanban/application/kanban_job_event_handler.py`
- **Critérios de Aceite:**
  - [ ] Handler se inscreve em `IssueReceivedEvent`
  - [ ] Card é criado com `title`, `issue_number`, `issue_url`
  - [ ] Card é criado na lista "Issues"
  - [ ] `labels` são sincronizados com labels da issue
  - [ ] SSE emite evento `card_created`
  - [ ] WebUI mostra novo card instantaneamente

#### RF-007: Metadados da issue devem ser preservados
- **Descrição:** Card deve guardar referência completa à issue do GitHub
- **Critérios de Aceite:**
  - [ ] `issue_number` é salvo no card
  - [ ] `issue_url` é salvo no card
  - [ ] `author` (quem abriu) é salvo nos metadados
  - [ ] `repository` (owner/repo) é salvo nos metadados

---

### 4.4 Fase 4: Marcar Cards como "Vivos"

**Prioridade:** 🔴 Crítica
**Esforço:** 6 horas

#### RF-008: JobStartedEvent deve marcar card como "vivo"
- **Descrição:** Quando job inicia, card deve ser marcado como `being_processed=True`
- **Critérios de Aceite:**
  - [ ] `being_processed` é setado para `True`
  - [ ] `processing_started_at` é setado para `timestamp` do evento
  - [ ] `processing_job_id` é salvo (rastreabilidade)
  - [ ] `position=0` (card vai para o topo da coluna)
  - [ ] Card é movido para lista baseada em `agent_type`:
    - `analyze-issue` → "Brainstorm"
    - `resolve-issue` → "Em Andamento"
    - `review-issue` → "Em Revisão"
    - `publish-issue` → "Publicar"

#### RF-009: Cards vivos devem ter destaque visual
- **Descrição:** Frontend deve exibir card "vivo" com efeitos visuais
- **Arquivo:** `apps/web/src/components/Kanban/KanbanCard.tsx`
- **Critérios de Aceite:**
  - [ ] Borda pulsante azul (`@keyframes pulse-border`)
  - [ ] Badge "🤖 Agent working..." visível
  - [ ] Progress bar mostrando `processing_step / processing_total_steps`
  - [ ] Card aparece sempre no topo da coluna

---

### 4.5 Fase 5: Mover Cards quando Job Completa/Falha

**Prioridade:** 🟡 Importante
**Esforço:** 8 horas

#### RF-010: JobCompletedEvent deve mover card para "Em Revisão"
- **Descrição:** Quando job completa com sucesso, card deve ser movido
- **Critérios de Aceite:**
  - [ ] Card é movido para lista "Em Revisão"
  - [ ] `being_processed` é setado para `False`
  - [ ] `processing_job_id` é limpo
  - [ ] Histórico registra evento `processing_completed`
  - [ ] SSE emite evento `card_updated`

#### RF-011: PRCreatedEvent deve guardar pr_url no card
- **Descrição:** Quando PR é criada, card deve guardar link
- **Critérios de Aceite:**
  - [ ] Handler se inscreve em `PRCreatedEvent`
  - [ ] `pr_url` é atualizado no card
  - [ ] `pr_number` é salvo no card
  - [ ] Card mostra link "🔗 Pull Request" no modal

#### RF-012: JobFailedEvent deve marcar erro no card
- **Descrição:** Quando job falha, card deve refletir o erro
- **Critérios de Aceite:**
  - [ ] Card é movido para lista "Issues" (ou "Erros" se existir)
  - [ ] `being_processed` é setado para `False`
  - [ ] Label "❌ Erro" é adicionado
  - [ ] Histórico registra evento `processing_failed` com `error_message`
  - [ ] SSE emite evento `card_updated`

---

### 4.6 Fase 6: Sincronização Trello ↔ kanban.db

**Prioridade:** 🟡 Importante
**Esforço:** 16 horas

#### RF-013: Sincronização bidirecional Trello → kanban.db
- **Descrição:** Mudanças no Trello devem refletir no kanban.db
- **Arquivo:** `core/kanban/application/trello_sync_service.py`
- **Critérios de Aceite:**
  - [ ] `sync_from_trello()` é implementado
  - [ ] Polling periódico (5 minutos) OU webhook do Trello
  - [ ] Cards movidos no Trello são movidos no kanban.db
  - [ ] Cards renomeados no Trello são atualizados no kanban.db
  - [ ] Conflicts são resolvidos (última escrita vence)

#### RF-014: Fila de sincronização assíncrona
- **Descrição:** Sincronização não deve bloquear operações CRUD
- **Critérios de Aceite:**
  - [ ] `asyncio.Queue` para operações de sync
  - [ ] Background worker processa fila
  - [ ] Retry logic para falhas (3 tentativas)
  - [ ] Dead letter queue para operações que falham após retries

#### RF-015: Endpoint manual de sync
- **Descrição:** Usuário pode disparar sync manualmente
- **Endpoint:** `POST /api/kanban/sync/from-trello`
- **Critérios de Aceite:**
  - [ ] Request body contém `board_id`
  - [ ] Sync é executado imediatamente
  - [ ] Response retorna contagem de cards sincronizados
  - [ ] SSE emite eventos para cada card atualizado

---

## 5. Requisitos Não-Funcionais

### 5.1 Performance

| RNF | Especificação | Target |
|-----|---------------|--------|
| **RNF-001** | Latência de atualização Kanban | < 100ms (EventBus → SSE) |
| **RNF-002** | Tempo de criação de card | < 50ms (kanban.db insert) |
| **RNF-003** | Query de cards (com filtros) | < 20ms (indexado por issue_number) |
| **RNF-004** | Sincronização Trello | Não bloqueia CRUD (fila assíncrona) |

### 5.2 Disponibilidade

| RNF | Especificação |
|-----|---------------|
| **RNF-005** | KanbanJobEventHandler sempre registrado no startup |
| **RNF-006** | kanban.db auto-inicializado se não existe |
| **RNF-007** | SSE com reconexão automática |

### 5.3 Consistência

| RNF | Especificação |
|-----|---------------|
| **RNF-008** | kanban.db como fonte única da verdade (PRD024) |
| **RNF-009** | Histórico imutável (entradas nunca são editadas) |
| **RNF-010** | Resolução de conflitos: última escrita vence (Trello vs Kanban) |

### 5.4 Observabilidade

| RNF | Especificação |
|-----|---------------|
| **RNF-011** | Logs em todos os pontos críticos (registro, eventos, erros) |
| **RNF-012** | Métricas de contadores (cards criados, movidos, erros) |
| **RNF-013** | Tracing distribuído (correlation_id do webhook ao card) |

---

## 6. Casos de Uso

### UC-001: Webhook Chega → Card Criado

**Ator:** GitHub Webhook
**Pré-condições:** kanban.db inicializado, KanbanJobEventHandler registrado
**Fluxo Principal:**

1. GitHub envia webhook `issues.opened`
2. `WebhookProcessor` processa webhook
3. `WebhookProcessor.emit(IssueReceivedEvent)`
4. EventBus entrega evento para `KanbanJobEventHandler`
5. `KanbanJobEventHandler.handle_issue_received()` é chamado
6. Card é criado na lista "Issues" com dados da issue
7. SSE emite `card_created` para WebUI
8. Usuário vê card aparecer instantaneamente

**Pós-condições:** Card visível no Kanban, histórico com evento `created`

**Fluxo Alternativo:**
- **5a:** Card já existe para essa issue → Atualiza dados existentes

---

### UC-002: Job Inicia → Card Vivo

**Ator:** JobOrchestrator
**Pré-condições:** Card existe, KanbanJobEventHandler registrado
**Fluxo Principal:**

1. `JobOrchestrator.execute_job()` é chamado
2. `JobOrchestrator.emit(JobStartedEvent)`
3. EventBus entrega evento para `KanbanJobEventHandler`
4. `KanbanJobEventHandler.handle_job_started()` é chamado
5. Card é marcado como `being_processed=True`
6. Card é movido para lista baseada em `agent_type` (ex: "Em Andamento")
7. `position=0` (card vai para o topo)
8. SSE emite `card_updated` para WebUI
9. Usuário vê card piscar azul com badge "🤖 Agent working..."

**Pós-condições:** Card "vivo" no topo da coluna, histórico com evento `processing_started`

---

### UC-003: Job Completa → Card em Revisão

**Ator:** JobOrchestrator
**Pré-condições:** Card marcado como "vivo"
**Fluxo Principal:**

1. `JobOrchestrator` completa job com sucesso
2. `JobOrchestrator.emit(JobCompletedEvent)`
3. EventBus entrega evento para `KanbanJobEventHandler`
4. `KanbanJobEventHandler.handle_job_completed()` é chamado
5. Card é movido para lista "Em Revisão"
6. `being_processed=False` (card para de piscar)
7. Histórico registra evento `processing_completed`
8. SSE emite `card_updated` para WebUI
9. Usuário vê card na coluna "Em Revisão", sem badge "vivo"

**Pós-condições:** Card em "Em Revisão", não está mais "vivo", histórico completo

---

### UC-004: PR Criada → Card com Link

**Ator:** GitService
**Pré-condições:** Card em "Em Revisão"
**Fluxo Principal:**

1. `GitService` cria PR com sucesso
2. `GitService.emit(PRCreatedEvent)`
3. EventBus entrega evento para `KanbanJobEventHandler`
4. `KanbanJobEventHandler.handle_pr_created()` é chamado
5. `pr_url` é atualizado no card
6. Modal do card mostra link "🔗 Pull Request"
7. Histórico registra evento `pr_created`
8. SSE emite `card_updated` para WebUI

**Pós-condições:** Card com link para PR, usuário pode clicar e abrir

---

## 7. Roadmap de Implementação

### 7.1 Cronograma (6 dias úteis)

| Dia | Fase | Task | Entrega |
|-----|------|------|--------|
| **1** | Fase 1 | Conectar KanbanJobEventHandler ao EventBus | Handler registrado, ouvindo eventos |
| **2** | Fase 2 | Auto-inicializar kanban.db | kanban.db criado no startup |
| **3** | Fase 3 | Criar cards quando webhook chega | Cards aparecem ao receber issue |
| **4** | Fase 4 | Marcar cards como "vivos" | Cards piscam azul durante processamento |
| **5** | Fase 5 | Mover cards quando job completa/falha | Cards movem para "Em Revisão" |
| **6** | Fase 6 | Sincronização Trello ↔ kanban.db | Sync bidirecional funcionando |

### 7.2 Dependências

| Task | Depende de | Bloqueia |
|------|-----------|---------|
| Fase 1 | PRD016 (EventBus implementado) | Todas as outras |
| Fase 2 | PRD024 (KanbanInitializer implementado) | Fase 3 |
| Fase 3 | Fase 1 | Fase 4 |
| Fase 4 | Fase 1, Fase 3 | Fase 5 |
| Fase 5 | Fase 4 | - |
| Fase 6 | PRD020 (TrelloSyncService) | - |

---

## 8. DoD (Definition of Done)

### 8.1 DoD Geral

- [ ] Código implementado seguindo padrões do projeto (TDD estrito)
- [ ] Testes escritos ANTES da implementação (Red → Green → Refactor)
- [ ] Código review aprovado, sem issues críticas
- [ ] PRD024 atualizado com status correto das tasks
- [ ] CHANGELOG.md atualizado com mudanças
- [ ] Build funcionando sem erros ou warnings

### 8.2 DoD por Fase

#### Fase 1: Conectar Handler
- [ ] `KanbanJobEventHandler.start()` implementado
- [ ] Handler registrado em `runtime/bootstrap/app.py`
- [ ] Teste e2e: emitir `JobStartedEvent` → card atualizado
- [ ] Log confirma registro no startup

#### Fase 2: Auto-inicializar
- [ ] `KanbanInitializer` chamado no lifespan
- [ ] kanban.db criado se não existe
- [ ] 6 listas padrão criadas
- [ ] Teste: workspace novo → kanban.db presente

#### Fase 3: Criar Cards
- [ ] `handle_issue_received()` implementado
- [ ] Card criado com dados da issue
- [ ] Teste: webhook → card visível no Kanban
- [ ] SSE emite `card_created`

#### Fase 4: Cards Vivos
- [ ] `handle_job_started()` atualiza `being_processed`
- [ ] Card movido para lista correta
- [ ] Frontend exibe card piscando azul
- [ ] Teste: job inicia → card "vivo" visível

#### Fase 5: Mover Cards
- [ ] `handle_job_completed()` move para "Em Revisão"
- [ ] `handle_job_failed()` marca erro
- [ ] `handle_pr_created()` guarda `pr_url`
- [ ] Teste: job completo → card em "Em Revisão"

#### Fase 6: Sincronização
- [ ] `sync_from_trello()` implementado
- [ ] Fila assíncrona funcionando
- [ ] Endpoint `/sync/from-trello` funcionando
- [ ] Teste: mudança no Trello → refletida no Kanban

---

## 9. Arquivos a Criar/Modificar

### 9.1 Arquivos a Modificar

| Arquivo | Linhas | Modificação |
|---------|--------|-------------|
| `runtime/bootstrap/app.py` | ~140 | Inicializar `KanbanJobEventHandler` |
| `runtime/bootstrap/app.py` | ~75 | Auto-inicializar kanban.db |
| `core/kanban/application/kanban_job_event_handler.py` | 211-217 | Implementar `register_listeners()` |
| `core/kanban/application/kanban_job_event_handler.py` | NOVO | Adicionar `handle_issue_received()` |
| `core/kanban/application/kanban_job_event_handler.py` | NOVO | Adicionar `handle_pr_created()` |
| `apps/web/src/components/Kanban/KanbanBoard.tsx` | 140 | Usar workspace do contexto |
| `apps/web/src/pages/Kanban.tsx` | 42-55 | Adicionar botão "Novo Card" |
| `docs/prd/PRD024-kanban-cards-vivos.md` | - | Atualizar status das tasks |

### 9.2 Arquivos a Criar

1. **`apps/web/src/components/Kanban/CreateCardModal.tsx`**
   - Formulário para criar cards manualmente
   - Validação de campos
   - Conexão com POST /api/kanban/cards

2. **`apps/web/src/contexts/WorkspaceContext.tsx`**
   - Contexto global para workspace ativo
   - Provider em `App.tsx`

3. **`tests/integration/kanban/test_kanban_integration.py`**
   - Teste e2e: webhook → card criado
   - Teste e2e: job inicia → card "vivo"
   - Teste e2e: job completo → card movido

---

## 10. Métricas de Sucesso

### 10.1 Métricas Técnicas

| Métrica | Baseline | Alvo | Como Medir |
|---------|----------|------|------------|
| **Latência webhook → card** | N/A | < 200ms | Teste e2e |
| **Latência job → card vivo** | N/A | < 100ms | Teste e2e |
| **Cards criados automaticamente** | 0% | 100% | Contador de cards |
| **Cards movidos automaticamente** | 0% | 100% | Histórico de cards |
| **Taxa de erro de sync** | N/A | < 1% | Logs de erro |

### 10.2 Métricas de Negócio

| Métrica | Baseline | Alvo | Impacto |
|---------|----------|------|---------|
| **Visibilidade do trabalho** | 0% | 100% | Stakeholders veem o que a Skybridge faz |
| **Confiança no Kanban** | Baixa | Alta | Kanban reflete realidade |
| **Tempo para detectar problemas** | Horas | Minutos | Cards "vivos" mostram problemas em tempo real |
| **Redução de work duplicado** | 0% | 80% | Time olha Kanban em vez de Trello/GitHub |

---

## 11. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| EventBus não ter `subscribe()` | Baixa | Alto | ✅ Já verificado: método existe |
| kanban.db não ser inicializado | Média | Alto | Auto-inicialização no startup |
| Cards "vivos" não sincronizarem | Média | Médio | Testes e2e + logs detalhados |
| Performance degradar com SSE | Baixa | Médio | Limitar taxa de emissão de eventos |
| Conflito Trello vs Kanban | Média | Baixo | Última escrita vence, log de conflitos |

---

## 12. Relação com Outros PRDs

| PRD | Relação | Descrição |
|-----|---------|-----------|
| **PRD013** | Evolui | Agentes (PRD013) emitem eventos que Kanban consome |
| **PRD016** | Base | Domain Events (PRD016) são usados para integração |
| **PRD019** | Complementa | Agent SDK (PRD019) emite eventos de progresso |
| **PRD020** | Paralelo | Trello Sync (PRD020) funciona em paralelo |
| **PRD023** | Contexto | Workspaces (PRD023) determinam qual kanban.db usar |
| **PRD024** | Corrige | Este PRD corrige as pendências críticas do PRD024 |

---

## 13. Aprovação

| Papel | Nome | Data | Assinatura |
|-------|------|------|------------|
| Autor | Sky | 2026-02-04 | ✍️ |
| Tech Lead | ___________ | ___________ | ______ |
| Produto | ___________ | ___________ | ______ |

---

> "A verdade do Kanban é a verdade da Skybridge" – made by Sky 🚀

---

**Histórico de Revisões:**

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-02-04 | Sky | Criação inicial - Documenta pendências críticas do PRD024 |
