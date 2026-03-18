# Spec: DevTools UI

Interface de inspeção visual com 3 painéis (Tree, State, Events) acessível via atalho Ctrl+D.

## ADDED Requirements

### Requirement: Tela DevTools acessível via atalho

O sistema SHALL fornecer uma `DevToolsScreen` acessível através do atalho `Ctrl+D` em qualquer ponto da aplicação.

#### Scenario: Abrir DevTools via Ctrl+D
- **WHEN** o usuário pressiona `Ctrl+D`
- **THEN** a `DevToolsScreen` é empilhada (`push_screen`)
- **AND** a aplicação principal continua rodando em background

#### Scenario: Fechar DevTools via Escape
- **WHEN** o usuário pressiona `Escape` na DevToolsScreen
- **THEN** a DevToolsScreen é desempilhada (`pop_screen`)
- **AND** a aplicação principal volta ao foco

#### Scenario: DevTools não pausa a aplicação
- **WHEN** a DevToolsScreen está aberta
- **THEN** a TUI principal continua processando eventos
- **AND** timers, animações e workers continuam rodando

---

### Requirement: Layout de 3 painéis

A DevToolsScreen SHALL ter 3 painéis principais: Tree, State e Events.

#### Scenario: Painel Tree à esquerda
- **WHEN** a DevToolsScreen é montada
- **THEN** o painel Tree ocupa 1/3 da largura
- **AND** mostra a hierarquia de widgets registrados

#### Scenario: Painel State à direita (superior)
- **WHEN** a DevToolsScreen é montada
- **THEN** o painel State ocupa 2/3 da largura, metade da altura
- **AND** mostra estado detalhado do widget selecionado

#### Scenario: Painel Events à direita (inferior)
- **WHEN** a DevToolsScreen é montada
- **THEN** o painel Events ocupa 2/3 da largura, metade da altura
- **AND** mostra timeline de eventos recentes

#### Scenario: Painéis são redimensionáveis
- **WHEN** o usuário arrasta a borda entre painéis
- **THEN** os painéis são redimensionados proporcionalmente
- **AND** o layout é salvo para a próxima sessão

---

### Requirement: Painel Tree - hierarquia navegável

O painel Tree SHALL mostrar a hierarquia completa de widgets com navegação por teclado.

#### Scenario: Tree mostra widgets indentados
- **WHEN** o painel Tree é renderizado
- **THEN** cada nível de hierarquia é indentado com 2 espaços
- **AND** usa caracteres `├─`, `└─`, `│` para conectar nós

#### Scenario: Tree mostra informações resumidas
- **WHEN** um widget é exibido na Tree
- **THEN** mostra:
  - Ícone representativo (📺 Screen, 🎨 Widget, ⚡ AnimatedVerb, etc.)
  - `class_name`
  - Primeira informação de estado relevante entre colchetes
- **EXAMPLE**: `⚡ AnimatedVerb [codando]`

#### Scenario: Navegação por setas
- **WHEN** o usuário usa `↑` `↓` no painel Tree
- **THEN** a seleção move entre nós
- **AND** o painel State atualiza para mostrar o nó selecionado

#### Scenario: Expandir/colapsar nós
- **WHEN** o usuário pressiona `Enter` em um nó com children
- **THEN** o nó é expandido ou colapsado
- **AND** o estado de expansão é mantido enquanto navega

#### Scenario: Filtro de Tree por texto
- **WHEN** o usuário digita texto no painel Tree
- **THEN** apenas nós matching o filtro são mostrados
- **AND** o path completo até o nó é exibido

---

### Requirement: Painel State - estado detalhado

O painel State SHALL mostrar o estado completo do widget selecionado em formato legível.

#### Scenario: Estado básico do widget
- **WHEN** um widget é selecionado na Tree
- **THEN** o painel State mostra:
  - `dom_id`
  - `class_name`
  - `is_visible`, `is_focused`
  - `position` (x, y, width, height)

#### Scenario: Props reactive
- **WHEN** o widget tem props reactive
- **THEN** cada prop é mostrada com:
  - Nome da prop
  - Valor atual
  - Indicador visual se mudou recentemente (●)
  - Último timestamp de mudança

#### Scenario: Estado customizado (dataclasses)
- **WHEN** o widget tem `EstadoLLM` ou similar
- **THEN** a dataclass é expandida mostrando todos os campos
- **AND** valores numéricos mostram barras de progresso visuais
- **EXAMPLE**: `certeza ████░░░░ 0.85`

#### Scenario: Histórico de mudanças
- **WHEN** uma prop reactive tem histórico
- **THEN** um mini-gráfico mostra as últimas 10 mudanças
- **AND** seta ↑↓ indica tendência (subindo/descendo)

#### Scenario: Botão de trace no painel State
- **WHEN** o botão `[+] Trace` é pressionado
- **THEN** tracing é habilitado para todas as props do widget
- **AND** o botão muda para `[-] Untrace`

