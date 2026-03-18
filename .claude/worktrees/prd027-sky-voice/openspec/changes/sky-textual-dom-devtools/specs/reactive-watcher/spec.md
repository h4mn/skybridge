# Spec: Reactive Watcher

Sistema automático de rastreamento de propriedades `reactive()` de widgets Textual, detectando mudanças e mantendo histórico.

## ADDED Requirements

### Requirement: Descoberta automática de props reactive

O sistema SHALL descobrir automaticamente todas as propriedades `reactive()` de um widget Textual registrado.

#### Scenario: Descobrir props ao registrar
- **WHEN** um widget com props reactive é registrado
- **THEN** o watcher identifica todos os atributos `reactive` via introspecção
- **AND** cada prop é adicionada ao `DOMNode.reactive_props`

#### Scenario: Props com tipos complexos
- **WHEN** um reactive prop contém `EstadoLLM` (dataclass)
- **THEN** o watcher serializa para `dict` mantendo todos os campos
- **AND** tipos primitivos (int, float, str, bool) são mantidos como estão

#### Scenario: Props reactive nulas ou undefined
- **WHEN** um reactive prop tem valor `None`
- **THEN** o watcher registra `None` no histórico
- **AND** nenhuma exceção é lançada

---

### Requirement: Detecção de mudanças via watch_*

O sistema SHALL interceptar mudanças em props reactive através dos métodos `watch_*` do widget.

#### Scenario: Mudança em prop simple
- **WHEN** `AnimatedVerb._offset` muda de `0.0` para `5.0`
- **THEN** o watcher captura o novo valor
- **AND** um registro é adicionado ao histórico com timestamp

#### Scenario: Mudança em prop complexa
- **WHEN** `AnimatedVerb._estado` muda para novo `EstadoLLM`
- **THEN** o watcher captura todos os campos do novo estado
- **AND** o diff com o estado anterior é calculado

#### Scenario: Mudanças rápidas consecutivas
- **WHEN** uma prop muda 3 vezes em menos de 100ms
- **THEN** as 3 mudanças são registradas individualmente
- **AND** cada uma tem seu próprio timestamp com precisão de ms

#### Scenario: Valor não muda (mesmo valor)
- **WHEN** uma prop é setada para o mesmo valor que já tinha
- **THEN** nenhuma entrada é adicionada ao histórico
- **AND** o watcher ignora a mudança redundante

---

### Requirement: Histórico de mudanças

O sistema SHALL manter um histórico limitado de mudanças para cada prop reactive.

#### Scenario: Histórico padrão de 50 entradas
- **WHEN** uma prop sofre mudanças
- **THEN** até 50 entradas são mantidas no histórico
- **AND** entradas mais antigas são descartadas (FIFO)

#### Scenario: Histórico configurável
- **WHEN** `SkyTextualDOM.configure(history_limit=100)` é chamado
- **THEN** todas as props passam a manter até 100 entradas

#### Scenario: Histórico vazio para props nunca mudadas
- **WHEN** uma prop nunca teve seu valor alterado
- **THEN** seu histórico é uma lista vazia `[]`

#### Scenario: Entrada de histórico contém metadata
- **WHEN** uma mudança é registrada
- **THEN** cada entrada contém:
  - `timestamp`: `datetime` com timezone
  - `old_value`: Valor anterior
  - `new_value`: Valor novo
  - `source`: Origem da mudança (user, system, timer)

---

### Requirement: Diff entre estados

O sistema SHALL calcular diff automático entre valores antigos e novos de props reactive.

#### Scenario: Diff de dict simples
- **WHEN** uma prop muda de `{"a": 1, "b": 2}` para `{"a": 1, "b": 3}`
- **THEN** o diff mostra `{"b": {"old": 2, "new": 3}}`
- **AND** campos não modificados não aparecem no diff

#### Scenario: Diff de dataclass
- **WHEN** `EstadoLLM` muda `certeza` de `0.8` para `0.95`
- **THEN** o diff mostra apenas o campo modificado
- **AND** estrutura é `{campo: {old: ..., new: ...}}`

