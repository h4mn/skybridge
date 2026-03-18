# PRD025: WebUI - Workspaces Globais com Isolamento Completo

**Status:** 🚧 Em Implementação
**Data:** 2026-02-01
**Autor:** Sky
**Versão:** 1.2
**Depende de:** PL003 (Isolamento Profissional de Testes) - ✅ COMPLETO

---

## Status de Implementação

### Fase 1: Fundamentos - ✅ COMPLETADO

**PL003 JÁ IMPLEMENTADO:** Isolamento profissional de testes foi implementado anteriormente.

- [x] Análise de componentes existentes
- [x] Levantamento de endpoints por workspace
- [x] Identificação de ajustes necessários (EventStream, App)
- [x] **PRÉ-REQUISITO:** PL003 implementado (isolamento de testes)
- [x] Validação backend (#13)
- [x] Ajustes frontend (#11, #12)
- [x] Validação de dados por workspace (#16)

### Fase 2: Testes e Validação - ✅ COMPLETADO

- [x] Teste e2e de troca de workspace (#14)
- [x] Testes de isolamento para Dashboard
- [x] Testes de isolamento para Jobs
- [x] Testes de isolamento para EventStream
- [x] Documentação de arquitetura de workspace no frontend (#15)

### Fase 3: Implementação de Páginas Planejadas

**MOVIDO PARA PRDS DEDICADAS:**

- **Kanban:** Veja [PRD024 - Kanban Cards Vivos](../prd/PRD024-kanban-cards-vivos.md)
- **Wiki:** Veja [PRD025 - Wiki Markdown Colaborativa](../prd/PRD025-wiki-markdown-colaborativa.md)

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
| 7 | **Kanban** | Planejada | `/api/kanban/*` | 🔮 *(veja [PRD024](../prd/PRD024-kanban-cards-vivos.md))* |
| 8 | **Wiki** | Planejada | `/api/wiki/*` | 🔮 *(veja [PRD025](../prd/PRD025-wiki-markdown-colaborativa.md))* |

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
- [ ] Página Kanban tem funcionalidade completa (veja [PRD024](../prd/PRD024-kanban-cards-vivos.md))
- [ ] Página Wiki tem funcionalidade completa (veja [PRD025](../prd/PRD025-wiki-markdown-colaborativa.md))
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
| Dashboard.tsx | [x] | [x] | [x] |
| Jobs.tsx | [x] | [x] | [x] |
| Agents.tsx | [x] | [x] | [x] |
| Worktrees.tsx | [x] | [x] | [x] |
| Events.tsx | [x] | [x] | [x] |
| Logs.tsx | [x] | [x] | [x] |
| Kanban.tsx | [ ] | [ ] | [ ] *(veja PRD024)* |
| Wiki.tsx | [ ] | [ ] | [ ] *(veja PRD025)* |
| EventStream.tsx | [x] | [x] | [x] |
| LogStream.tsx | [x] | [x] | [x] |
| WorkspaceSelector.tsx | [x] | [x] | [x] |

**Arquivos de Teste Criados:**
- `apps/web/src/pages/__tests__/Dashboard.test.tsx` - Atualizado com testes de workspace
- `apps/web/src/pages/__tests__/Jobs.workspace.test.tsx` - Novo arquivo com testes de isolamento
- `apps/web/src/components/__tests__/EventStream.workspace.test.tsx` - Novo arquivo com testes de SSE
- `apps/web/src/test/workspace-switching.e2e.test.ts` - Novo arquivo com testes e2e de troca

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
| GET /api/health | N/A (global) | [x] |
| GET /api/webhooks/jobs | [x] | [x] |
| GET /api/agents/executions | [x] | [x] |
| GET /api/agents/executions/{id}/messages | [x] | [x] |
| GET /api/webhooks/worktrees | [x] | [x] |
| DELETE /api/webhooks/worktrees/{name} | [x] | [x] |
| DELETE /api/observability/events/history | [x] | [x] |
| POST /api/observability/events/generate-fake | [x] | [x] |
| GET /api/observability/events/stream | [x] (query param) | [x] |
| GET /api/logs/files | [x] | [x] |
| GET /api/logs/file/{filename} | [x] | [x] |

**Mudanças Implementadas:**
- `get_job_queue()` - Cache por workspace em `handlers.py:109-154`
- `get_agent_execution_store()` - Cache por workspace em `handlers.py:174-218`
- `/webhooks/worktrees/*` - Usa workspace do contexto em `routes.py:846-1057`
- `/observability/events/stream` - Aceita query parameter `workspace` em `routes.py:1150`

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
| App.tsx | [x] | ✅ |
| EventStream.tsx | [x] | ✅ |
| Dashboard.tsx | [x] | ✅ |
| Jobs.tsx | [x] | ✅ |
| Agents.tsx | [x] | ✅ |
| Worktrees.tsx | [x] | ✅ |
| Events.tsx | [x] | ✅ |
| Logs.tsx | [x] | ✅ |
| Kanban.tsx | [ ] | 🔮 (veja PRD024) |
| Wiki.tsx | [ ] | 🔮 (veja PRD025) |

---

## 4. Páginas Planejadas - Referências

As páginas Kanban e Wiki foram movidas para PRDs dedicadas:

### 4.1 Kanban Board

**PRD024:** Kanban - Cards Vivos com Sincronização Trello

- Fonte única da verdade em kanban.db (SQLite)
- Sincronização bidirecional com Trello
- "Cards vivos" que mostram quando agentes estão processando
- Suporte a múltiplos workspaces

Ver: [docs/prd/PRD024-kanban-cards-vivos.md](../prd/PRD024-kanban-cards-vivos.md)

### 4.2 Wiki Colaborativa

**PRD025:** Wiki - Markdown Colaborativa por Workspace

- Markdown completo com live preview
- Organização hierárquica de páginas
- Busca full-text
- Histórico de versões
- Suporte a múltiplos workspaces

Ver: [docs/prd/PRD025-wiki-markdown-colaborativa.md](../prd/PRD025-wiki-markdown-colaborativa.md)

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

### Fase 3: Páginas Planejadas
**Objetivo:** Kanban e Wiki têm suas próprias PRDs

| # | Tarefa | Depende de | PRD |
|---|--------|-----------|-----|
| - | Kanban Board (cards vivos + sync Trello) | ADR024 | [PRD024](../prd/PRD024-kanban-cards-vivos.md) |
| - | Wiki Colaborativa (markdown) | ADR024 | [PRD025](../prd/PRD025-wiki-markdown-colaborativa.md) |

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
