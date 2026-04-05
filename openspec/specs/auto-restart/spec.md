# auto-restart Specification

## Purpose
TBD - created by archiving change document-track-productivity-system. Update Purpose after archive.
## Requirements
### Requirement: Verificação de consistência
O sistema SHALL verificar consistência entre estado local (state.json) e realidade do Toggl antes de cada ação.

#### Scenario: Estado consistente
- **WHEN** state.json indica `running: true` e Toggl confirma timer rodando
- **THEN** sistema prossegue com ação solicitada normalmente

#### Scenario: Estado inconsistente detectado
- **WHEN** state.json indica `running: true` mas Toggl reports `running: false`
- **THEN** sistema detecta parada inesperada
- **AND** retorna ação `auto_restart` com motivos

### Requirement: Auto-restart de timer
O sistema SHALL reiniciar automaticamente timer parado inesperadamente.

#### Scenario: Reinício automático
- **WHEN** inconsistência é detectada (state diz rodando, Toggl diz parado)
- **THEN** sistema retorna `{"action": "auto_restart", "reason": "...", ...}`
- **AND** parâmetros do último timer (project, tags, description) são preservados
- **AND** evento é registrado em events.log

#### Scenario: Confirmação de restart
- **WHEN** ação `auto_restart` é executada
- **THEN** novo timer é iniciado via `toggl_start_timer`
- **AND** usuário recebe notificação: "⚠️ Timer parado inesperadamente (possível conflito Desktop/Chrome)"

### Requirement: Event logging
O sistema SHALL registrar todos os eventos de auto-restart para debug.

#### Scenario: Registro de auto-restart
- **WHEN** auto-restart é executado
- **THEN** evento é registrado em `data/events.log`
- **AND** formato: `timestamp | auto_restart | Timer parado inesperadamente, reiniciado`

#### Scenario: Registro de start/stop
- **WHEN** timer é iniciado ou parado normalmente
- **THEN** evento é registrado com tipo `start` ou `stop`
- **AND** duration é incluída para eventos `stop`

### Requirement: Detecção de conflitos
O sistema SHALL identificar possíveis causas de parada inesperada.

#### Scenario: Conflito Desktop/Chrome
- **WHEN** timer MCP é parado por app Desktop ou Chrome
- **THEN** consistency_check detecta parada
- **AND** reason inclui "(possível conflito Desktop/Chrome)"

#### Scenario: Pomodoro automático
- **WHEN** Toggl Desktop tem Pomodoro automático configurado
- **THEN** sistema detecta entries com `duronly: true` e múltiplos de 25min
- **AND** padrão é documentado em events.log

---

> "Auto-recuperação é melhor que auto-piedade" – made by Sky [restart]

