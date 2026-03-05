# Histórico de Sessão para Debug

Especificação para salvamento de histórico de sessão em arquivo JSON para debugging.

## ADDED Requirements

### Requirement: Histórico de sessão salvo em arquivo JSON
O sistema SHALL salvar o histórico completo da sessão de chat em um arquivo JSON no diretório `.sky/debug/` para fins de debugging.

#### Scenario: Arquivo criado ao encerrar sessão
- **WHEN** sessão de chat é encerrada (método `close()`)
- **THEN** sistema cria arquivo `.sky/debug/session_<timestamp>.json`
- **AND** arquivo contém histórico completo da sessão

#### Scenario: Arquivo contém mensagens e metadados
- **WHEN** arquivo de histórico é aberto
- **THEN** contém array de mensagens com `role`, `content`, `timestamp`
- **AND** contém metadados: `session_id`, `model`, `total_turns`, `duration_ms`

### Requirement: Histórico inclui uso de ferramentas
O sistema SHALL registrar todas as chamadas de ferramentas realizadas pelo SDK durante a sessão.

#### Scenario: Chamadas de ferramenta são registradas
- **WHEN** Sky usa ferramenta `Read`, `Glob` ou `Grep`
- **THEN** histórico inclui entrada `tool_use` com nome, parâmetros e resultado
- **AND** timestamp da chamada é registrado

#### Scenario: Erros de ferramenta são registrados
- **WHEN** ferramenta retorna erro
- **THEN** histórico inclui entrada `tool_error` com mensagem de erro
- **AND** stack trace é incluído se disponível

### Requirement: Nome de arquivo único por sessão
O sistema SHALL gerar nomes de arquivos únicos usando timestamp para evitar sobrescrever sessões anteriores.

#### Scenario: Timestamp ISO 8601 no nome
- **WHEN** novo arquivo de histórico é criado
- **THEN** nome segue formato `session_<YYYYMMDD>T<HHMMSS>.json`
- **AND** fuso horário é UTC

#### Scenario: Múltiplas sessões não colidem
- **WHEN** duas sessões são encerradas no mesmo segundo
- **THEN** cada arquivo tem nome único (timestamp inclui milissegundos se necessário)

### Requirement: Diretório de debug criado automaticamente
O sistema SHALL criar diretório `.sky/debug/` automaticamente se não existir.

#### Scenario: Diretório criado no primeiro histórico
- **WHEN** primeiro histórico é salvo
- **THEN** diretório `.sky/debug/` é criado se não existir
- **AND** histórico é salvo com sucesso

### Requirement: Histórico opcional/configurável
O sistema SHALL permitir desabilitar salvamento de histórico via configuração.

#### Scenario: Variável de ambiente controla histórico
- **WHEN** `SKY_CHAT_DEBUG_HISTORY=false` é definido
- **THEN** nenhum arquivo de histórico é criado
- **AND** sessão funciona normalmente

#### Scenario: Padrão é salvar histórico
- **WHEN** variável não está definida
- **THEN** histórico é salvo (comportamento padrão)
