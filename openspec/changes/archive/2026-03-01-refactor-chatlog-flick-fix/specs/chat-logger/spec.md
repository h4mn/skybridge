# Spec: ChatLogger

## ADDED Requirements

### Requirement: ChatLogger deve redirecionar stdout e stderr permanentemente ao inicializar

O sistema SHALL substituir `sys.stdout` e `sys.stderr` por streams customizados que roteiam todas as saídas para o `ChatLogger`, garantindo que bibliotecas externas não imprimam diretamente na UI Textual.

#### Scenario: Inicialização do ChatLogger redireciona streams
- **WHEN** uma instância de `ChatLogger` é criada
- **THEN** `sys.stdout` e `sys.stderr` são substituídos por `_ChatLoggerStream`
- **AND** streams originais são salvos em `_original_stdout` e `_original_stderr`
- **AND** todas as saídas subsequentes são roteadas para `ChatLogger._route_output()`

#### Scenario: Biblioteca externa imprimindo é capturada
- **WHEN** uma biblioteca externa (sentence-transformers, torch, etc) executa `print("Loading model...")`
- **THEN** o texto é capturado por `_ChatLoggerStream.write()`
- **AND** roteado para `ChatLogger._route_output()`
- **AND** NUNCA aparece na UI Textual

### Requirement: ChatLogger deve fornecer método restore para restaurar streams originais

O sistema SHALL fornecer método `restore()` que restaura `sys.stdout` e `sys.stderr` para seus valores originais e fecha o arquivo de log.

#### Scenario: Método restore devolve streams originais
- **WHEN** `chat_logger.restore()` é chamado
- **THEN** `sys.stdout` é restaurado para `_original_stdout`
- **AND** `sys.stderr` é restaurado para `_original_stderr`
- **AND** arquivo de log é fechado com rodapé de sessão

#### Scenario: ChatLogger funciona como context manager
- **WHEN** `ChatLogger` é usado como context manager (`with ChatLogger() as log:`)
- **THEN** `__exit__` chama `restore()` automaticamente
- **AND** streams são restaurados ao sair do contexto

### Requirement: ChatLogger deve filtrar saídas baseado em verbosidade

O sistema SHALL filtrar saídas capturadas baseado no nível de verbosidade configurado (`DEBUG`, `INFO`, `WARNING`, `ERROR`), descartando mensagens que não atendem ao critério.

#### Scenario: Verbosidade WARNING descarta mensagens de info
- **GIVEN** ChatLogger configurado com `verbosity="WARNING"`
- **WHEN** uma saída contendo "Loading model..." é capturada
- **THEN** a saída é descartada (não salva em arquivo, não exibida na UI)
- **AND** nenhuma ação é tomada

#### Scenario: Verbosidade WARNING loga mensagens de erro
- **GIVEN** ChatLogger configurado com `verbosity="WARNING"`
- **WHEN** uma saída contendo "Error loading model" é capturada
- **THEN** a saída é salva em arquivo
- **AND** a saída é exibida no `ChatLog` widget (se conectado)

### Requirement: ChatLogger deve silenciar bibliotecas externas via variáveis de ambiente e logging

O sistema SHALL configurar variáveis de ambiente (`HF_HUB_OFFLINE`, `TRANSFORMERS_VERBOSITY`, `TOKENIZERS_PARALLELISM`) e níveis de logging do Python para silenciar saídas de sentence-transformers, torch, transformers e huggingface_hub.

#### Scenario: Variáveis de ambiente são configuradas na inicialização
- **WHEN** `ChatLogger.__init__()` é executado
- **THEN** `os.environ["HF_HUB_OFFLINE"]` é configurado para `"1"`
- **AND** `os.environ["TRANSFORMERS_VERBOSITY"]` é configurado para `"error"`
- **AND** `os.environ["TOKENIZERS_PARALLELISM"]` é configurado para `"false"`

#### Scenario: Loggers de bibliotecas externas são configurados para CRITICAL
- **WHEN** `ChatLogger._setup_external_libs()` é executado
- **THEN** `logging.getLogger("sentence_transformers")` tem nível `CRITICAL`
- **AND** `logging.getLogger("torch")` tem nível `CRITICAL`
- **AND** `logging.getLogger("transformers")` tem nível `CRITICAL`
- **AND** `logging.getLogger("huggingface_hub")` tem nível `CRITICAL`

### Requirement: ChatLogger deve salvar logs em arquivo isolado

