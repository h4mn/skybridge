# ChatLog 2.0 - Subsistema de Log

Subsistema de log para aplicações Textual com ring buffer, virtualização e filtros poderosos.

## Características

- **Ring Buffer**: Limite configurável de entries (economiza memória)
- **Virtualização**: Renderiza apenas linhas visíveis + margem (performance)
- **Filtros Combinados**: Nível (DEBUG..CRITICAL) E escopo (SYSTEM, USER, API, etc.)
- **Busca Reativa**: Highlight em tempo real com suporte a curingas (* e ?)
- **Clipboard**: Cópia de logs filtrados para clipboard
- **LogConsumer Protocol**: Desacoplamento entre logger e UI

## Uso Básico

### Criar e Configurar ChatLog

```python
from core.sky.log import ChatLog, ChatLogConfig, LogEntry, LogScope
import logging
from datetime import datetime

# Configuração padrão
config = ChatLogConfig(
    max_entries=1000,              # Ring buffer (auto-descarta antigos)
    buffer_when_closed=100,         # Buffer quando widget fechado
    virtualization_threshold=50,    # Ativa acima de 50 entries
    virtualization_margin=20        # Margem acima/abaixo do visível
)

# Criar widget
chat_log = ChatLog(config=config)
```

### Escrever Logs

```python
# Via LogConsumer Protocol (preferido)
entry = LogEntry(
    level=logging.INFO,
    message="Sistema iniciado",
    timestamp=datetime.now(),
    scope=LogScope.SYSTEM,
    context={"startup_time": 1.23}
)
chat_log.write_log(entry)

# Via ChatLogger adapter
from core.sky.chat.logging import ChatLogger

chat_logger = ChatLogger(log_consumer=chat_log)
chat_logger.info("Mensagem informativa")
chat_logger.error("Erro ocorreu!")
chat_logger.warning("Aviso importante")
```

## Filtros

### Por Nível

```python
# Mostrar apenas ERROR e CRITICAL
chat_log.set_min_level(logging.ERROR)

# Mostrar tudo (NOTSET = ALL)
chat_log.set_min_level(logging.NOTSET)
```

### Por Escopo

```python
# Mostrar apenas logs de voz
chat_log.set_scope(LogScope.VOICE)

# Mostrar todos
chat_log.set_scope(LogScope.ALL)
```

### Busca

```python
# Buscar texto (case-insensitive)
chat_log.set_search_term("error")

# Buscar com curingas
pattern = re.compile("error.*timeout")
chat_log.set_search_term("error", pattern)
```

## Integração com UI

### Usar com LogToolbar

```python
from textual.app import App, ComposeResult
from core.sky.log import ChatLog, ChatLogConfig, LogToolbar

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield LogToolbar()
        yield ChatLog(config=ChatLogConfig())
```

### Eventos

```python
from core.sky.log.widgets import FilterChanged, SearchChanged

class ChatLogScreen(Widget):
    @on(FilterChanged)
    def on_filter_changed(self, event: FilterChanged):
        # Nível ou escopo mudou
        self.chat_log.set_min_level(event.level)
        self.chat_log.set_scope(event.scope)

    @on(SearchChanged)
    def on_search_changed(self, event: SearchChanged):
        # Termo de busca mudou
        self.chat_log.set_search_term(event.search_term)
```

## LogScope (Escopos Disponíveis)

| Escopo | Descrição |
|--------|-----------|
| `ALL` | Todos os escopos |
| `SYSTEM` | Eventos do sistema |
| `USER` | Ações do usuário |
| `API` | Chamadas de API |
| `DATABASE` | Operações de banco |
| `NETWORK` | Operações de rede |
| `VOICE` | Operações de voz/áudio |
| `MEMORY` | Operações de memória |

## Níveis de Log (Padrão logging)

| Nível | Valor | Uso |
|-------|-------|-----|
| `DEBUG` | 10 | Informação detalhada para debugging |
| `INFO` | 20 | Informação geral |
| `WARNING` | 30 | Algo inesperado, mas não erro |
| `ERROR` | 40 | Erro operacional |
| `CRITICAL` | 50 | Erro crítico, sistema pode não continuar |

## Performance

### Ring Buffer

O `ChatLog` usa `collections.deque(maxlen=config.max_entries)` que automaticamente descarta entries mais antigos quando o limite é atingido.

```python
# Configuração para produção
config = ChatLogConfig(
    max_entries=10000,  # Mantém até 10k entries
    virtualization_threshold=200  # Virtualiza acima de 200
)
```

### Virtualização

Quando há muitos entries, apenas os visíveis + margem são renderizados como widgets Textual. Isso reduz drasticamente o uso de memória e tempo de renderização.

```python
# Desabilitar virtualização (não recomendado para >100 entries)
config = ChatLogConfig(
    max_entries=100,
    virtualization_threshold=999999  # Praticamente nunca virtualiza
)
```

### Buffer When Closed

Quando o widget não está visível, um buffer reduzido é usado:

```python
# Economiza memória quando widget fechado
config = ChatLogConfig(
    buffer_when_closed=100  # Apenas 100 entries quando fechado
)
```

## POC (Proof of Concept)

Para testar visualmente:

```bash
python -m core.sky.log.poc
```

Ou via Textual:

```bash
textual run -m core.sky.log.poc
```

## Migração do ChatLog Legado

### Antigo (DEPRECATED)

```python
# NÃO USAR - obsoleto
from core.sky.chat.textual_ui.widgets.common.log import ChatLog

chat_log = ChatLog()
chat_log.info("Mensagem")
chat_log.error("Erro")
chat_log.evento("EVENTO", "dados")
```

### Novo (Recomendado)

```python
# USAR ESTE
from core.sky.log import ChatLog, ChatLogConfig

chat_log = ChatLog(config=ChatLogConfig())
entry = LogEntry(level=logging.INFO, message="Mensagem", ...)
chat_log.write_log(entry)

# Ou via ChatLogger com LogConsumer
from core.sky.chat.logging import ChatLogger

chat_logger = ChatLogger(log_consumer=chat_log)
chat_logger.info("Mensagem")
chat_logger.error("Erro")
# evento() está DEPRECATED - use info() com context
chat_logger.info("EVENTO dados", context={"type": "event", "event_name": "EVENTO"})
```

## Referências

- [Textual Documentation](https://textual.textualize.io/)
- [Python logging](https://docs.python.org/3/library/logging.html)
- Design: `openspec/changes/chatlog-2-0-refactor/design.md`
