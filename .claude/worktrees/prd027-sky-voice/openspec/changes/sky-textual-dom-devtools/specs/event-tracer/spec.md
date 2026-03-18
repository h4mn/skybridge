# Spec: Event Tracer

Log de eventos Textual com metadados (timestamp, widget, tipo, dados) e filtros avançados.

## ADDED Requirements

### Requirement: Captura automática de eventos Textual

O sistema SHALL capturar automaticamente todos os eventos Textual disparados na aplicação.

#### Scenario: Capturar eventos de mount/unmount
- **WHEN** um widget é montado (`on_mount`)
- **THEN** um evento `MOUNT` é registrado com:
  - `timestamp`
  - `widget_dom_id`
  - `widget_class`
  - `parent_dom_id` (se existir)

#### Scenario: Capturar eventos de interação
- **WHEN** um evento de interação ocorre (click, submit, key press)
- **THEN** um evento `INTERACTION` é registrado com:
  - `event_type` (ex: "click", "submit")
  - `target_dom_id`
  - `event_data` (dados relevantes do evento)

#### Scenario: Capturar eventos customizados
- **WHEN** um evento customizado é postado (`post_message(MyEvent)`)
- **THEN** o tracer captura o evento com:
  - `event_class_name`
  - `sender_dom_id`
  - `event_attrs` (atributos do evento)

---

### Requirement: Eventos de mudança de estado

O sistema SHALL registrar mudanças de estado reactive como eventos especiais.

#### Scenario: Prop changed event
- **WHEN** uma prop reactive muda de valor
- **THEN** um evento `PROP_CHANGED` é registrado com:
  - `widget_dom_id`
  - `prop_name`
  - `old_value`
  - `new_value`
  - `diff` (se aplicável)

#### Scenario: State snapshot event
- **WHEN** um snapshot de estado é capturado
- **THEN** um evento `SNAPSHOT` é registrado com:
  - `snapshot_name`
  - `snapshot_id`

#### Scenario: Error event
- **WHEN** um erro é capturado em qualquer widget
- **THEN** um evento `ERROR` é registrado com:
  - `widget_dom_id`
  - `error_type`
  - `error_message`
  - `stack_trace` (se disponível)

---

### Requirement: Buffer circular de eventos

O tracer SHALL manter um buffer circular de eventos com tamanho configurável.

#### Scenario: Buffer padrão de 1000 eventos
- **WHEN** o tracer é inicializado
- **THEN** mantém até 1000 eventos em memória
- **AND** eventos mais antigos são descartados quando o limite é atingido

#### Scenario: Buffer configurável
- **WHEN** `SkyTextualDOM.configure(event_buffer_size=5000)` é chamado
- **THEN** o buffer passa a manter 5000 eventos

#### Scenario: Buffer não perde eventos críticos
- **WHEN** o buffer está cheio
- **THEN** eventos `ERROR` e `CRITICAL` nunca são descartados
- **AND** são movidos para um buffer separado de "eventos permanentes"

---

### Requirement: Filtros de eventos

O sistema SHALL permitir filtrar eventos por múltiplos critérios.

#### Scenario: Filtrar por tipo de evento
- **WHEN** `tracer.filter(event_types=["MOUNT", "UNMOUNT"])` é chamado
- **THEN** apenas eventos mount/unmount são retornados
- **AND** outros tipos são ocultados

#### Scenario: Filtrar por widget
- **WHEN** `tracer.filter(widget_dom_id="AnimatedVerb_123")` é chamado
- **THEN** apenas eventos desse widget são retornados

#### Scenario: Filtrar por intervalo de tempo
- **WHEN** `tracer.filter(since=datetime(...), until=datetime(...))` é chamado
- **THEN** apenas eventos no intervalo são retornados

#### Scenario: Filtros compostos
- **WHEN** múltiplos filtros são combinados
- **THEN** apenas eventos que satisfazem TODOS os critérios são retornados
- **EXAMPLE**: `filter(event_types=["CLICK"], widget_dom_id="...")`

---

### Requirement: Busca textual em eventos

O sistema SHALL permitir buscar eventos por conteúdo textual.

#### Scenario: Busca em todas as propriedades
- **WHEN** `tracer.search("codando")` é chamado
- **THEN** todos os eventos contendo "codando" em qualquer propriedade são retornados
- **AND** a busca é case-insensitive

#### Scenario: Busca em propriedade específica
- **WHEN** `tracer.search("erro", prop="error_message")` é chamado
- **THEN** apenas eventos com "erro" em `error_message` são retornados