#### Scenario: Diff de tipos incompatíveis
- **WHEN** uma prop muda de `int` para `str`
- **THEN** o diff mostra `{"old": 123, "new": "abc"}`
- **AND** nenhuma exceção é lançada

#### Scenario: Diff sem mudanças
- **WHEN** um objeto muda mas valores internos são idênticos
- **THEN** o diff retorna `{}` (vazio)

---

### Requirement: Tracing de props específicas

O sistema SHALL permitir habilitar tracing seletivo para props específicas, logando todas mudanças.

#### Scenario: Iniciar trace de prop
- **WHEN** `SkyTextualDOM.trace("AnimatedVerb_12345", "_offset")` é chamado
- **THEN** todas as mudanças futuras de `_offset` são logadas no ChatLog
- **AND** log mostra valor old → new com timestamp

#### Scenario: Trace de todas as props do widget
- **WHEN** `SkyTextualDOM.trace("AnimatedVerb_12345")` é chamado sem prop específica
- **THEN** todas as props reactive do widget são traceadas
- **AND** cada mudança é logada separadamente

#### Scenario: Parar trace
- **WHEN** `SkyTextualDOM.untrace("AnimatedVerb_12345")` é chamado
- **THEN** o tracing para esse widget é desabilitado
- **AND** nenhuma mudança adicional é logada

#### Scenario: Trace com filtro de valor
- **WHEN** `SkyTextualDOM.trace("AnimatedVerb_12345", "_offset", filter=lambda x: x > 10)` é chamado
- **THEN** apenas mudanças onde novo valor > 10 são logadas
- **AND** mudanças que não satisfazem o filtro são silenciosas

---

### Requirement: Streams de mudanças

O sistema SHALL permitir subscrição a streams de mudanças para props específicas.

#### Scenario: Subscrição a mudanças de prop
- **WHEN** um callback é registrado via `on_prop_change(dom_id, prop, callback)`
- **THEN** o callback é chamado a cada mudança da prop
- **AND** o callback recebe `(old_value, new_value, timestamp)`

#### Scenario: Múltiplos subscribers
- **WHEN** múltiplos callbacks são registrados para mesma prop
- **THEN** todos os callbacks são chamados em ordem de registro
- **AND** falha em um callback não afeta os outros

#### Scenario: Cancelar subscrição
- **WHEN** um subscriber é removido
- **THEN** o callback para de ser chamado
- **AND** outros subscribers continuam funcionando

---

### Requirement: Performance no rastreamento

O sistema SHALL ter overhead mínimo no rastreamento de props reactive.

#### Scenario: Overhead O(1) por mudança
- **WHEN** uma prop reactive muda
- **THEN** a operação de rastreamento é O(1)
- **AND** não depende do número de props ou histórico

#### Scenario: Sem rastreamento = zero overhead
- **WHEN** um widget é registrado com `watch=False`
- **THEN** nenhuma introspecção de reactive é feita
- **AND** nenhuma estrutura de histórico é alocada

#### Scenario: Garbage collection de histórico antigo
- **WHEN** o histórico atinge o limite configurado
- **THEN** entradas mais antigas são removidas automaticamente
- **AND** memória é liberada (sem memory leak)

---

### Requirement: Detecção de loops de mudança

O sistema SHALL detectar e alertar sobre loops rápidos de mudança na mesma prop.

#### Scenario: Loop detectado
- **WHEN** uma prop muda mais de 100 vezes em 1 segundo
- **THEN** um alerta é gerado no ChatLog
- **AND** o alerta identifica o widget e prop com loop
- **EXAMPLE**: `[LOOP DETECTED] AnimatedVerb._offset changed 150 times in 1s`

#### Scenario: Loop se configura
- **WHEN** o loop é configurado via `SkyTextualDOM.configure(loop_threshold=50, window_ms=500)`
- **THEN** loops são detectados com 50 mudanças em 500ms

#### Scenario: Loop alerta não bloqueia mudanças
- **WHEN** um loop é detectado
- **THEN** as mudanças continuam sendo registradas
- **AND** apenas um alerta visual é emitido

---

> "Observar sem interferir é a arte do debugging perfeito" – made by Sky 👁️
