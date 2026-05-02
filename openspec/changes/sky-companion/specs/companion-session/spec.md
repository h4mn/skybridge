## ADDED Requirements

### Requirement: Sessão de jogatina é iniciada ao conectar ao mod

O sistema SHALL criar uma sessão de jogatina quando o Channel MCP se conecta com sucesso ao mod pela primeira vez. A sessão DEVE registrar timestamp de início.

#### Scenario: Sessão criada ao primeiro polling bem-sucedido

- **WHEN** o Channel MCP faz o primeiro polling bem-sucedido a `GET /state` após inicialização
- **THEN** uma sessão é criada com timestamp de início e status "active"

### Requirement: Eventos da sessão são registrados

O sistema SHALL registrar todos os eventos recebidos via Channel MCP durante a sessão, com timestamp e tipo.

#### Scenario: Evento de milestone registrado na sessão

- **WHEN** o Channel MCP recebe evento de milestone de terraformação
- **THEN** o evento é adicionado ao log da sessão com tipo "milestone", descrição e timestamp

#### Scenario: Evento de chat registrado na sessão

- **WHEN** o Channel MCP recebe evento `/skychat`
- **THEN** o evento é adicionado ao log da sessão com tipo "skychat", mensagem do jogador e timestamp

### Requirement: Notas podem ser adicionadas à sessão

O sistema SHALL permitir que Claude Code adicione notas à sessão via tool `add_session_note(text)`.

#### Scenario: Nota adicionada

- **WHEN** Claude Code chama `add_session_note` com text = "Jogador preferiu focar em O2 primeiro"
- **THEN** a nota é adicionada ao log da sessão com tipo "note" e timestamp

### Requirement: Sessão é encerrada ao desconectar do mod

O sistema SHALL encerrar a sessão quando o Channel MCP detecta que o mod ficou indisponível por tempo prolongado (ex: jogo fechado). A sessão DEVE registrar timestamp de fim e duração total.

#### Scenario: Sessão encerrada ao fechar jogo

- **WHEN** o Channel MCP detecta que o mod está indisponível por mais de 60 segundos consecutivos
- **THEN** a sessão é encerrada com timestamp de fim e duração calculada

#### Scenario: Sessão NÃO encerrada em falha temporária

- **WHEN** o mod falha em responder 1-2 polling cycles mas volta a responder
- **THEN** a sessão permanece ativa (não encerra por falhas temporárias)

### Requirement: Resumo da sessão disponível

O sistema SHALL fornecer um resumo da sessão via tool `get_session_summary()` incluindo duração, milestones atingidos, eventos significativos e notas.

#### Scenario: Resumo com sessão ativa

- **WHEN** Claude Code chama `get_session_summary` durante uma sessão ativa
- **THEN** o tool retorna duração atual, contagem de eventos por tipo, lista de milestones e notas

#### Scenario: Resumo com sessão encerrada

- **WHEN** Claude Code chama `get_session_summary` após a sessão ter sido encerrada
- **THEN** o tool retorna resumo completo com duração total e todos os eventos registrados
