# Spec: Performance Cache

Capability para cache local que otimiza performance da skill /track para < 30s.

## ADDED Requirements

### Requirement: Cache de state local
O sistema SHALL manter cache local em state.json para evitar chamadas MCP pesadas.

#### Scenario: Cache hit
- **WHEN** operação precisa de dados que estão em state.json
- **THEN** sistema lê de state.json (< 300ms)
- **AND** evita chamar `get_time_entries` (3-5min)

#### Scenario: Cache miss
- **WHEN** dado solicitado não está em state.json
- **THEN** sistema busca via MCP e atualiza cache
- **AND** próxima operação beneficia do cache

### Requirement: Project cache
O sistema SHALL mapear nomes de projetos para IDs Toggl.

#### Scenario: ID de projeto conhecido
- **WHEN** usuário inicia timer com projeto "skybridge"
- **THEN** sistema busca ID em project_cache (219139925)
- **AND** não precisa chamar `toggl_list_projects`

#### Scenario: Projeto desconhecido
- **WHEN** projeto não está em project_cache
- **THEN** sistema busca via MCP e adiciona ao cache
- **AND** futuras operações usam cached ID

#### Scenario: Cache de workspace
- **WHEN** workspace_id é necessário
- **THEN** sistema usa DEFAULT_WORKSPACE de state.json (20989145)
- **AND** evita `toggl_list_workspaces`

### Requirement: Context tracking
O sistema SHALL rastrear contexto de trabalho (projeto, fase).

#### Scenario: Contexto atual
- **WHEN** usuário inicia timer sem especificar projeto
- **THEN** sistema usa contexto de state.json
- **AND** infere project e tags baseados em sessão atual

#### Scenario: Atualização de contexto
- **WHEN** contexto muda (ex: novo projeto)
- **THEN** state.json é atualizado
- **AND** próximos timers usam novo contexto

### Requirement: Otimização < 30s
O sistema SHALL garantir resposta em < 30s para todas as operações.

#### Scenario: Retoma de pomodoro (verify-first)
- **WHEN** usuário solicita "retoma o pomodoro" sem modo otimista
- **THEN** tempo total < 30s
- **AND** breakdown: orchestrator (< 300ms) + MCP start_timer (~25s)

#### Scenario: Retoma de pomodoro (optimistic-start)
- **WHEN** usuário solicita "retoma o pomodoro" com --optimistic
- **THEN** tempo perceived < 5s (apenas orchestrator + confirmação)
- **AND** MCP start_timer ocorre em background
- **AND** verify_after=true indica que verificação é necessária

#### Scenario: Nova track
- **WHEN** usuário inicia nova tracking
- **THEN** tempo total < 30s
- **AND** state.json fornece todos os parâmetros necessários

#### Scenario: Status check
- **WHEN** usuário verifica status
- **THEN** tempo < 1s
- **AND** apenas state.json é lido (sem chamada MCP)

### Requirement: Sincronização bidirecional
O sistema SHALL manter sincronia entre cache e API Toggl.

#### Scenario: Atualização pós-start
- **WHEN** timer é iniciado via MCP
- **THEN** state.json é atualizado com `running: true`
- **AND** `last_start` é registrado

#### Scenario: Atualização pós-stop
- **WHEN** timer é parado via MCP
- **THEN** state.json é atualizado com `running: false`
- **AND** `last_stop` e `last_duration` são registrados

---

> "Cache local é a diferença entre 3min e 30s" – made by Sky [performance]