#### Scenario: Busca com regex
- **WHEN** `tracer.search(regex=r"AnimatedVerb.*erro")` é chamado
- **THEN** eventos matching o regex são retornados
- **AND** a busca usa sintaxe regex Python completa

---

### Requirement: Exportação de eventos

O sistema SHALL permitir exportar eventos para análise externa.

#### Scenario: Exportar como JSON
- **WHEN** `tracer.export(fmt="json")` é chamado
- **THEN** retorna array JSON de eventos
- **AND** cada evento é um objeto com todas as propriedades

#### Scenario: Exportar como CSV
- **WHEN** `tracer.export(fmt="csv")` é chamado
- **THEN** retorna string CSV com cabeçalho
- **AND** colunas são as propriedades comuns dos eventos

#### Scenario: Exportar filtrado
- **WHEN** `tracer.export(fmt="json", filters=...)` é chamado
- **THEN** apenas eventos matching os filtros são exportados

---

### Requirement: Stream de eventos em tempo real

O sistema SHALL permitir subscrição a um stream de eventos em tempo real.

#### Scenario: Subscrever a todos os eventos
- **WHEN** `tracer.subscribe(callback)` é chamado
- **THEN** o callback é chamado para cada novo evento
- **AND** recebe o evento completo como argumento

#### Scenario: Subscreber com filtro
- **WHEN** `tracer.subscribe(callback, filter=event_types=["ERROR"])` é chamado
- **THEN** o callback é chamado apenas para eventos ERROR

#### Scenario: Unsubscribe
- **WHEN** `unsubscribe(subscription_id)` é chamado
- **THEN** o callback para de receber eventos
- **AND** o subscription_id não é mais válido

#### Scenario: Múltiplos subscribers
- **WHEN** 5 callbacks estão inscritos
- **THEN** todos os 5 são chamados para cada evento matching
- **AND** falha em um callback não afeta os outros

---

### Requirement: Timeline visual de eventos

A DevTools UI SHALL exibir eventos em uma timeline visual navegável.

#### Scenario: Timeline horizontal
- **WHEN** o painel Events é exibido
- **THEN** eventos são mostrados em timeline horizontal
- **AND** distância entre eventos representa tempo decorrido

#### Scenario: Timeline com zoom
- **WHEN** o usuário usa scroll no painel Events
- **THEN** a timeline dá zoom (mais/menos detalhe visível)
- **AND** eventos são agregados/desagregados conforme zoom

#### Scenario: Clique em evento mostra detalhes
- **WHEN** um evento é clicado na timeline
- **THEN** um modal com detalhes completos é exibido
- **AND** todas as propriedades do evento são mostradas formatadas

---

### Requirement: Performance de tracing

O tracer SHALL ter overhead mínimo e não afetar performance da aplicação.

#### Scenario: Overhead O(1) por evento
- **WHEN** um evento é capturado
- **THEN** a operação é O(1)
- **AND** não depende do número de eventos no buffer

#### Scenario: Tracing assíncrono
- **WHEN** um evento é capturado
- **THEN** a escrita no buffer é assíncrona
- **AND** não bloqueia o thread principal da UI

#### Scenario: Desabilitar tracing dinamicamente
- **WHEN** `tracer.disable()` é chamado
- **THEN** nenhum evento é mais capturado
- **AND** overhead de tracing é zero
- **WHEN** `tracer.enable()` é chamado
- **THEN** a captura de eventos é retomada

---

### Requirement: Alertas baseados em eventos

O sistema SHALL detectar padrões de eventos e emitir alertas automaticamente.

#### Scenario: Muitos erros em curto período
- **WHEN** 5+ eventos ERROR ocorrem em 10 segundos
- **THEN** um alerta `ERROR_BURST` é emitido
- **AND** o alerta mostra contagem de erros e timeframe

#### Scenario: Evento nunca visto antes
- **WHEN** um tipo de evento customizado aparece pela primeira vez
- **THEN** um alerta informativo `NEW_EVENT_TYPE` é emitido
- **AND** o tipo é registrado como "conhecido" para o futuro

#### Scenario: Widget disparando eventos excessivamente
- **WHEN** um widget dispara 100+ eventos em 1 segundo
- **THEN** um alerta `EVENT_SPAM` é emitido
- **AND** o widget culpado é identificado no alerta

---

> "Eventos são a pulsação da aplicação — ouça-os atentamente" – made by Sky 💓
