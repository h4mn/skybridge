# Estrutura de Componentes - Chat Sky

> Documento gerado automaticamente com toda a árvore de componentes do Chat Sky em formato de arquivos.

```
src/core/sky/chat/textual_ui/
├── __init__.py
├── commands.py
├── voice_commands.py
│
├── dom/
│   ├── __init__.py
│   ├── node.py
│   ├── mixin.py
│   ├── differ.py
│   ├── registry.py
│   ├── snapshot.py
│   ├── tracer.py
│   └── watcher.py
│
├── dom/screens/
│   ├── __init__.py
│   └── devtools.py
│
├── screens/
│   ├── __init__.py
│   ├── chat.py
│   ├── config.py
│   ├── help.py
│   ├── session_summary.py
│   └── welcome.py
│
├── styles/
│   └── __init__.py
│
├── widgets/
│   ├── __init__.py
│   ├── animated_verb.py
│   ├── bubbles.py
│   ├── chat_log.py
│   ├── chat_scroll.py
│   ├── chat_text_area.py
│   ├── context_bar.py
│   ├── header.py
│   ├── modal.py
│   ├── overlay_container.py
│   ├── recording_mixin.py
│   ├── thinking.py
│   ├── title.py
│   ├── title_history.py
│   ├── title_history_dialog.py
│   ├── toast.py
│   ├── tool_feedback.py
│   └── turn.py
│
└── workers/
    ├── __init__.py
    ├── base.py
    ├── claude.py
    ├── errors.py
    ├── memory.py
    ├── metrics.py
    ├── queue.py
    └── rag.py
```

## Descrição dos Diretórios

### `/` (Raiz)
- **__init__.py**: Inicialização do módulo textual_ui
- **commands.py**: Sistema de comandos do chat
- **voice_commands.py**: Comandos de voz integrados

### `/dom`
Sistema de DOM customizado para gerenciamento de componentes:
- **node.py**: Nó base do DOM
- **mixin.py**: Mixins para componentes
- **differ.py**: Algoritmo de diff para atualizações
- **registry.py**: Registro de componentes
- **snapshot.py**: Sistema de snapshots do estado
- **tracer.py**: Rastreamento de mudanças
- **watcher.py**: Observador de modificações

### `/dom/screens`
- **devtools.py**: Ferramentas de desenvolvedor

### `/screens`
Telas principais da aplicação:
- **chat.py**: Tela principal do chat
- **config.py**: Tela de configurações
- **help.py**: Tela de ajuda
- **session_summary.py**: Resumo da sessão
- **welcome.py**: Tela de boas-vindas

### `/styles`
- **__init__.py**: Estilos globais e temas

### `/widgets`
Componentes de UI reutilizáveis:
- **animated_verb.py**: Verbo animado
- **bubbles.py**: Bolhas de mensagem
- **chat_log.py**: Log do chat
- **chat_scroll.py**: Scroll customizado do chat
- **chat_text_area.py**: Área de texto do chat
- **context_bar.py**: Barra de contexto
- **header.py**: Cabeçalho da aplicação
- **modal.py**: Componente modal
- **overlay_container.py**: Container de overlays
- **recording_mixin.py**: Mixin de gravação
- **thinking.py**: Indicador de pensamento
- **title.py**: Título da aplicação
- **title_history.py**: Histórico de títulos
- **title_history_dialog.py**: Diálogo de histórico de títulos
- **toast.py**: Notificações toast
- **tool_feedback.py**: Feedback de ferramentas
- **turn.py**: Turno de conversa

### `/workers`
Processos em background:
- **base.py**: Worker base
- **claude.py**: Worker de integração com Claude
- **errors.py**: Tratamento de erros
- **memory.py**: Sistema de memória
- **metrics.py**: Métricas e monitoramento
- **queue.py**: Fila de tarefas
- **rag.py**: Worker de RAG (Retrieval Augmented Generation)

## Principais Tecnologias

- **Textual**: Framework de UI terminal
- **Python**: Linguagem principal
- **Claude API**: Integração com IA
- **RAG**: Sistema de memória com busca semântica
- **DOM Custom**: Sistema próprio de gerenciamento de componentes

---

> "A estrutura é a espinha dorsal de qualquer software sólido" 🏗️ made by Sky 🚀
