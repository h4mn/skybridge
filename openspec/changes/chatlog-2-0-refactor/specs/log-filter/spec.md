# Log Filter

Filtro combinado: nível (logging padrão) + escopo (categoria).

## ADDED Requirements

### Requirement: LogFilter fornece filtro por nível e escopo

O sistema SHALL fornecer um widget `LogFilter` com dois eixos de filtro: nível e escopo.

#### Scenario: Filtro padrão é ALL em ambos eixos

- **GIVEN** um `LogFilter` recém-criado
- **WHEN** o widget é renderizado
- **THEN** nível `ALL` está selecionado
- **AND** escopo `ALL` está selecionado
- **AND** nenhum filtro é aplicado

---

### Requirement: Filtro por nível usa logging padrão do Python

O sistema SHALL usar níveis do módulo `logging`, não enum custom.

#### Scenario: Níveis disponíveis são padrão logging

- **GIVEN** os botões de nível
- **THEN** os níveis são: `ALL`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **AND** correspondem a `logging.DEBUG`, `logging.INFO`, etc.

#### Scenario: Filtrar por ERROR mostra ERROR e CRITICAL

- **GIVEN** um `ChatLog` com mensagens DEBUG, INFO, WARNING, ERROR, CRITICAL
- **WHEN** o filtro nível é configurado para `ERROR`
- **THEN** mensagens ERROR e CRITICAL são visíveis
- **AND** mensagens WARNING, INFO, DEBUG ficam ocultas

---

### Requirement: Filtro por escopo categoriza logs por tipo

O sistema SHALL fornecer filtro por escopo: ALL, SYSTEM, USER, API, DATABASE, NETWORK, VOICE, MEMORY.

#### Scenario: Escopos disponíveis são bem definidos

- **GIVEN** o enum `LogScope`
- **THEN** os escopos são: `ALL`, `SYSTEM`, `USER`, `API`, `DATABASE`, `NETWORK`, `VOICE`, `MEMORY`

#### Scenario: Filtrar por VOICE mostra apenas logs de voz

- **GIVEN** um `ChatLog` com logs de vários escopos
- **WHEN** o filtro escopo é configurado para `VOICE`
- **THEN** apenas logs com `scope=LogScope.VOICE` são visíveis
- **AND** logs de outros escopos ficam ocultos

---

### Requirement: Filtros são aplicados em conjunto (AND lógico)

O sistema SHALL aplicar ambos os filtros simultaneamente.

#### Scenario: Filtro ERROR + VOICE mostra apenas errors de voz

- **GIVEN** um `ChatLog` com logs de vários níveis e escopos
- **WHEN** nível é `ERROR` e escopo é `VOICE`
- **THEN** apenas logs que são AMBOS ERROR E VOICE são visíveis
- **AND** logs WARNING de voz ficam ocultos (nível não bate)
- **AND** logs ERROR de API ficam ocultos (escopo não bate)

---

### Requirement: LogFilter emite mensagem quando filtros mudam

O sistema SHALL fazer `LogFilter` emitir `FilterChanged` quando qualquer seleção muda.

#### Scenario: Mudar nível emite evento com nível novo

- **GIVEN** um `LogFilter` com nível `ALL`
- **WHEN** o usuário clica em `ERROR`
- **THEN** uma mensagem `FilterChanged` é emitida
- **AND** o nível no evento é `logging.ERROR`
- **AND** o escopo permanece inalterado

#### Scenario: Mudar escopo emite evento com escopo novo

- **GIVEN** um `LogFilter` com escopo `ALL`
- **WHEN** o usuário clica em `VOICE`
- **THEN** uma mensagem `FilterChanged` é emitida
- **AND** o escopo no evento é `LogScope.VOICE`
- **AND** o nível permanece inalterado

---

### Requirement: Hierarquia de níveis é respeitada

O sistema SHALL aplicar filtro usando hierarquia do logging: `DEBUG < INFO < WARNING < ERROR < CRITICAL`.

#### Scenario: Filtrar por INFO inclui níveis superiores

- **GIVEN** um filtro configurado para `INFO`
- **WHEN** mensagens de todos os níveis são avaliadas
- **THEN** INFO, WARNING, ERROR e CRITICAL passam
- **AND** DEBUG fica oculto

---

### Requirement: LogFilter exibe contador de mensagens filtradas

O sistema SHALL exibir contador de quantas mensagens passam pelos filtros atuais.

#### Scenario: Contador atualiza quando filtros mudam

- **GIVEN** um `ChatLog` com 100 mensagens totais
- **WHEN** os filtros são mudados para mostrar 10 mensagens
- **THEN** o contador mostra "10/100"
- **AND** o formato é "visíveis/total"

#### Scenario: Contador considera ambos os filtros

- **GIVEN** um `ChatLog` com 100 mensagens
- **AND** 20 mensagens são ERROR, 5 são VOICE
- **WHEN** filtros são ERROR + VOICE
- **THEN** se houver 2 mensagens que são AMBAS ERROR e VOICE
- **AND** o contador mostra "2/100"

---

### Requirement: Filtros podem ser definidos programaticamente

O sistema SHALL permitir que os filtros sejam definidos via código.

#### Scenario: Definir nível via método

- **GIVEN** um `LogFilter`
- **WHEN** `set_level(logging.WARNING)` é chamado
- **THEN** o botão WARNING fica selecionado
- **AND** `FilterChanged` é emitido
- **AND** o UI atualiza

#### Scenario: Definir escopo via método

- **GIVEN** um `LogFilter`
- **WHEN** `set_scope(LogScope.API)` é chamado
- **THEN** o botão API fica selecionado
- **AND** `FilterChanged` é emitido
- **AND** o UI atualiza

---

### Requirement: Filtros podem ser limpos (reset para ALL)

O sistema SHALL permitir limpar ambos os filtros.

#### Scenario: Limpar filtros mostra todas as mensagens

- **GIVEN** um `LogFilter` com nível `ERROR` e escopo `VOICE`
- **WHEN** `clear_filters()` é chamado
- **THEN** ambos os filtros são resetados para `ALL`
- **AND** todas as mensagens ficam visíveis
- **AND** `FilterChanged` é emitido
