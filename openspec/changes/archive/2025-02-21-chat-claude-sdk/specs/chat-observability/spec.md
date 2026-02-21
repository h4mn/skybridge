# Spec: Observabilidade do Chat

## ADDED Requirements

### Requirement: Métricas de latência registradas

O sistema DEVERÁ registrar latência de cada geração de resposta para monitoramento de performance.

#### Cenário: Latência medida e registrada
- **QUANDO** resposta é gerada via Claude SDK
- **ENTÃO** tempo de início é marcado antes da chamada
- **E** tempo de fim é marcado após resposta recebida
- **E** latência em ms é calculada (fim - início)
- **E** latência é registrada em log estruturado

#### Cenário: Latência exibida em modo verbose
- **QUANDO** chat é iniciado com flag `--verbose`
- **ENTÃO** latência de cada resposta é exibida ao usuário
- **E** formato é "⏱️ Resposta em 1.2s (1234ms)"

#### Cenário: Alerta de latência alta
- **QUANDO** latência excede 5000ms (5 segundos)
- **ENTÃO** alerta é registrado no log
- **E** usuário é notificado: "⚠️ Resposta demorou mais que o normal"

---

### Requirement: Contagem de tokens registrada

O sistema DEVERÁ registrar quantidade de tokens usados (entrada e saída) para controle de custos.

#### Cenário: Tokens de entrada contados
- **QUANDO** requisição é enviada para Claude SDK
- **ENTÃO** total de tokens de entrada é registrado
- **E** contagem inclui system prompt + contexto de memória + mensagem do usuário
- **E** tokens são registrados em log estruturado

#### Cenário: Tokens de saída contados
- **QUANDO** resposta é recebida do Claude SDK
- **ENTÃO** total de tokens de saída é registrado
- **E** contagem reflete tamanho exato da resposta gerada
- **E** tokens são registrados em log estruturado

#### Cenário: Totais de sessão exibidos ao encerrar
- **QUANDO** usuário encerra sessão com "sair"
- **ENTÃO** totais acumulados são exibidos
- **E** formato é "💰 Sessão: 1234 tokens in, 567 tokens out"

---

### Requirement: Uso de memória RAG observável

O sistema DEVERÁ registrar quantidade de memórias usadas e sua relevância para debugging.

#### Cenário: Contagem de memórias usadas
- **QUANDO** busca RAG é executada
- **ENTÃO** quantidade de memórias recuperadas é registrada
- **E** contagem distingue entre memórias acima e abaixo do threshold
- **E** contagem é incluída nas métricas da resposta

#### Cenário: Scores de similaridade registrados
- **QUANDO** memórias são recuperadas do RAG
- **ENTÃO** score de similaridade de cada memória é registrado
- **E** scores permitem analisar qualidade da busca semântica
- **E** scores são registrados em log detalhado (debug level)

#### Cenário: Memórias exibidas na UI
- **QUANDO** memórias são usadas na resposta
- **ENTÃO** UI exibe "📚 N memórias usadas"
- **E** preview das memórias é exibido em modo verbose
- **E** usuário pode ver qual contexto foi considerado

---

### Requirement: Execução de tools observável

O sistema DEVERÁ registrar tools executadas durante geração de resposta para rastreamento.

#### Cenário: Tools executadas listadas
- **QUANDO** Claude usa function calling durante resposta
- **ENTÃO** cada tool executada é registrada
- **E** nome da tool e parâmetros são registrados
- **E** resultado da tool é registrado (sucesso/falha)

#### Cenário: Tools exibidas na UI
- **QUANDO** tools são executadas durante resposta
- **ENTÃO** UI exibe "🔧 N tools executadas"
- **E** lista de tools é exibida em modo verbose
- **E** formato é tabela com nome e resultado

#### Cenário: Falha de tool registrada
- **QUANDO** tool falha durante execução
- **ENTÃO** erro é registrado com stack trace
- **E** falha é notificada na UI como "❌ Tool falhou"
- **E** resposta pode continuar sem a tool (fallback)

---

### Requirement: Estrutura de logs estruturados

O sistema DEVERÁ usar formato de log estruturado para fácil parsing e análise.

#### Cenário: Log em formato JSON
- **QUANDO** registrando eventos de chat
- **ENTÃO** logs são emitidos em formato JSON
- **E** cada log contém campos: timestamp, level, event, data
- **E** exemplos de eventos: chat.request, chat.response, chat.error

#### Cenário: Logs escritos em arquivo
- **QUANDO** chat é iniciado com flag `--log-file`
- **ENTÃO** logs são escritos em arquivo `.sky_chat.log`
- **E** arquivo é append-only (não sobrescreve)
- **E** rotação de log é feita a cada 10MB

#### Cenário: Níveis de log configuráveis
- **QUANDO** chat é iniciado com flag `--log-level`
- **ENTÃO** nível de log é definido (DEBUG, INFO, WARNING, ERROR)
- **E** apenas logs igual ou acima do nível são exibidos
- **E** padrão é INFO

---

### Requirement: Métricas agregadas por sessão

O sistema DEVERÁ calcular e exibir métricas agregadas ao fim de cada sessão.

#### Cenário: Resumo ao encerrar sessão
- **QUANDO** usuário digita "sair" ou Ctrl+C
- **ENTÃO** resumo da sessão é exibido
- **E** resumo inclui: mensagens trocadas, latência média, tokens totais
- **E** formato é tablea Rich com bordas

#### Cenário: Comparação com sessão anterior
- **QUANDO** sessão anterior existe nos logs
- **ENTÃO** resumo compara métricas com sessão anterior
- **E** delta é mostrado (↑↓) para latência média
- **E** tendência é indicada (melhor/pior)

---

### Requirement: Health checks externos

O sistema DEVERÁ suportar health checks para monitoramento externo (futuro).

#### Cenário: Endpoint /health para status
- **QUANDO** requisição HTTP é feita para endpoint /health
- **ENTÃO** status do chat é retornado
- **E** resposta inclui: Claude API status, RAG status, last response time
- **NOTA**: Este cenário é para implementação futura de API

#### Cenário: Métricas expostas em formato Prometheus
- **QUANDO** endpoint /metrics é consultado
- **ENTÃO** métricas são expostas em formato Prometheus
- **E** métricas incluem: chat_requests_total, chat_latency_ms, chat_tokens_total
- **NOTA**: Este cenário é para implementação futura

---

> "O que não é medido não pode ser melhorado" – made by Sky 🚀