---

### Requirement: Painel Events - timeline de eventos

O painel Events SHALL mostrar uma timeline cronológica de eventos e mudanças de estado.

#### Scenario: Lista cronológica de eventos
- **WHEN** o painel Events é renderizado
- **THEN** mostra eventos em ordem reversa (mais recentes no topo)
- **AND** cada evento tem timestamp HH:MM:SS.mmm

#### Scenario: Tipos de eventos exibidos
- **WHEN** eventos ocorrem na aplicação
- **THEN** o painel mostra:
  - Mudanças de reactive props (valor old → new)
  - Eventos Textual (click, submit, mount, unmount)
  - Mensagens de log/error do sistema

#### Scenario: Formato de entrada de evento
- **WHEN** um evento é exibido
- **THEN** o formato é:
  ```
  [14:32:01.123] AnimatedVerb.estado changed
                 {verbo: analisando} → {verbo: codando}
  ```
- **AND** o nome do widget é destacado

#### Scenario: Filtro de Events por tipo
- **WHEN** o usuário seleciona filtro "Props apenas"
- **THEN** apenas mudanças de reactive props são mostradas
- **AND** eventos de mount/unmount são ocultados

#### Scenario: Filtro de Events por widget
- **WHEN** um widget está selecionado na Tree
- **THEN** o painel Events mostra apenas eventos desse widget
- **AND** um toggle "Todos os widgets" volta ao filtro global

#### Scenario: Scroll automático para novo evento
- **WHEN** um novo evento é adicionado
- **THEN** o painel Events scrolla para o topo (evento mais recente)
- **AND** o evento é destacado por 500ms

---

### Requirement: Atualização em tempo real

A DevToolsScreen SHALL atualizar automaticamente enquanto está aberta.

#### Scenario: Refresh a cada 100ms
- **WHEN** a DevToolsScreen está aberta
- **THEN** todos os painéis são atualizados a cada 100ms
- **AND** mudanças na aplicação são refletidas na DevTools

#### Scenario: Mudança de prop reflete em tempo real
- **WHEN** uma prop reactive muda na aplicação
- **THEN** o painel State mostra o novo valor em até 100ms
- **AND** o painel Events adiciona entrada da mudança

#### Scenario: Novo widget registrado aparece na Tree
- **WHEN** um novo widget é registrado no DOM
- **THEN** o painel Tree mostra o novo widget
- **AND** a árvore é re-renderizada com o novo nó

#### Scenario: Pause de atualizações
- **WHEN** o usuário pressiona `Ctrl+P` (Pause)
- **THEN** as atualizações são suspensas
- **AND** um badge "PAUSED" aparece no header
- **AND** `Ctrl+P` novamente retoma as atualizações

---

### Requirement: Atalhos de navegação

A DevToolsScreen SHALL ter atalhos para navegação rápida entre painéis e ações comuns.

#### Scenario: Tab entre painéis
- **WHEN** o usuário pressiona `Tab`
- **THEN** o foco move para o próximo painel (Tree → State → Events → Tree)

#### Scenario: Filtro rápido
- **WHEN** o usuário pressiona `/`
- **THEN** o foco vai para o campo de filtro do painel ativo
- **AND** o cursor é posicionado no campo

#### Scenario: Busca de widget
- **WHEN** o usuário pressiona `Ctrl+F`
- **THEN** um modal de busca abre
- **AND** digitando busca na Tree por nome de classe ou dom_id

#### Scenario: Ir para parent/children
- **WHEN** um widget está selecionado e `Alt+↑` é pressionado
- **THEN** a seleção move para o parent
- **WHEN** `Alt+↓` é pressionado
- **THEN** a seleção move para o primeiro child

#### Scenario: Snapshot rápido
- **WHEN** `Ctrl+S` é pressionado
- **THEN** um snapshot do estado atual é capturado
- **AND** uma notificação confirma "Snapshot salvo"

---

### Requirement: Persistência de layout e filtros

A DevToolsScreen SHALL salvar e restaurar o estado entre sessões.

#### Scenario: Layout é salvo
- **WHEN** o usuário redimensiona painéis ou expande nós
- **THEN** o layout é salvo em `~/.skybridge/devtools-state.json`
- **AND** ao reabrir, o layout é restaurado

#### Scenario: Filtros são persistidos
- **WHEN** filtros de Events ou Tree são configurados
- **THEN** os filtros são salvos
- **AND** restaurados na próxima sessão

#### Scenario: Reset de estado
- **WHEN** o usuário pressiona `Ctrl+R` (Reset)
- **THEN** layout e filtros voltam ao padrão
- **AND** uma confirmação é pedida antes de resetar

---

> "Interface de inspeção deve ser tão rápida quanto o pensamento" – made by Sky ⚡
