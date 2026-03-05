# Spec: Textual Async Workers

## ADDED Requirements

### Requirement: Workers assíncronos para operações pesadas

O sistema DEVERÁ usar workers assíncronos para executar operações pesadas sem bloquear a UI Textual.

#### Cenário: Worker executa operação em background
- **QUANDO** operação pesada é iniciada (ex: chamada à API Claude)
- **ENTÃO** worker assíncrono é criado
- **E** operação é executada em background
- **E** UI Textual permanece responsiva
- **E** usuário pode continuar interagindo com a UI

#### Cenário: Worker notifica progresso
- **QUANDO** worker está executando operação longa
- **ENTÃO** worker emite eventos de progresso
- **E** UI é atualizada com indicador de progresso
- **E** usuário sabe que operação está em andamento

#### Cenário: Worker completa operação
- **QUANDO** worker finaliza operação
- **ENTÃO** resultado é retornado à UI
- **E** UI é atualizada com resultado
- **E** worker é encerrado

---

### Requirement: Worker para geração de resposta Claude

O sistema DEVERÁ usar worker assíncrono para chamadas à API Claude, evitando bloqueio da UI.

#### Cenário: Worker chama Claude SDK
- **QUANDO** usuário envia mensagem
- **ENTÃO** worker assíncrono é criado para chamar Claude SDK
- **E** UI exibe indicador "Sky está pensando..."
- **E** usuário pode continuar digitando (para buffer)

#### Cenário: Worker retorna resposta
- **QUANDO** worker recebe resposta do Claude SDK
- **ENTÃO** resposta é passada para a UI
- **E** bubble da mensagem é exibida
- **E** indicador thinking é removido

#### Cenário: Worker trata erro de API
- **QUANDO** worker encontra erro (timeout, rate limit, etc)
- **ENTÃO** erro é capturado
- **E** mensagem de erro amigável é exibida
- **E** UI não trava nem crasha

---

### Requirement: Worker para busca RAG

O sistema DEVERÁ usar worker assíncrono para buscas no banco de memória, evitando bloqueio.

#### Cenário: Worker busca memórias relevantes
- **QUANDO** usuário envia mensagem
- **ENTÃO** worker assíncrono executa busca RAG
- **E** busca é paralela à chamada Claude (se possível)
- **OU** busca é executada antes da chamada Claude

#### Cenário: Worker retorna top N memórias
- **QUANDO** worker completa busca
- **ENTÃO** top 5 memórias mais relevantes são retornadas
- **E** memórias são injetadas no contexto Claude

#### Cenário: Worker lida com banco vazio
- **QUANDO** worker busca em banco vazio
- **ENTÃO** lista vazia é retornada
- **E** contexto "{nenhuma memória relevante}" é usado

---

### Requirement: Worker para salvamento de memória

O sistema DEVERÁ usar worker assíncrono para salvar novas memórias aprendidas durante conversa.

#### Cenário: Worker salva memória aprendida
- **QUANDO** Sky aprende nova informação durante conversa
- **ENTÃO** worker assíncrono salva memória via PersistentMemory.learn()
- **E** UI não é bloqueada pelo salvamento
- **E** usuário recebe feedback sutil (ex: "💾 Aprendido")

#### Cenário: Worker confirma salvamento
- **QUANDO** worker finaliza salvamento
- **ENTÃO** confirmação é registrada em log
- **E** memória fica disponível para próximas buscas

---

### Requirement: Worker para tool execution

O sistema DEVERÁ usar worker assíncrono para executar ferramentas (function calling), mantendo UI responsiva.

#### Cenário: Worker executa tool
- **QUANDO** Claude chama uma ferramenta (function calling)
- **ENTÃO** worker assíncrono executa a tool
- **E** UI exibe indicador "Executando: <tool>..."
- **E** usuário pode ver progresso

#### Cenário: Worker retorna resultado da tool
- **QUANDO** worker finaliza execução da tool
- **ENTÃO** resultado é retornado ao Claude
- **E** indicador é atualizado (✅ ou ❌)
- **E** Claude continua gerando resposta

#### Cenário: Multiple workers para múltiplas tools
- **QUANDO** Claude chama múltiplas tools em paralelo
- **ENTÃO** múltiplos workers são criados
- **E** cada tool executa em seu próprio worker
- **E** UI exibe indicadores para cada tool

---

### Requirement: Pool de workers reutilizáveis

O sistema DEVERÁ manter pool de workers para reutilização, evitando criação/destruição excessiva.

#### Cenário: Pool de workers é criado ao iniciar
- **QUANDO** aplicativo Textual é iniciado
- **ENTÃO** pool de N workers é criado
- **E** workers ficam ociosos aguardando tarefas

#### Cenário: Tarefa é atribuída a worker ocioso
- **QUANDO** nova tarefa assíncrona é necessária
- **ENTÃO** worker ocioso do pool é atribuído
- **E** worker executa tarefa
- **E** worker volta ao pool após completar

#### Cenário: Pool se expande se necessário
- **QUANDO** todas as workers estão ocupadas
- **E** nova tarefa chega
- **ENTÃO** worker adicional é criado (até limite máximo)
- **E** pool cresce dinamicamente

#### Cenário: Pool encolhe quando ocioso
- **QUANDO** workers ficam ociosas por período prolongado
- **ENTÃO** workers excessivas são encerradas
- **E** pool volta ao tamanho base

---

### Requirement: Cancelamento de workers

O sistema DEVERÁ permitir cancelar workers em execução (ex: usuário cancela operação).

#### Cenário: Usuário cancela operação
- **QUANDO** usuário digita /cancel durante operação longa
- **ENTÃO** sinal de cancelamento é enviado ao worker
- **E** worker interrompe operação gracefully
- **E** recursos são liberados

#### Cenário: Timeout cancela worker automaticamente
- **QUANDO** worker excede tempo limite (ex: 30 segundos)
- **ENTÃO** worker é cancelado automaticamente
- **E** erro de timeout é exibido ao usuário
- **E** UI volta ao estado normal

---

### Requirement: Sincronização de workers com UI

O sistema DEVERÁ sincronizar resultados de workers com a UI Textual de forma thread-safe.

#### Cenário: Worker atualiza UI de forma segura
- **QUANDO** worker precisa atualizar a UI
- **ENTÃO** atualização é enfileirada para thread principal
- **E** UI processa atualização no momento apropriado
- **E** não há condição de corrida

#### Cenário: Múltiplos workers atualizam UI simultaneamente
- **QUANDO** múltiplos workers precisam atualizar UI
- **ENTÃO** atualizações são processadas em ordem
- **E** não há conflito de renderização

---

### Requirement: Métricas de workers

O sistema DEVERÁ coletar métricas sobre workers para monitoramento de performance.

#### Cenário: Tempo de execução é medido
- **QUANDO** worker executa tarefa
- **ENTÃO** tempo de início é marcado
- **E** tempo de fim é marcado
- **E** duração é registrada em métricas

#### Cenário: Contagem de workers ativos
- **QUANDO** sistema está rodando
- **ENTÃO** quantidade de workers ativas é monitorada
- **E** se pool estiver sempre cheio, alerta é registrado

#### Cenário: Errors de workers são registrados
- **QUANDO** worker falha
- **ENTÃO** erro é registrado com stack trace
- **E** erro é incluído nas métricas da sessão

---

> "A assincronicidade é a arte de fazer mais com menos espera" – made by Sky 🚀
