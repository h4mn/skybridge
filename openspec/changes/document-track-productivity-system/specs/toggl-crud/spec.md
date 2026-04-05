# Spec: Toggl CRUD

Capability para operações CRUD completas de time entries no Toggl via MCP.

## ADDED Requirements

### Requirement: Iniciar timer
O sistema SHALL iniciar um novo timer no Toggl com projeto, tags e descrição fornecidos.

#### Scenario: Início bem-sucedido
- **WHEN** usuário solicita iniciar timer com parâmetros válidos
- **THEN** sistema chama `toggl_start_timer` via MCP
- **AND** timer é criado no Toggl com ID único
- **AND** state.json é atualizado com `running: true`

#### Scenario: Início sem workspace
- **WHEN** workspace_id não é fornecido
- **THEN** sistema usa workspace_id do state.json
- **AND** retorna erro se não houver workspace configurado

### Requirement: Verificar timer atual
O sistema SHALL verificar se há um timer rodando no Toggl.

#### Scenario: Timer rodando
- **WHEN** usuário verifica status e timer está rodando
- **THEN** sistema chama `get_current_entry` via MCP
- **AND** retorna `{"running": true, ...}` com detalhes da entry

#### Scenario: Timer parado
- **WHEN** usuário verifica status e não há timer rodando
- **THEN** sistema retorna `{"running": false}`

### Requirement: Buscar histórico
O sistema SHALL buscar entries históricas por período.

#### Scenario: Buscar entries de hoje
- **WHEN** usuário solicita entries do período "today"
- **THEN** sistema chama `get_time_entries(period="today")`
- **AND** retorna lista de entries com start, stop, duration, tags

#### Scenario: Buscar por intervalo
- **WHEN** usuário fornece start_date e end_date
- **THEN** sistema busca entries no intervalo especificado

### Requirement: Parar timer
O sistema SHALL parar o timer rodando e gravar duration.

#### Scenario: Parada bem-sucedida
- **WHEN** usuário solicita parar timer
- **THEN** sistema chama `toggl_stop_timer` via MCP
- **AND** duration é calculada e gravada no Toggl
- **AND** state.json é atualizado com `running: false`
- **AND** last_stop e last_duration são registrados

### Requirement: Atualizar entry
O sistema SHALL modificar descrição e tags de uma entry existente.

#### Scenario: Atualizar descrição
- **WHEN** usuário solicita modificar descrição de entry
- **THEN** sistema atualiza entry via Toggl API
- **AND** novas tags são aplicadas se fornecidas

#### Scenario: Entry inexistente
- **WHEN** entry_id fornecido não existe
- **THEN** sistema retorna erro apropriado

---

> "CRUD completo é liberdade de gerenciar seu tempo" – made by Sky [toggl]
