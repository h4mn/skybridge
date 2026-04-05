# Discord Thread Manager - Specification

## ADDED Requirements

### Requirement: Criar thread a partir de mensagem
O sistema SHALL permitir criar uma nova thread a partir de uma mensagem existente em um canal.

#### Scenario: Criar thread com sucesso
- **WHEN** `create_thread` é chamado com `channel_id`, `message_id` e `name` válidos
- **THEN** thread é criada e retorna `{ thread_id, thread_name, parent_channel_id, message_id }`

#### Scenario: Thread com nome customizado
- **WHEN** `create_thread` é chamado com `name` = "Discussão Trading"
- **THEN** thread é criada com nome "Discussão Trading"

#### Scenario: Auto-archive duration configurável
- **WHEN** `create_thread` é chamado com `auto_archive_duration` = 60
- **THEN** thread é criada com auto-archive de 1 hora

#### Scenario: Valores válidos para auto_archive_duration
- **WHEN** `create_thread` é chamado
- **THEN** apenas valores 60, 1440, 4320, 10080 são aceitos (1h, 24h, 3d, 7d)

#### Scenario: Canal não autorizado
- **WHEN** `create_thread` é chamado para canal não em `groups`
- **THEN** erro "channel not allowlisted" é retornado

#### Scenario: Mensagem não encontrada
- **WHEN** `create_thread` é chamado com `message_id` inexistente
- **THEN** erro "message not found" é retornado

---

### Requirement: Listar threads ativas
O sistema SHALL permitir listar threads ativas em um canal.

#### Scenario: Listar threads com sucesso
- **WHEN** `list_threads` é chamado com `channel_id` válido
- **THEN** retorna lista de threads com `{ thread_id, thread_name, message_count, created_at, archived }`

#### Scenario: Canal sem threads
- **WHEN** `list_threads` é chamado para canal sem threads ativas
- **THEN** retorna lista vazia `[]`

#### Scenario: Incluir threads arquivadas opcionalmente
- **WHEN** `list_threads` é chamado com `include_archived` = true
- **THEN** threads arquivadas são incluídas no resultado

---

### Requirement: Arquivar thread
O sistema SHALL permitir arquivar uma thread existente.

#### Scenario: Arquivar thread com sucesso
- **WHEN** `archive_thread` é chamado com `thread_id` válido
- **THEN** thread é arquivada e retorna `{ thread_id, archived: true }`

#### Scenario: Thread já arquivada
- **WHEN** `archive_thread` é chamado para thread já arquivada
- **THEN** retorna sucesso sem alteração

#### Scenario: Thread não encontrada
- **WHEN** `archive_thread` é chamado com `thread_id` inexistente
- **THEN** erro "thread not found" é retornado

#### Scenario: Thread em canal não autorizado
- **WHEN** `archive_thread` é chamado para thread em canal não em `groups`
- **THEN** erro "channel not allowlisted" é retornado

---

### Requirement: Validação de entrada com Pydantic
O sistema SHALL validar todas as entradas usando modelos Pydantic.

#### Scenario: Validação de create_thread
- **WHEN** `create_thread` recebe parâmetros
- **THEN** `CreateThreadInput` valida tipos e valores

#### Scenario: Erro de validação
- **WHEN** parâmetro inválido é passado (ex: `auto_archive_duration` = 30)
- **THEN** erro de validação Pydantic é retornado com detalhes

---

> "Threads organizam o caos" – made by Sky 🚀
