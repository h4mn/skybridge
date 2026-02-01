# PRD025: WebUI - Workspaces Globais com Isolamento Completo

**Status:** 🚧 Em Elaboração
**Data:** 2026-02-01
**Autor:** Sky
**Versão:** 1.0
**Depende de:** PL003 (Isolamento Profissional de Testes)

---

## Status de Implementação

### Fase 0: Definição - 🚧 EM PROGRESSO

**BLOQUEADO por PL003:** Aguardando implementação do isolamento profissional de testes antes de prosseguir.

- [x] Análise de componentes existentes
- [x] Levantamento de endpoints por workspace
- [x] Identificação de ajustes necessários (EventStream, App)
- [ ] **PRÉ-REQUISITO:** PL003 implementado (isolamento de testes)
- [ ] Validação backend (#13)
- [ ] Ajustes frontend (#11, #12)
- [ ] Testes de validação (#14, #16)

---

## 1. Executivo Resumido

### Problema

Atualmente o WebUI da Skybridge **não implementa isolamento de workspaces** conforme especificado no ADR024. Todos os componentes mostram os mesmos dados independentemente do workspace selecionado, violando o princípio de multi-instância.

### Solução

**Implementar workspace-aware WebUI** onde todas as 8 páginas (1 Dashboard + 5 Operação + 2 Planejadas) respeitam o workspace ativo selecionado via header `X-Workspace`.

### Proposta de Valor

| Benefício | Antes | Depois |
|-----------|-------|--------|
| Isolamento de dados | Todos os workspaces misturados | Dados específicos por workspace |
| Multi-projeto | Impossível gerenciar múltiplos projetos | Workspaces para cada projeto/time |
| Segurança | Dados de trading misturados com core | Separação total por contexto |
| Escalabilidade | Single-instance | Multi-tenant ready |

---

## 2. Estrutura do WebUI

### 2.1 Páginas Implementadas

| # | Página | Tipo | Endpoint(s) | Status Workspace |
|---|--------|------|-------------|------------------|
| 1 | **Dashboard** | Dashboard | `/health`, `/webhooks/jobs`, `/logs/files` | ⚠️ #12 (App.tsx) |
| 2 | **Jobs** | Operação | `/webhooks/jobs` | ✅ OK |
| 3 | **Agents** | Operação | `/agents/executions`, `/agents/executions/{id}/messages` | ✅ OK |
| 4 | **Worktrees** | Operação | `/webhooks/worktrees`, DELETE `/webhooks/worktrees/{name}` | ✅ OK |
| 5 | **Events** | Operação | `/observability/events/*` | ⚠️ #11 (EventStream) |
| 6 | **Logs** | Operação | `/logs/*` | ✅ OK |
| 7 | **Kanban** | Planejada | - | 🔮 #17 (a implementar) |
| 8 | **Wiki** | Planejada | - | 🔮 #18 (a implementar) |

### 2.2 Componentes Internos

| Componente | Uso | Status Workspace |
|------------|-----|------------------|
| EventStream.tsx | Events page | ⚠️ **#11** - usa axios direto |
| LogStream.tsx | Dashboard/Logs | ✅ OK - usa observabilityApi |
| WorkspaceSelector.tsx | Header | ✅ OK - usa workspacesApi |
| ContextualNavbar.tsx | Navegação | ✅ OK - sem requisições |
| Sidebar.tsx | Navegação | ✅ OK - sem requisições |

---

## 3. Definições de Pronto (DoDs)

### DoD #1: Sem Placeholders

**Critério:** Todas as páginas planejadas (Kanban, Wiki) devem ter funcionalidade completa implementada, não placeholders.

```typescript
// ❌ NÃO ACEITO - Placeholder
export default function Kanban() {
  return (
    <Card className="p-4">
      <p className="text-muted mb-0">
        🚧 Em construção: Quadro Kanban para acompanhar o fluxo de trabalho dos agentes autônomos.
      </p>
    </Card>
  )
}

// ✅ ACEITO - Implementação funcional
export default function Kanban() {
  const { data: columns, isLoading } = useQuery({
    queryKey: ['kanban-columns'],
    queryFn: () => kanbanApi.getColumns()
  })

  if (isLoading) return <LoadingSpinner />

  return (
    <KanbanBoard
      columns={columns}
      onDragEnd={handleDragEnd}
      onCreateCard={createCard}
    />
  )
}
```

**Checklist:**
- [ ] Página Kanban tem funcionalidade completa (drag-and-drop, CRUD de cards)
- [ ] Página Wiki tem funcionalidade completa (criar/editar/páginas)
- [ ] Zero mensagens "Em construção"
- [ ] Zero componentes placeholder sem funcionalidade

### DoD #2: Testes para Todos os Componentes x Workspace

**Critério:** Cada página/componente que faz requisições à API deve ter testes validando o isolamento por workspace.

**Estrutura de Testes:**

```typescript
// ✅ PADRÃO DE TESTE - Isolamento por Workspace
describe('JobsPage - Workspace Isolation', () => {
  it('deve mostrar apenas jobs do workspace ativo', async () => {
    // GIVEN: Workspace core tem 3 jobs, trading tem 2 jobs
    mockApi.get('/api/webhooks/jobs')
      .withHeaders({ 'X-Workspace': 'core' })
      .reply(200, { jobs: coreJobs })

    mockApi.get('/api/webhooks/jobs')
      .withHeaders({ 'X-Workspace': 'trading' })
      .reply(200, { jobs: tradingJobs })

    // WHEN: Seleciona workspace core
    render(<JobsPage />)
    await waitFor(() => screen.getByText('core'))

    // THEN: Mostra apenas 3 jobs
    expect(screen.getAllByTestId(/job-item/)).toHaveLength(3)

    // WHEN: Troca para trading
    fireEvent.click(screen.getByText('Workspace Selector'))
    fireEvent.click(screen.getByText('Trading Bot'))

    // THEN: Mostra apenas 2 jobs
    await waitFor(() => {
      expect(screen.getAllByTestId(/job-item/)).toHaveLength(2)
    })
  })
})
```

**Checklist por Componente:**

| Componente | Teste de Isolamento | Teste de Troca | Teste de Erro |
|------------|---------------------|----------------|---------------|
| Dashboard.tsx | [ ] | [ ] | [ ] |
| Jobs.tsx | [ ] | [ ] | [ ] |
| Agents.tsx | [ ] | [ ] | [ ] |
| Worktrees.tsx | [ ] | [ ] | [ ] |
| Events.tsx | [ ] | [ ] | [ ] |
| Logs.tsx | [ ] | [ ] | [ ] |
| Kanban.tsx | [ ] | [ ] | [ ] |
| Wiki.tsx | [ ] | [ ] | [ ] |
| EventStream.tsx | [ ] | [ ] | [ ] |
| LogStream.tsx | [ ] | [ ] | [ ] |
| WorkspaceSelector.tsx | [x] | [ ] | [ ] |

### DoD #3: Backend Filtra por Workspace

**Critério:** Todos os endpoints da API implementam filtro por workspace usando o header `X-Workspace`.

**Validação:**

```python
# ✅ PADRÃO CORRETO - Backend filtra por workspace
@router.get("/api/webhooks/jobs")
async def list_jobs(request: Request):
    # 1. Extrai workspace do header
    workspace_id = request.headers.get("X-Workspace", "core")

    # 2. Usa workspace para filtrar/buscar dados
    job_queue = get_job_queue_for_workspace(workspace_id)

    # 3. Retorna apenas dados do workspace solicitado
    return {"jobs": job_queue.get_all_jobs()}
```

**Checklist de Endpoints:**

| Endpoint | Filtra por Workspace | Implementado |
|----------|----------------------|--------------|
| GET /api/health | N/A (global) | [ ] |
| GET /api/webhooks/jobs | [ ] | [ ] |
| GET /api/agents/executions | [ ] | [ ] |
| GET /api/agents/executions/{id}/messages | [ ] | [ ] |
| GET /api/webhooks/worktrees | [ ] | [ ] |
| DELETE /api/webhooks/worktrees/{name} | [ ] | [ ] |
| DELETE /api/observability/events/history | [ ] | [ ] |
| POST /api/observability/events/generate-fake | [ ] | [ ] |
| GET /api/logs/files | [ ] | [ ] |
| GET /api/logs/file/{filename} | [ ] | [ ] |

### DoD #4: Frontend Usa Apenas apiClient

**Critério:** Todas as requisições HTTP usam `apiClient` (nunca `axios` ou `fetch` direto).

```typescript
// ❌ NÃO ACEITO - Usa axios diretamente
import axios from 'axios'
const response = await axios.delete('/api/observability/events/history')

// ✅ ACEITO - Usa apiClient com header X-Workspace
import apiClient from '@/api/client'
const response = await apiClient.delete('/api/observability/events/history')

// ✅ ACEITO - Usa endpoint com tipagem
import { observabilityApi } from '@/api/endpoints'
await observabilityApi.clearEventHistory()
```

**Arquivos para Validar:**

| Arquivo | Usa apiClient? | Status |
|---------|----------------|--------|
| App.tsx | [ ] | ⚠️ #12 |
| EventStream.tsx | [ ] | ⚠️ #11 |
| Dashboard.tsx | [x] | ✅ |
| Jobs.tsx | [x] | ✅ |
| Agents.tsx | [x] | ✅ |
| Worktrees.tsx | [x] | ✅ |
| Events.tsx | [x] | ✅ |
| Logs.tsx | [x] | ✅ |
| Kanban.tsx | [ ] | 🔮 |
| Wiki.tsx | [ ] | 🔮 |

---

## 4. Plano para Página Kanban

### 4.1 Propósito

Conforme PRD013 (Orquestração Multi-Agente) e SPEC009, o Kanban visualiza o fluxo de trabalho dos agentes autônomos com estados:

```
OPEN → IN_PROGRESS → READY_FOR_TEST → UNDER_CHALLENGE → AWAITING_HUMAN_APPROVAL → VERIFIED → CLOSED
```

### 4.2 Funcionalidades

#### RF001: Quadro Kanban Visual
- **Descrição:** Visualizar cards de issues em colunas por estado
- **Colunas:** Backlog, Em Progresso, Em Teste, Em Revisão, Pronto, Fechado
- **Drag-and-Drop:** Mover cards entre colunas
- **Filtros:** Por workspace, por label, por assignee
- **Prioridade:** Alta

#### RF002: Gestão de Cards
- **Descrição:** Criar, editar, deletar cards
- **Campos:** Título, descrição, labels, assignee, prioridade
- **Prioridade:** Alta

#### RF003: Detalhes do Card
- **Descrição:** Modal com detalhes completos do card
- **Abas:** Discussão, Thinking Steps, Logs, Files Changed
- **Prioridade:** Média

#### RF004: Integração com Agents
- **Descrição:** Cards são criados/atualizados por agentes automaticamente
- **Eventos:** Agent cria card, move entre colunas, adiciona comentários
- **Prioridade:** Alta

### 4.3 Endpoints Backend

```python
# Novos endpoints para Kanban
@router.get("/api/kanban/columns")
async def get_columns(request: Request):
    """Retorna colunas do Kanban filtradas por workspace."""
    workspace_id = request.headers.get("X-Workspace", "core")
    return kanban_service.get_columns(workspace_id)

@router.get("/api/kanban/cards")
async def get_cards(request: Request, column_id: str | None = None):
    """Retorna cards do Kanban filtrados por workspace e coluna."""
    workspace_id = request.headers.get("X-Workspace", "core")
    return kanban_service.get_cards(workspace_id, column_id)

@router.post("/api/kanban/cards")
async def create_card(request: Request, card: CardCreate):
    """Cria novo card no workspace."""
    workspace_id = request.headers.get("X-Workspace", "core")
    return kanban_service.create_card(workspace_id, card)

@router.patch("/api/kanban/cards/{card_id}")
async def update_card(request: Request, card_id: str, card: CardUpdate):
    """Atualiza card (mover coluna, editar campos)."""
    workspace_id = request.headers.get("X-Workspace", "core")
    return kanban_service.update_card(workspace_id, card_id, card)

@router.delete("/api/kanban/cards/{card_id}")
async def delete_card(request: Request, card_id: str):
    """Deleta card do workspace."""
    workspace_id = request.headers.get("X-Workspace", "core")
    return kanban_service.delete_card(workspace_id, card_id)
```

### 4.4 Componentes Frontend

```
apps/web/src/
├── pages/
│   └── Kanban.tsx                   # Página principal
├── components/
│   ├── Kanban/
│   │   ├── KanbanBoard.tsx          # Quadro com colunas
│   │   ├── KanbanColumn.tsx         # Coluna com cards
│   │   ├── KanbanCard.tsx           # Card individual
│   │   ├── CardModal.tsx            # Modal de detalhes
│   │   ├── CreateCardModal.tsx      # Modal de criação
│   │   └── KanbanFilters.tsx        # Filtros por workspace/labels
│   └── __tests__/
│       └── Kanban.test.tsx          # Testes de isolamento
```

### 4.5 Roadmap Kanban

| Fase | Tarefa | Status |
|------|--------|--------|
| 1 | Backend: Endpoints Kanban | 🔮 Pendente |
| 2 | Frontend: KanbanBoard básico | 🔮 Pendente |
| 3 | Frontend: Drag-and-Drop | 🔮 Pendente |
| 4 | Frontend: Modais (CRUD) | 🔮 Pendente |
| 5 | Frontend: Filtros workspace | 🔮 Pendente |
| 6 | Integração: Agents → Kanban | 🔮 Pendente |
| 7 | Testes: Isolamento workspace | 🔮 Pendente |

---

## 5. Plano para Página Wiki

### 5.1 Propósito

Conforme visão Skybridge (core/vision.md), a Wiki é documentação colaborativa de tarefas e procedimentos por workspace.

### 5.2 Funcionalidades

#### RF001: Páginas Wiki
- **Descrição:** Criar, editar, visualizar páginas de documentação
- **Markdown:** Suporte completo a Markdown
- **Preview:** Live preview de Markdown
- **Prioridade:** Alta

#### RF002: Organização
- **Descrição:** Hierarquia de páginas, categorias, tags
- **Busca:** Full-text search em páginas
- **Histórico:** Versionamento de edições
- **Prioridade:** Média

#### RF003: Colaboração
- **Descrição:** Múltiplos editores, comentários, sugestões
- **Lock:** Edição exclusiva (prevenir conflitos)
- **Prioridade:** Baixa

### 5.3 Endpoints Backend

```python
# Novos endpoints para Wiki
@router.get("/api/wiki/pages")
async def get_pages(request: Request):
    """Retorna páginas wiki filtradas por workspace."""
    workspace_id = request.headers.get("X-Workspace", "core")
    return wiki_service.get_pages(workspace_id)

@router.get("/api/wiki/pages/{slug}")
async def get_page(request: Request, slug: str):
    """Retorna página wiki específica."""
    workspace_id = request.headers.get("X-Workspace", "core")
    return wiki_service.get_page(workspace_id, slug)

@router.post("/api/wiki/pages")
async def create_page(request: Request, page: PageCreate):
    """Cria nova página wiki no workspace."""
    workspace_id = request.headers.get("X-Workspace", "core")
    return wiki_service.create_page(workspace_id, page)

@router.put("/api/wiki/pages/{slug}")
async def update_page(request: Request, slug: str, page: PageUpdate):
    """Atualiza página wiki."""
    workspace_id = request.headers.get("X-Workspace", "core")
    return wiki_service.update_page(workspace_id, slug, page)

@router.delete("/api/wiki/pages/{slug}")
async def delete_page(request: Request, slug: str):
    """Deleta página wiki do workspace."""
    workspace_id = request.headers.get("X-Workspace", "core")
    return wiki_service.delete_page(workspace_id, slug)
```

### 5.4 Componentes Frontend

```
apps/web/src/
├── pages/
│   └── Wiki.tsx                     # Página principal
├── components/
│   ├── Wiki/
│   │   ├── WikiList.tsx             # Lista de páginas
│   │   ├── WikiPage.tsx             # Visualizador de página
│   │   ├── WikiEditor.tsx           # Editor Markdown
│   │   ├── WikiSearch.tsx           # Busca full-text
│   │   ├── WikiSidebar.tsx          # Árvore de páginas
│   │   └── PageHistory.tsx          # Histórico de versões
│   └── __tests__/
│       └── Wiki.test.tsx            # Testes de isolamento
```

### 5.5 Roadmap Wiki

| Fase | Tarefa | Status |
|------|--------|--------|
| 1 | Backend: Endpoints Wiki | 🔮 Pendente |
| 2 | Frontend: WikiList + WikiPage básicos | 🔮 Pendente |
| 3 | Frontend: Editor Markdown + Preview | 🔮 Pendente |
| 4 | Frontend: Árvore de páginas | 🔮 Pendente |
| 5 | Frontend: Busca full-text | 🔮 Pendente |
| 6 | Frontend: Filtros workspace | 🔮 Pendente |
| 7 | Testes: Isolamento workspace | 🔮 Pendente |

---

## 6. Plano de Execução

### Fase 1: Fundamentos (Bloqueio Crítico)
**Objetivo:** Validar e ajustar backend/frontend para workspace-aware

| # | Tarefa | Depende de |
|---|--------|-----------|
| #13 | Validar backend filtra por workspace | - |
| #11 | Ajustar EventStream.tsx para usar apiClient | #13 |
| #12 | Ajustar App.tsx para usar healthApi.get() | #13 |
| #16 | Validar dados por workspace nos componentes | #11, #12, #13 |

### Fase 2: Testes e Validação
**Objetivo:** Garantir isolamento completo

| # | Tarefa | Depende de |
|---|--------|-----------|
| #14 | Teste e2e de troca de workspace | #16 |
| #15 | Documentar arquitetura de workspace no frontend | #16 |

### Fase 3: Implementação de Páginas Planejadas
**Objetivo:** Completar Kanban e Wiki sem placeholders

| # | Tarefa | Depende de |
|---|--------|-----------|
| #17 | Criar página Kanban com suporte a workspace | #16 |
| #18 | Criar página Wiki com suporte a workspace | #16 |

---

## 7. Success Metrics

### Métricas de Qualidade

| Métrica | Target | Como Medir |
|---------|--------|------------|
| Cobertura de testes workspace | 100% dos componentes | `pytest --cov=apps/web` |
| Zero placeholders | 0 páginas placeholder | Code review |
| Isolamento de dados | 100% dos endpoints | Validação backend |
| Compliance apiClient | 100% das requisições | Lint rule |

### Métricas de Usabilidade

| Métrica | Baseline | Target |
|---------|----------|--------|
| Tempo para trocar workspace | N/A | <1s |
| Tempo para carregar dados do workspace | N/A | <2s |
| Confusão entre workspaces | Alta | Zero (pesquisa) |

---

## 8. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Backend não filtra por workspace | Alta | Crítico | **Validar primeiro (#13)** |
| Memory leak ao trocar workspace | Média | Médio | React Query auto-cleanup |
| Frontend usa axios/fetch direto | Média | Alto | **Lint rule para apiClient** |
| Kanban/Wiki viram placeholders | Baixa | Alto | **DoD #1 explícito** |

---

## 9. Referências

- **ADR024:** Workspaces Multi-Instância
- **PRD013:** Webhook Autonomous Agents
- **PRD014:** WebUI Dashboard
- **SPEC008:** AI Agent Interface
- **SPEC009:** Orquestração Multi-Agente
- **PB013:** Workspaces CLI

---

## Aprovações

| Papel | Nome | Data | Assinatura |
|-------|------|------|------------|
| Autor | Sky | 2026-02-01 | ✍️ |

---

> "A melhor forma de prever o futuro é criá-lo" – made by Sky 🚀

---

**Documento versão:** 1.0
**Última atualização:** 2026-02-01
**Status:** 🚧 Em Elaboração
