## ADDED Requirements

### Requirement: Channel MCP empurra eventos significativos para Claude Code

O Channel MCP (`planet-crafter-channel.py`) SHALL fazer polling de `GET /events` no mod em intervalo de 10s e enviar `JSONRPCNotification` via `notifications/claude/channel` quando a fila de eventos não estiver vazia.

#### Scenario: Evento significativo gera notificação

- **WHEN** o polling de `GET /events` retorna pelo menos 1 evento (ex: milestone de terraformação)
- **THEN** o Channel MCP envia `JSONRPCNotification` com method `notifications/claude/channel` contendo descrição do evento

#### Scenario: Sem eventos, sem notificação

- **WHEN** o polling de `GET /events` retorna array vazio
- **THEN** o Channel MCP NÃO envia notificação

### Requirement: Throttling mínimo de 30s entre notificações

O Channel MCP SHALL respeitar intervalo mínimo de 30 segundos entre notificações para não lotar o contexto do Claude Code.

#### Scenario: Eventos rápidos são agrupados

- **WHEN** dois eventos significativos ocorrem com menos de 30s de diferença
- **THEN** o Channel MCP envia apenas uma notificação combinando ambos os eventos após o throttle

#### Scenario: Intervalo normal entre eventos

- **WHEN** dois eventos ocorrem com mais de 30s de diferença
- **THEN** o Channel MCP envia duas notificações separadas

### Requirement: Channel MCP declara capability experimental claude/channel

O servidor MCP SHALL declarar `capabilities.experimental = {"claude/channel": {}}` na inicialização para que Claude Code registre o listener de notificações.

#### Scenario: Capability declarada na inicialização

- **WHEN** o Channel MCP inicializa com Claude Code
- **THEN** o `create_initialization_options()` inclui `capabilities.experimental = {"claude/channel": {}}`

### Requirement: Channel MCP reconecta automaticamente ao mod

O Channel MCP SHALL lidar com falhas de conexão ao mod (jogo fechado, mod crashou) sem crashar, tentando reconectar.

#### Scenario: Mod indisponível

- **WHEN** o polling falha (Connection refused, timeout) porque o jogo está fechado
- **THEN** o Channel MCP loga o erro e tenta novamente no próximo ciclo de polling (10s), sem crashar

#### Scenario: Mod volta a ficar disponível

- **WHEN** o jogo é aberto após um período de indisponibilidade
- **THEN** o Channel MCP retoma o polling normalmente no próximo ciclo