O sistema SHALL salvar todas as saídas logadas (baseado em verbosidade) em arquivo isolado `.sky/chat.log` com cabeçalho de sessão contendo `session_id` e timestamp.

#### Scenario: Arquivo de log é criado com cabeçalho de sessão
- **WHEN** `ChatLogger` é inicializado
- **THEN** arquivo `.sky/chat.log` é criado (ou aberto em modo append)
- **AND** cabeçalho é escrito com formato:
  ```
  ============================================================
  Chat Session: {session_id}
  Started: {timestamp_iso}
  ============================================================
  ```

#### Scenario: Mensagens logadas são escritas no arquivo
- **WHEN** `chat_logger.info("Mensagem")` é chamado
- **THEN** linha é escrita no arquivo: `[HH:MM:SS] [CHAT] [INFO] Mensagem`

#### Scenario: Rodapé de sessão é escrito no restore
- **WHEN** `chat_logger.restore()` é chamado
- **THEN** rodapé é escrito no arquivo:
  ```
  ============================================================
  Session Ended: {timestamp_iso}
  ============================================================
  ```

### Requirement: ChatLogger deve integrar com ChatLog widget para exibição na UI

O sistema SHALL fornecer método `set_chat_log_widget()` e aceitar parâmetro `chat_log_widget` no construtor para conectar o `ChatLogger` ao widget `ChatLog` existente, permitindo exibição de logs na UI Textual.

#### Scenario: ChatLog widget é conectado via construtor
- **GIVEN** um widget `ChatLog` existente
- **WHEN** `ChatLogger(chat_log_widget=chat_log_widget)` é criado
- **THEN** `_chat_log_widget` é armazenado
- **AND** chamadas a `info()`, `error()`, `evento()` etc são exibidas no widget

#### Scenario: ChatLog widget é conectado via setter
- **GIVEN** um `ChatLogger` sem widget conectado
- **WHEN** `chat_logger.set_chat_log_widget(widget)` é chamado
- **THEN** `_chat_log_widget` é atualizado
- **AND** chamadas subsequentes são exibidas no widget

#### Scenario: Logs não são exibidos na UI quando show_in_ui=False
- **GIVEN** `ChatLogger(show_in_ui=False)` foi criado
- **WHEN** `chat_logger.error("Erro")` é chamado
- **THEN** mensagem é salva em arquivo
- **AND** mensagem NÃO é exibida no `ChatLog` widget

### Requirement: ChatLogger deve fornecer interface simples de logging

O sistema SHALL fornecer métodos `debug()`, `info()`, `warning()`, `error()`, `evento()` e `structured()` para logging estruturado, seguindo a interface do widget `ChatLog`.

#### Scenario: Método info exibe mensagem no ChatLog
- **WHEN** `chat_logger.info("Mensagem informativa")` é chamado
- **THEN** `[INFO] Mensagem informativa` é exibido no `ChatLog` widget em ciano
- **AND** log é salvo em arquivo

#### Scenario: Método error exibe mensagem no ChatLog
- **WHEN** `chat_logger.error("Erro crítico")` é chamado
- **THEN** `[ERROR] Erro crítico` é exibido no `ChatLog` widget em vermelho bold
- **AND** log é salvo em arquivo

#### Scenario: Método evento exibe mensagem no ChatLog
- **WHEN** `chat_logger.evento("RAG", "Busca completada")` é chamado
- **THEN** `[EVENTO] RAG Busca completada` é exibido no `ChatLog` widget em verde
- **AND** log é salvo em arquivo

#### Scenario: Método structured loga dados JSON
- **WHEN** `chat_logger.structured("Busca realizada", {"query": "teste", "results": 5})` é chamado
- **THEN** log é salvo em arquivo com JSON serializado
- **AND** log é exibido no `ChatLog` widget (se disponível)

### Requirement: ChatLogger deve ser completamente independente do SkybridgeLogger

O sistema SHALL NÃO importar ou depender de `runtime.observability.logger`, implementando sua própria lógica de logging de forma isolada.

#### Scenario: ChatLogger não importa SkybridgeLogger
- **WHEN** código de `ChatLogger` é analisado
- **THEN** NÃO há imports de `runtime.observability.logger`
- **AND** NÃO há uso de `get_logger()` do `runtime`
- **AND** `ChatLogger` é completamente independente

#### Scenario: Domínio sky.chat não importa SkybridgeLogger
- **WHEN** código de `src/core/sky/chat/*` é analisado
- **THEN** NÃO há imports de `runtime.observability.logger`
- **AND** apenas `ChatLogger` de `core.sky.chat.logging` é usado
