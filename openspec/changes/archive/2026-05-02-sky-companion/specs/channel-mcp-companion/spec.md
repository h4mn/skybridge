## ADDED Requirements

### Requirement: Channel MCP empurra eventos significativos para Claude Code

O Channel MCP (`planet-crafter-channel.py`) SHALL fazer polling de `GET /events` no mod e enviar `JSONRPCNotification` via `notifications/claude/channel` quando a fila de eventos não estiver vazia.

**Throttling**: O Channel MCP SHALL usar throttling diferenciado por tipo de evento:
- **Chat (`skychat`)**: sem throttle — notificação imediata (até 2s de delay)
- **Milestone/terraform**: throttle de 30s — agrupa eventos de progresso
- **Morte/ação**: throttle de 10s

**Polling**: Intervalo de 2s para verificar eventos de chat, 10s para outros tipos.

#### Scenario: Evento de chat gera notificação imediata

- **WHEN** o polling detecta evento tipo "skychat"
- **THEN** o Channel MCP envia notificação imediatamente, sem aguardar throttle

#### Scenario: Evento significativo gera notificação

- **WHEN** o polling de `GET /events` retorna pelo menos 1 evento (ex: milestone de terraformação)
- **THEN** o Channel MCP envia `JSONRPCNotification` com method `notifications/claude/channel` contendo descrição do evento

#### Scenario: Sem eventos, sem notificação

- **WHEN** o polling de `GET /events` retorna array vazio
- **THEN** o Channel MCP NÃO envia notificação

### Requirement: Throttling diferenciado por tipo de evento (DEPRECATED: migrado pra requirement acima)

~~O Channel MCP SHALL respeitar intervalo mínimo de 30 segundos entre notificações para não lotar o contexto do Claude Code.~~

**Novo comportamento**: Throttle é por categoria. Chat sem throttle, milestones com 30s, outros com 10s.

#### Scenario: Eventos de milestone são agrupados

- **WHEN** dois milestones ocorrem com menos de 30s de diferença
- **THEN** o Channel MCP envia apenas uma notificação combinando ambos após o throttle

#### Scenario: Chat não é throttled

- **WHEN** duas mensagens /skychat chegam com menos de 30s de diferença
- **THEN** o Channel MCP envia duas notificações separadas imediatamente

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
