# Proposal: SkyTextualDOM - DevTools para Textual TUI

## Why

A interface Textual TUI do Skybridge possui uma arquitetura reativa complexa com múltiplos níveis de estado (AnimatedVerb com EstadoLLM, Turn com estados de processamento, métricas dinâmicas, etc.). Atualmente, a inspeção desse estado é limitada a tooltips, modais pontuais e o ChatLog. Não existe uma forma centralizada de visualizar a árvore completa de widgets e seus estados em tempo real, dificultando debugging e compreensão do fluxo de dados.

**Problema:** Impossível ver "o que está acontecendo" em toda a UI de uma vez.

**Agora:** A TUI está crescendo em complexidade (PRD019, P3, P4) e precisa de ferramentas de inspeção adequadas.

## What Changes

Implementar um sistema **DOM-like** inspirado no React DevTools/Browser DevTools para Textual:

- **SkyTextualDOM**: Registro global automático de widgets com árvore navegável
- **DOMNode**: Wrapper que encapsula widget + estado serializável + histórico
- **ReactiveWatcher**: Rastreamento automático de mudanças em `reactive()` props
- **DevToolsScreen**: Tela dedicada (Ctrl+D) com visualização em 3 painéis:
  - **Tree**: Hierarquia de widgets com indicadores de estado
  - **State**: Estado detalhado do widget selecionado
  - **Events**: Timeline de mudanças de estado e eventos
- **StateDiff**: Comparação entre snapshots de estado (before/after)
- **EventTracer**: Log de eventos com filtros por tipo/widget
- **SkyWidgetMixin**: Mixin para auto-registro de widgets no DOM

## Capabilities

### New Capabilities

- **dom-registry**: Registro global de widgets com árvore navegável. Gerencia `DOMNode` com referências para parent/children e permite queries estilo CSS (`get()`, `query()`).

- **reactive-watcher**: Rastreamento automático de propriedades `reactive()` de widgets Textual. Detecta mudanças via `watch_*` methods e mantém histórico de valores.

- **devtools-ui**: Interface de inspeção visual com 3 painéis (Tree, State, Events). Acessível via atalho Ctrl+D com navegação por teclado.

- **state-snapshot**: Captura do estado completo da UI em um momento específico. Permite comparação entre snapshots para identificar mudanças.

- **event-tracer**: Log de eventos Textual com metadados (timestamp, widget, tipo, dados). Filtros por tipo de evento e/ou widget específico.

### Modified Capabilities

Nenhuma. Este é um novo sistema isolado que não modifica requisitos de capabilities existentes.

## Impact

### Código Afetado

- **Novos módulos**: `src/core/sky/chat/textual_ui/dom/` (registry, node, watcher, differ, tracer, screens/devtools)
- **Integração opcional**: Widgets existentes podem herdar `SkyWidgetMixin` para auto-registro (não obrigatório)
- **ChatScreen**: Adicionar binding `Ctrl+D` para abrir DevToolsScreen

### APIs

- **Nova API pública**: `SkyTextualDOM` (singleton) com métodos `register()`, `get()`, `query()`, `print()`, `trace()`, `snapshot()`, `diff()`
- **Nova Screen**: `DevToolsScreen` para exibir a interface de inspeção

### Dependências

- **Sem novas dependências externas**: Usa apenas APIs Textual existentes (reactive, events, screen system)

### Sistemas

- **Isolado**: Não interfere no funcionamento normal da TUI. Apenas observa.
- **Overhead mínimo**: Registro e rastreamento são O(1) por widget. Histórico configurável (limitado a N entradas).

---

> "Ver é entender — uma ferramenta de inspeção transforma caos em clareza" – made by Sky 🔍
