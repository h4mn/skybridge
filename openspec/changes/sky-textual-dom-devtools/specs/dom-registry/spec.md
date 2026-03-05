# Spec: DOM Registry

Sistema de registro global para widgets Textual, permitindo navegação em árvore e queries estilo DOM.

## ADDED Requirements

### Requirement: Registro global de widgets

O sistema SHALL manter um registro centralizado de todos os widgets Textual registrados, permitindo acesso via identificador único.

#### Scenario: Registrar widget manualmente
- **WHEN** um widget é registrado via `SkyTextualDOM.register(widget)`
- **THEN** o widget recebe um `dom_id` único
- **AND** o widget é adicionado ao registro global
- **AND** uma referência `DOMNode` é criada encapsulando o widget

#### Scenario: Widget com dom_id customizado
- **WHEN** um widget é registrado com `dom_id` explícito
- **THEN** o `dom_id` fornecido é usado
- **AND** o registro usa esse identificador para consultas

#### Scenario: Identificador único automático
- **WHEN** um widget é registrado sem `dom_id`
- **THEN** o sistema gera automaticamente um `dom_id` no formato `<ClassName>_<uniqueId>`
- **EXAMPLE**: `AnimatedVerb_12345`

---

### Requirement: Árvore hierárquica parent-child

O sistema SHALL manter a relação hierárquica entre widgets, permitindo navegação de parent para children e vice-versa.

#### Scenario: Vincular parent-child
- **WHEN** um widget é registrado com `parent` especificado
- **THEN** o `DOMNode` do filho referencia o parent
- **AND** o `DOMNode` do parent inclui o filho em sua lista de children

#### Scenario: Navegar para cima (parent)
- **WHEN** consultado o `parent` de um `DOMNode`
- **THEN** o sistema retorna o `DOMNode` do parent ou `None` se for root

#### Scenario: Navegar para baixo (children)
- **WHEN** consultada a lista de `children` de um `DOMNode`
- **THEN** o sistema retorna todos os `DOMNode`s filhos em ordem de montagem

#### Scenario: Widget root sem parent
- **WHEN** um widget `Screen` é registrado sem parent
- **THEN** seu `parent` é `None`
- **AND** ele é considerado um nó root da árvore

---

### Requirement: Query por dom_id

O sistema SHALL permitir recuperar um `DOMNode` específico através de seu `dom_id`.

#### Scenario: Busca por ID existente
- **WHEN** `SkyTextualDOM.get("AnimatedVerb_12345")` é chamado
- **THEN** o `DOMNode` correspondente é retornado
- **AND** o `DOMNode` contém referência ao widget Textual original

#### Scenario: Busca por ID inexistente
- **WHEN** `SkyTextualDOM.get("Inexistente_999")` é chamado
- **THEN** o sistema retorna `None`
- **AND** nenhuma exceção é lançada

---

### Requirement: Query estilo CSS seletor

O sistema SHALL permitir buscar múltiplos `DOMNode`s usando seletores estilo CSS.

#### Scenario: Busca por classe
- **WHEN** `SkyTextualDOM.query("AnimatedVerb")` é chamado
- **THEN** todos os `DOMNode`s com `class_name == "AnimatedVerb"` são retornados

#### Scenario: Busca por padrão
- **WHEN** `SkyTextualDOM.query("Turn*")` é chamado
- **THEN** todos os `DOMNode`s cujo `class_name` inicia com "Turn" são retornados

#### Scenario: Busca por estado
- **WHEN** `SkyTextualDOM.query("[estado=DONE]")` é chamado
- **THEN** todos os `DOMNode`s com `state['estado'] == 'DONE'` são retornados

#### Scenario: Busca composta
- **WHEN** `SkyTextualDOM.query("AnimatedVerb[emocao=debugando]")` é chamado
- **THEN** apenas `AnimatedVerb` com `state['emocao'] == 'debugando'` são retornados

#### Scenario: Query vazia retorna lista vazia
- **WHEN** `SkyTextualDOM.query("Inexistente*")` é chamado
- **THEN** uma lista vazia `[]` é retornada
- **AND** nenhuma exceção é lançada

---

### Requirement: Serialização de estado

O `DOMNode` SHALL manter uma representação serializável do estado do widget, permitindo inspeção sem acessar o widget diretamente.

