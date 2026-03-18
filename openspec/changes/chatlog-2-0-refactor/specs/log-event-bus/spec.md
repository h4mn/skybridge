# Log Event Bus

Sistema pub/sub central para distribuição de eventos de log.

## ADDED Requirements

### Requirement: Event Bus distribui LogEntry para inscritos

O sistema SHALL fornecer um `LogEventBus` que permite publicar eventos de log para múltiplos consumidores inscritos.

#### Scenario: Publicar evento distribui para todos os inscritos

- **GIVEN** um `LogEventBus` com 3 consumidores inscritos
- **WHEN** um `LogEntry` é publicado no bus
- **THEN** todos os 3 consumidores recebem o evento na ordem de inscrição

#### Scenario: Inscrição após publicação não recebe eventos passados

- **GIVEN** um `LogEventBus` onde um evento já foi publicado
- **WHEN** um novo consumidor se inscreve
- **THEN** o consumidor NÃO recebe o evento publicado anteriormente
- **AND** apenas recebe eventos publicados após sua inscrição

---

### Requirement: LogEntry contém nível, mensagem e timestamp

O sistema SHALL fornecer um `LogEntry` imutável com nível, mensagem e timestamp.

#### Scenario: Criar LogEntry com dados válidos

- **GIVEN** nível `LogLevel.INFO`, mensagem `"Sistema iniciado"` e timestamp atual
- **WHEN** um `LogEntry` é criado
- **THEN** o `LogEntry` contém os valores fornecidos
- **AND** os atributos são somente leitura

#### Scenario: LogEntry representa diferentes níveis

- **GIVEN** os níveis `DEBUG`, `INFO`, `WARNING`, `ERROR`, `EVENT`
- **WHEN** `LogEntry` é criado com cada nível
- **THEN** todos os níveis são válidos e representados corretamente

---

### Requirement: Consumidores podem cancelar inscrição

O sistema SHALL permitir que consumidores cancelem sua inscrição no Event Bus.

#### Scenario: Cancelar inscrição para de receber eventos

- **GIVEN** um consumidor inscrito no `LogEventBus`
- **WHEN** o consumidor cancela a inscrição
- **THEN** o consumidor para de receber novos eventos
- **AND** outros consumidores continuam recebendo normalmente

#### Scenario: Cancelar inscrição inexistente não lança erro

- **GIVEN** um `LogEventBus`
- **WHEN** uma inscrição inexistente é cancelada
- **THEN** nenhuma exceção é lançada
- **AND** o operation é um no-op

---

### Requirement: Event Bus é thread-safe

O sistema SHALL garantir que o `LogEventBus` pode ser usado de múltiplas threads simultaneamente.

#### Scenario: Publicar de múltiplas threads não causa race condition

- **GIVEN** um `LogEventBus` com 2 consumidores
- **WHEN** 5 threads publicam 100 eventos cada simultaneamente
- **THEN** todos os eventos são entregues aos consumidores
- **AND** nenhum evento é perdido ou duplicado

---

### Requirement: LogLevel define hierarquia de severidade

O sistema SHALL fornecer `LogLevel` com hierarquia: `DEBUG < INFO < WARNING < ERROR`.

#### Scenario: Comparar níveis retorna ordem correta

- **GIVEN** os níveis `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **WHEN** comparado usando operadores de comparação
- **THEN** `DEBUG < INFO < WARNING < ERROR`
- **AND** `ERROR > WARNING > INFO > DEBUG`

#### Scenario: Filtro por nível inclui níveis superiores

- **GIVEN** filtro configurado para `WARNING`
- **WHEN** um `LogEntry` com nível `ERROR` é avaliado
- **THEN** o entry passa o filtro (ERROR >= WARNING)

---

### Requirement: Event suporta metadados opcionais

O sistema SHALL permitir metadados adicionais no `LogEntry`.

#### Scenario: LogEntry com metadados contém dados extras

- **GIVEN** um `LogEntry` criado com metadados `{"user_id": 123, "request_id": "abc"}`
- **WHEN** os metadados são acessados
- **THEN** os valores originais são retornados
- **AND** os metadados são imutáveis

---

### Requirement: Event Bus fornece estatísticas de publicação

O sistema SHALL rastrear e fornecer estatísticas sobre eventos publicados.

#### Scenario: Estatísticas refletem eventos publicados

- **GIVEN** um `LogEventBus` onde 50 eventos foram publicados
- **WHEN** as estatísticas são consultadas
- **THEN** o contador de eventos publicados é 50
- **AND** o número de inscritos ativos é reportado
