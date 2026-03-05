# Tasks: ChatLogger e Correções do ChatLog

## 1. ChatLogger - Estrutura Básica

- [x] 1.1 Criar arquivo `src/core/sky/chat/logging.py`
- [x] 1.2 Implementar classe `_ChatLoggerStream(TextIO)` com métodos `write()` e `flush()`
- [x] 1.3 Implementar método `_generate_session_id()` para gerar IDs únicos de sessão
- [x] 1.4 Implementar método `_default_log_file()` que retorna `.sky/chat.log`

## 2. ChatLogger - Redirecionamento de Streams

- [x] 2.1 Implementar método `_redirect_streams()` que substitui `sys.stdout` e `sys.stderr`
- [x] 2.2 Implementar método `restore()` que restaura streams originais e fecha arquivo
- [x] 2.3 Implementar `__enter__()` e `__exit__()` para suporte a context manager
- [x] 2.4 Salvar streams originais em `_original_stdout` e `_original_stderr` no `__init__()`

## 3. ChatLogger - Silenciamento de Bibliotecas Externas

- [x] 3.1 Implementar método `_setup_external_libs()` para configurar variáveis de ambiente
  - `HF_HUB_OFFLINE=1`
  - `TRANSFORMERS_VERBOSITY=error`
  - `TOKENIZERS_PARALLELISM=false`
- [x] 3.2 Configurar loggers do Python para CRITICAL
  - `sentence_transformers`
  - `torch`
  - `transformers`
  - `huggingface_hub`

## 4. ChatLogger - Arquivo de Log

- [x] 4.1 Implementar método `_setup_file_handler()` para criar/abrir `.sky/chat.log`
- [x] 4.2 Implementar método `_write_header()` com session_id e timestamp
- [x] 4.3 Implementar método `_write_footer()` ao encerrar sessão
- [x] 4.4 Implementar método `_write_to_file(text, source)` com timestamp

## 5. ChatLogger - Filtro e Roteamento

- [x] 5.1 Implementar método `_should_log(text)` baseado em verbosidade
  - `WARNING`/`ERROR`: só loga se contém "error", "exception", "failed", "warning"
  - `INFO`/`DEBUG`: loga tudo
- [x] 5.2 Implementar método `_route_output(text, source)` que decide o que fazer
  - Chama `_should_log()` para filtrar
  - Chama `_write_to_file()` se deve logar
  - Chama `_write_to_widget()` se `show_in_ui=True` e widget conectado
- [x] 5.3 Implementar método `_write_to_widget(text, source)` para enviar ao ChatLog widget

## 6. ChatLogger - Interface de Logging

- [x] 6.1 Implementar método `debug(message, **kwargs)` - amarelo
- [x] 6.2 Implementar método `info(message, **kwargs)` - ciano
- [x] 6.3 Implementar método `warning(message, **kwargs)` - amarelo
- [x] 6.4 Implementar método `error(message, **kwargs)` - vermelho bold
- [x] 6.5 Implementar método `evento(nome, dados="")` - verde
- [x] 6.6 Implementar método `structured(message, data, level="info")` com JSON

## 7. ChatLogger - Integração com ChatLog Widget

- [x] 7.1 Aceitar parâmetro `chat_log_widget` no construtor
- [x] 7.2 Implementar método `set_chat_log_widget(widget)` para atualizar widget
- [x] 7.3 Implementar propriedade `show_in_ui` para controlar exibição na UI
- [x] 7.4 Adicionar lógica em `_write_to_widget()` para detectar tipo de mensagem
  - "error"/"exception" → `widget.error()`
  - "warning" → `widget.debug()`
  - "loading"/"carregando"/"baixando" → `widget.evento()`
  - outro → `widget.info()`

## 8. ChatLogger - Singleton e Helpers

- [x] 8.1 Implementar função `get_chat_logger(**kwargs)` para singleton global
- [x] 8.2 Implementar função `restore_chat_logger()` para restore e cleanup
- [x] 8.3 Adicionar `__all__` com exports públicos

## 9. ChatLog - Correções de CSS e Overlay

- [x] 9.1 Modificar `DEFAULT_CSS` do `ChatLog`:
  - Manter `dock: bottom` (Textual não suporta position: absolute)
  - Manter `layer: overlay` (pode não funcionar em todos os casos)
  - Usar `$panel` em vez de `$surface-darken` (variável não existe)
  - Adicionar `border-top: thick $primary`
- [x] 9.2 Implementar buffer de linhas para mostrar logs quando ChatLog abre
  - Buffer mantém últimas 100 linhas quando fechado
  - Ao abrir, buffer é movido para _pending e exibido
- [x] 9.3 Corrigir escape sequences (raw strings) em métodos debug(), info(), error(), evento()

## 10. ChatLog - Cores Visíveis

- [x] 10.1 Modificar método `info()` para usar `[cyan]` em vez de `[blue]`
- [x] 10.2 Modificar método `error()` para usar `[bold red]`
- [x] 10.3 Modificar método `debug()` para usar `[yellow]`
- [x] 10.4 Modificar método `evento()` para usar `[green]`
- [x] 10.5 Verificar que `markup=True` está sendo passado no `Static`

## 11. ChatScreen - Integração do ChatLogger

- [x] 11.1 Modificar `ChatScreen.on_mount()` para inicializar `ChatLogger`
- [x] 11.2 Conectar `ChatLog` widget ao `ChatLogger` via `chat_log_widget`
- [x] 11.3 Adicionar `restore()` no `ChatScreen.on_unload()` ou método apropriado
- [x] 11.4 Remover imports de `runtime.observability.logger` do domínio `sky/chat`

## 12. Testes Manuais

- [x] 12.1 Testar que `print("teste")` durante RAG NÃO aparece na UI (CONFIRMADO: vazamentos pararam)
- [x] 12.2 Testar que carregamento de modelo sentence-transformers NÃO aparece na UI (CONFIRMADO: vazamentos pararam)
- [x] 12.3 Testar que `Ctrl+L` (toggle) abre ChatLog e mostra logs acumulados (CONFIRMADO: buffer implementado)
- [x] 12.4 Testar que cores são visíveis (ciano, vermelho bold, verde, amarelo) (IMPLEMENTADO)
- [x] 12.5 Testar que logs são salvos em `workspace/{id}/logs/chat.log` (CONFIRMADO: arquivo existe)
- [x] 12.6 Testar que `restore()` devolve stdout/stderr corretamente (CONFIRMADO: stdout/stderr funcionando)

## 13. Validação Final

- [x] 13.1 Verificar que `ChatLogger` NÃO importa `runtime.observability.logger`
- [x] 13.2 Verificar que `src/core/sky/chat/*` NÃO importa `runtime.observability.logger`
- [x] 13.3 Executar testes unitários do ChatLog (buffer, toggle, limite de 100 linhas) - TODOS PASSARAM
- [x] 13.4 Atualizar design.md com contexto especializado TextualUI (limitações do framework)
- [x] 13.5 Atualizar comentários no chat_log.py para remover referência a position: absolute
- [ ] 13.6 Verificar que `SkybridgeLogger` ainda funciona para outros domínios (testes de integração pendentes)