#### Scenario: Estado básico capturado
- **WHEN** um widget é registrado
- **THEN** `DOMNode.state` contém:
  - `class_name`: Nome da classe do widget
  - `dom_id`: Identificador único
  - `is_visible`: Se o widget está visível
- **AND** `DOMNode.reactive_props` contém todas props `reactive()` atuais

#### Scenario: Estado com reactive props
- **WHEN** um `AnimatedVerb` com `_offset=5.0`, `_pulso=1.5` é registrado
- **THEN** `DOMNode.reactive_props['_offset'] == 5.0`
- **AND** `DOMNode.reactive_props['_pulso'] == 1.5`

#### Scenario: Estado com dados customizados
- **WHEN** um widget tem atributos customizados (ex: `EstadoLLM`)
- **THEN** `DOMNode.state` contém representação serializável desses dados
- **AND** dataclasses são convertidas para `dict`

---

### Requirement: Impressão da árvore completa

O sistema SHALL gerar uma representação visual da árvore completa de widgets registrados.

#### Scenario: Imprimir árvore formatada
- **WHEN** `SkyTextualDOM.tree()` é chamado
- **THEN** uma string formatada com indentação é retornada
- **AND** cada nível de hierarquia é representado com `├─` e `└─`
- **AND** widgets pais aparecem antes dos filhos

#### Scenario: Árvore mostra informações resumidas
- **WHEN** a árvore é impressa
- **THEN** cada nó mostra:
  - `class_name` do widget
  - `dom_id` entre colchetes
  - Primeiras informações de estado relevantes (ex: verbo para `AnimatedVerb`)

#### Scenario: Árvore com múltiplos root nodes
- **WHEN** múltiplas `Screen` estão registradas
- **THEN** a árvore mostra cada root node separadamente
- **AND** a hierarquia de cada uma é preservada

---

### Requirement: Auto-registro via mixin

O sistema SHALL fornecer um mixin `SkyWidgetMixin` que permite auto-registro de widgets ao montar.

#### Scenario: Widget com mixin se registra automaticamente
- **WHEN** um widget com `SkyWidgetMixin` é montado (`on_mount`)
- **THEN** o widget chama `SkyTextualDOM.register(self)` automaticamente
- **AND** o `parent` é detectado via `self.parent`

#### Scenario: Auto-registro detecta parent
- **WHEN** um widget filho com mixin é montado dentro de um parent também registrado
- **THEN** o `DOMNode` do filho referencia o parent correto
- **AND** o parent tem o filho em sua lista de children

#### Scenario: Mixin é opcional
- **WHEN** um widget sem mixin é criado
- **THEN** o widget funciona normalmente
- **AND** pode ser registrado manualmente se desejado

---

### Requirement: Desregistro de widgets

O sistema SHALL permitir remover widgets do registro quando são destruídos.

#### Scenario: Desregistro manual
- **WHEN** `SkyTextualDOM.unregister(dom_id)` é chamado
- **THEN** o `DOMNode` é removido do registro global
- **AND** o parent remove o nó de sua lista de children

#### Scenario: Auto-desregistro via mixin
- **WHEN** um widget com `SkyWidgetMixin` é desmontado (`on_unmount`)
- **THEN** o mixin chama `SkyTextualDOM.unregister(self._dom_id)` automaticamente

#### Scenario: Desregistro de parent remove children
- **QUANDO** um parent é desregistrado
- **THEN** todos os `DOMNode`s filhos são também desregistrados
- **AND** a árvore abaixo do parent é completamente removida

---

### Requirement: Thread-safety no registro

O sistema SHALL garantir operações thread-safe no registro global.

#### Scenario: Registro concorrente
- **WHEN** múltiplos widgets tentam registrar simultaneamente
- **THEN** todos os registros são bem-sucedidos
- **AND** nenhum `dom_id` é duplicado
- **AND** nenhuma condição de corrida ocorre

#### Scenario: Query durante registro
- **WHEN** uma query é executada enquanto widgets são registrados
- **THEN** a query retorna um estado consistente
- **AND** widgets parcialmente registrados não aparecem em resultados

---

> "A estrutura clara é a base da inspeção eficaz" – made by Sky 🏗️
