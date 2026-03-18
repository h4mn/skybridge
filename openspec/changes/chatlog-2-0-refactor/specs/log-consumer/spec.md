# Log Consumer

Interface para consumidores de log via Protocol simples.

## ADDED Requirements

### Requirement: LogConsumer define interface padrão

O sistema SHALL fornecer um Protocol `LogConsumer` que define a interface para todos os consumidores de log.

#### Scenario: Qualquer classe com write_log é um consumidor válido

- **GIVEN** uma classe com método `write_log(level, message, timestamp, scope, context)`
- **WHEN** a classe é usada como `LogConsumer`
- **THEN** o type-checker aceita a classe como válida
- **AND** nenhuma exceção de tipo é lançada

#### Scenario: LogConsumer pode ser mockado para testes

- **GIVEN** um mock de `LogConsumer`
- **WHEN** o mock é passado para código que espera um consumidor
- **THEN** o código funciona normalmente
- **AND** as chamadas podem ser assertivas no teste

---

### Requirement: LogEntry usa logging padrão do Python

O sistema SHALL usar níveis do módulo `logging` do Python, não enum custom.

#### Scenario: Níveis correspondem ao logging padrão

- **GIVEN** os níveis disponíveis
- **THEN** `logging.DEBUG` (10), `logging.INFO` (20), `logging.WARNING` (30), `logging.ERROR` (40), `logging.CRITICAL` (50)

#### Scenario: LogEntry com nível logging.INFO é válido

- **GIVEN** nível `logging.INFO`, mensagem `"Sistema iniciado"`, timestamp atual
- **WHEN** um `LogEntry` é criado
- **THEN** o `LogEntry` contém os valores fornecidos
- **AND** os atributos são somente leitura (frozen dataclass)

#### Scenario: Níveis são comparáveis por hierarquia

- **GIVEN** os níveis `logging.DEBUG`, `logging.INFO`, `logging.WARNING`, `logging.ERROR`
- **THEN** `logging.DEBUG < logging.INFO < logging.WARNING < logging.ERROR`
- **AND** `logging.ERROR > logging.WARNING > logging.INFO > logging.DEBUG`

---

### Requirement: LogEntry inclui escopo (scope)

O sistema SHALL incluir campo `scope` em `LogEntry` para categorização.

#### Scenario: LogEntry com scope LogScope.API

- **GIVEN** um `LogEntry` com `scope=LogScope.API`
- **WHEN** o entry é criado
- **THEN** o scope é armazenado corretamente
- **AND** pode ser usado para filtragem

#### Scenario: Escopos disponíveis são bem definidos

- **GIVEN** o enum `LogScope`
- **THEN** os escopos são: `ALL`, `SYSTEM`, `USER`, `API`, `DATABASE`, `NETWORK`, `VOICE`, `MEMORY`

---

### Requirement: LogEntry suporta contexto opcional

O sistema SHALL permitir campo `context` com metadados adicionais.

#### Scenario: LogEntry com contexto contém dados extras

- **GIVEN** um `LogEntry` criado com `context={"user_id": 123, "request_id": "abc"}`
- **WHEN** o contexto é acessado
- **THEN** os valores originais são retornados
- **AND** o contexto é imutável (frozen dataclass)

---

### Requirement: FileLogConsumer escreve em arquivo

O sistema SHALL fornecer um `FileLogConsumer` que escreve logs em arquivo.

#### Scenario: Escrever log em arquivo cria entrada formatada

- **GIVEN** um `FileLogConsumer` configurado com arquivo `/tmp/test.log`
- **WHEN** `write_log(logging.INFO, "Test message", ...)` é chamado
- **THEN** o arquivo contém uma linha com timestamp, nível e mensagem
- **AND** o formato é `[YYYY-MM-DD HH:MM:SS] [INFO] Test message`

---

### Requirement: Consumer implementa write_log de forma síncrona

O sistema SHALL definir `write_log` como método síncrono.

#### Scenario: write_log retorna imediatamente

- **GIVEN** um `LogConsumer` implementado
- **WHEN** `write_log(...)` é chamado
- **THEN** o método retorna sem bloquear
- **AND** qualquer operação assíncrona é interna ao consumidor

---

### Requirement: LogEntry fornece método de matching por filtro

O sistema SHALL fornecer método em `LogEntry` para verificar se passa por filtro.

#### Scenario: matches_filter retorna True quando nível e scope combinam

- **GIVEN** um `LogEntry` com `level=logging.ERROR` e `scope=LogScope.API`
- **WHEN** `entry.matches_filter(level_min=logging.WARNING, scope=LogScope.ALL)` é chamado
- **THEN** retorna `True` (ERROR >= WARNING)

#### Scenario: matches_filter retorna False quando scope não bate

- **GIVEN** um `LogEntry` com `scope=LogScope.VOICE`
- **WHEN** `entry.matches_filter(level_min=logging.INFO, scope=LogScope.API)` é chamado
- **THEN** retorna `False` (scope diferente)
