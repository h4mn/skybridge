# Spec: ChatLog Overlay

## ADDED Requirements

### Requirement: ChatLog deve usar position absolute para verdadeiro overlay

O sistema SHALL configurar o widget `ChatLog` com `position: absolute; bottom: 0; left: 0; right: 0; z-index: 10` para remover o widget do fluxo normal do layout, garantindo que a abertura/fechamento não empurre outros widgets.

#### Scenario: ChatLog inicia fechado e fora do fluxo
- **WHEN** `ChatScreen` é montado
- **THEN** `ChatLog` tem `display: none`
- **AND** `ChatLog` tem `position: absolute`
- **AND** outros widgets (ChatScroll, ChatTextArea) ocupam todo o espaço disponível

#### Scenario: Toggle para visível NÃO empurra widgets
- **GIVEN** `ChatLog` está fechado (`display: none`)
- **WHEN** `log.toggle_class("visible")` é chamado
- **THEN** `ChatLog` fica com `display: block`
- **AND** `ChatLog` é exibido sobreposto (overlay) na parte inferior
- **AND** `ChatScroll` mantém sua altura e posição
- **AND** `ChatTextArea` mantém sua altura e posição

#### Scenario: Toggle para fechado remove overlay
- **GIVEN** `ChatLog` está visível
- **WHEN** `log.toggle_class("visible")` é chamado novamente
- **THEN** `ChatLog` volta para `display: none`
- **AND** overlay é removido
- **AND** layout permanece inalterado

### Requirement: ChatLog deve ter z-index suficiente para ficar por cima de outros widgets

O sistema SHALL configurar `z-index: 10` no `ChatLog` para garantir que o widget fique por cima de todos os outros widgets da `ChatScreen` quando visível.

#### Scenario: ChatLog visível cobre área inferior da tela
- **GIVEN** `ChatLog` está visível
- **WHEN** usuário visualiza a tela
- **THEN** `ChatLog` é exibido sobreposto na parte inferior
- **AND** conteúdo abaixo do `ChatLog` não é visível (coberto pelo overlay)
- **AND** `ChatLog` tem `z-index` maior que outros widgets

### Requirement: ChatLog deve usar cores visíveis e contrastantes

O sistema SHALL usar cores Textual mais fortes (`cyan` para info, `bold red` para erro, `green` para evento, `yellow` para debug) para garantir visibilidade em temas escuros.

#### Scenario: Mensagem de info é exibida em ciano visível
- **WHEN** `log.info("Mensagem informativa")` é chamado
- **THEN** `[INFO] Mensagem informativa` é exibido em cor ciano
- **AND** o texto é claramente visível em temas escuros

#### Scenario: Mensagem de erro é exibida em vermelho bold
- **WHEN** `log.error("Erro crítico")` é chamado
- **THEN** `[ERROR] Erro crítico` é exibido em vermelho bold
- **AND** o erro se destaca visualmente

#### Scenario: Mensagem de evento é exibida em verde
- **WHEN** `log.evento("RAG", "Busca completada")` é chamado
- **THEN** `[EVENTO] RAG Busca completada` é exibido em verde
- **AND** o evento é claramente distinguível de outros tipos de mensagem

#### Scenario: Mensagem de debug é exibida em amarelo
- **WHEN** `log.debug("Depuração")` é chamado
- **THEN** `[DEBUG] Depuração` é exibido em amarelo
- **AND** a mensagem de debug é distinguível

### Requirement: ChatLog deve ter borda superior destacada

O sistema SHALL configurar `border-top: thick $primary` para criar uma borda superior destacada, facilitando a identificação visual do painel de log.

#### Scenario: Borda superior é visível quando log está aberto
- **GIVEN** `ChatLog` está visível
- **WHEN** usuário visualiza a tela
- **THEN** borda superior em cor `$primary` é claramente visível
- **AND** borda tem espessura `thick`

### Requirement: ChatLog deve ter altura fixa de 20 linhas

O sistema SHALL configurar `height: 20` no `ChatLog` para garantir que o painel tenha altura fixa e previsível.

#### Scenario: ChatLog tem altura fixa
- **GIVEN** `ChatLog` está visível
- **WHEN** usuário visualiza a tela
- **THEN** `ChatLog` ocupa exatamente 20 linhas de altura
- **AND** conteúdo dentro do `ChatLog` pode ser rolado (scroll)

### Requirement: ChatLog deve preservar sistema de fila anti-flicker

O sistema SHALL preservar o sistema de fila (`_pending`, `_flush_scheduled`) e flush em batch (`call_after_refresh`) para evitar flicker durante streaming de logs.

#### Scenario: Múltiplas mensagens são enfileiradas
- **WHEN** `log.write()` é chamado múltiplas vezes em sequência rápida
- **THEN** mensagens são adicionadas à fila `_pending`
- **AND** `_flush_scheduled` é definido como `True`
- **AND** flush é agendado para o próximo tick da UI

#### Scenario: Flush em batch monta todos os widgets de uma vez
- **WHEN** `_flush()` é executado
- **THEN** todas as mensagens pendentes são montadas em uma única operação
- **AND** um único `mount(*[Static(...)])` é executado
- **AND** apenas um reflow do DOM ocorre

### Requirement: ChatLog deve usar markup Textual para cores

O sistema SHALL passar `markup=True` ao criar widgets `Static` para processar markup de cores Textual (`[cyan]`, `[bold red]`, `[green]`, `[yellow]`).

#### Scenario: Markup é processado corretamente
- **WHEN** `Static("[cyan]Texto[/cyan]", markup=True)` é criado
- **THEN** texto é exibido em ciano
- **AND** markup Textual é processado
