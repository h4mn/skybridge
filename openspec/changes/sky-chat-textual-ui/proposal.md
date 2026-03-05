# Proposal: Sky Chat Textual UI

## Why

A UI atual do chat Sky baseada em input/output simples não oferece uma experiência visual rica. O Textual TUI oferece componentes assíncronos, suporte a CSS e layouts flexíveis que permitirão criar uma interface de chat moderna, responsiva e visualmente atraente que se integra perfeitamente com o Agent SDK assíncrono.

## What Changes

### Layout Principal
- **BREAKING**: Substituir UI atual (stdin/stdout simples) por Textual TUI
- Layout com cabeçalho fixo (2 linhas), rodapé fixo (input + status bar) e área de conteúdo scrollável
- Margem estético no container principal para breathing room

### Cabeçalho (2 linhas - Opção B)
```
┌────────────────────────────────────────────────────────────────────────────┐
│  🌌 Sky Chat: "Sky debugando erro na API"              [████████░░] 80%    │
│  RAG: ON │ 3 mems │ ⚡1.2s │ 💰 1234/10k tokens │ Haiku 3.5                    │
└────────────────────────────────────────────────────────────────────────────┘
```

**Linha 1 - Título + Barra de Contexto:**
- Título dinâmico no formato: `"Sujeito | Verbo Gerúndio Animado | Predicado"`
  - Exemplo: `"Sky debugando erro na API"`, `"Sky aprendendo async Python"`
  - Verbo com **color sweep animation**: onda de cor percorre as letras da esquerda para direita
  - Título é gerado/regenerado pela Sky conforme a conversa evolui
- Barra de progressão de contexto (0-100% da janela de 20 mensagens)
  - 🟢 Verde (0-50%), 🟡 Amarelo (51-75%), 🟠 Laranja (76-90%), 🔴 Vermelho (91-100%)
  - Mostra quantas mensagens do contexto foram usadas antes de truncar

**Linha 2 - Métricas de Observabilidade:**
- RAG status (ON/OFF), memórias usadas, latência última, tokens sessão, modelo

### Container de Mensagens
- Sistema de mensagens com bubbles estilizados via CSS
- Separador visual claro entre turnos (resolvendo confusão atual)
- Scroll container com auto-scroll para última mensagem
- Markdown customizado com syntax highlighting

### Componentes de Feedback
- `thinking` indicator animado (não apenas texto)
- `tool-feedback` para execução de ferramentas
- Toast/notifications para alertas
- Modal para confirmações (/new, /cancel)

### Tela de Apresentação (Welcome Screen)
- Centralizada horizontal e verticalmente
- Letreiro "SkyBridge" animado
- Input abaixo do letreiro
- Rodapé introdutório diferenciado

### Extras
- Screen management com push/pop para navegação entre telas
- Workers assíncronos para operações pesadas sem travar a UI
- Suporte a comandos com widgets: buttons, inputs, checkboxes, listviews, datatables, trees
- CSS customizável para temas

## Capabilities

### New Capabilities
- `textual-chat-ui`: Interface de chat baseada em Textual TUI com header/footer fixos, message bubbles e componentes interativos
- `textual-layouts`: Sistema de layouts Textual (vertical, horizontal, grid, dock) para organizar componentes da UI
- `textual-screen-management`: Sistema de navegação entre telas com push/pop de screens
- `textual-async-workers`: Workers assíncronos para executar operações pesadas sem bloquear a UI

### Modified Capabilities

#### UI existente será completamente substituída:

- **`claude-chat-integration`**: Toda UI de chat muda de Rich para Textual
  - Header: de `Panel` Rich → Header fixo Textual
  - Footer: de `Panel` Rich → Footer fixo com input field
  - Mensagens: de `Markdown` direto → Message bubbles em scroll container
  - Thinking: de texto simples → Componente animado Textual
  - Memórias: de texto dim → Widget/panel Textual customizado
  - Tools: de `Table` Rich → Componente Textual integrado

- **`chat-observability`**: Componentes de métricas e feedback muda de Rich para Textual
  - Tools executadas: de `Table` Rich → DataTable ou lista Textual
  - Resumo da sessão: de `Table` Rich → DataTable Textual
  - Alertas: de texto formatado → Notificações/toast Textual
  - Métricas inline: de texto dim → Badge/meter Textual

- **`chat-session-context`**: Tela de apresentação e separação visual muda
  - Tela inicial: de ASCII box → Tela centralizada horizontal/vertical com letreiro "SkyBridge", input abaixo, rodapé introdutório
  - Separação de conversas: de inexistente/confuso → Separador visual claro entre turnos
  - Notificação /new: de texto simples → Modal ou overlay Textual

- **`sky-personality`**: Renderização de markdown pode precisar de customização
  - Blocos de código: de Rich padrão → Syntax highlighting customizado via CSS Textual
  - Formatação: de Rich markdown → MarkdownText widget com CSS personalizado

## Impact

- **Novo código**: `src/core/sky/chat/textual_ui.py` e módulos relacionados
- **Dependência**: `textual` e `textual-dev` adicionados ao requirements.txt
- **Compatibilidade**: CLI `sky`将继续 suportar modo simples se `USE_TEXTUAL_UI=false`
- **Testes**: Novos testes unitários para componentes Textual e integração com Agent SDK
