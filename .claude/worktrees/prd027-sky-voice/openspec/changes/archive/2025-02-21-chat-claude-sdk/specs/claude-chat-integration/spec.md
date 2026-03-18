# Spec: Integração Claude Chat

## ADDED Requirements

### Requirement: Integração com Claude SDK para geração de respostas

O sistema DEVERÁ usar Claude Agent SDK para gerar respostas no chat, substituindo o sistema de respostas baseadas em padrões fixos.

#### Cenário: Geração de resposta bem-sucedida via SDK
- **QUANDO** usuário envia uma mensagem no chat
- **ENTÃO** sistema gera resposta usando Claude Agent SDK
- **E** resposta é contextualmente relevante à conversa
- **E** resposta mantém a personalidade da Sky

#### Cenário: Falha do SDK com fallback para legacy
- **QUANDO** Claude Agent SDK falha (erro de API, timeout, etc.)
- **ENTÃO** sistema automaticamente volta para respostas legacy baseadas em padrões
- **E** erro é registrado para observabilidade

#### Cenário: Feature flag controla integração
- **QUANDO** variável de ambiente `USE_CLAUDE_CHAT` é `true`
- **ENTÃO** chat usa Claude Agent SDK para respostas
- **QUANDO** variável de ambiente `USE_CLAUDE_CHAT` é `false` ou não definida
- **ENTÃO** chat usa respostas legacy baseadas em padrões

---

### Requirement: Fluxo de mensagens através do ClaudeChatAdapter

O sistema DEVERÁ fornecer uma classe `ClaudeChatAdapter` implementando a mesma interface de `SkyChat` para integração transparente.

#### Cenário: Adapter recebe mensagem do usuário
- **QUANDO** usuário envia mensagem via `ChatMessage(role="user", content="...")`
- **ENTÃO** adapter armazena mensagem no histórico
- **E** adapter processa mensagem para oportunidades de aprendizado

#### Cenário: Adapter gera resposta
- **QUANDO** `respond(message)` é chamado
- **ENTÃO** adapter recupera memória relevante via RAG
- **E** adapter constrói system prompt com personalidade + contexto de memória
- **E** adapter chama Claude Agent SDK
- **E** adapter retorna resposta gerada
- **E** adapter armazena resposta no histórico

#### Cenário: Compatibilidade de interface do adapter
- **QUANDO** código espera interface `SkyChat`
- **ENTÃO** `ClaudeChatAdapter` pode ser usado como substituto direto
- **E** métodos `receive()` e `respond()` funcionam de forma idêntica

---

### Requirement: Integração de memória com contexto Claude

O sistema DEVERÁ injetar memória relevante do RAG na janela de contexto do Claude para cada geração de resposta.

#### Cenário: Memória recuperada e injetada
- **QUANDO** usuário faz uma pergunta
- **ENTÃO** sistema busca memória RAG com a query do usuário
- **E** top 5 memórias mais relevantes são recuperadas
- **E** memórias são formatadas no system prompt
- **E** Claude usa memórias para informar resposta

#### Cenário: Nenhuma memória relevante encontrada
- **QUANDO** nenhuma memória atinge o threshold de busca (0.6)
- **ENTÃO** system prompt indica "(nenhuma memória relevante)"
- **E** Claude responde baseado apenas em conhecimento geral
- **E** Claude não alucina fatos

#### Cenário: Resultados de memória exibidos na UI
- **QUANDO** memórias são recuperadas para resposta
- **ENTÃO** UI exibe quantidade de memórias usadas
- **E** UI mostra breve preview do conteúdo da memória
- **E** exibição é estilizada com Rich (texto dimmed)

---

### Requirement: Configuração de modelo Claude

O sistema DEVERÁ permitir configuração do modelo Claude via variável de ambiente.

#### Cenário: Modelo padrão é haiku
- **QUANDO** variável de ambiente `CLAUDE_MODEL` não está definida
- **ENTÃO** sistema usa `claude-3-haiku-20240307` como modelo padrão
- **E** modelo é escolhido por baixa latência e eficiência de custo

#### Cenário: Modelo customizado via ambiente
- **QUANDO** variável de ambiente `CLAUDE_MODEL` é definida com nome de modelo válido
- **ENTÃO** sistema usa modelo especificado para todas as respostas do chat
- **E** nome do modelo é registrado nas métricas de observabilidade

#### Cenário: Nome de modelo inválido
- **QUANDO** variável de ambiente `CLAUDE_MODEL` contém nome de modelo inválido
- **ENTÃO** sistema registra erro e volta para modelo padrão
- **E** usuário é notificado do fallback

---

### Requirement: Gerenciamento de tokens para controle de custo

O sistema DEVERÁ limitar tokens de resposta para controlar custos de API.

#### Cenário: Limite de tokens de resposta enforceado
- **QUANDO** gerando resposta via Claude SDK
- **ENTÃO** sistema define `max_tokens=500` (aproximadamente 300-400 palavras)
- **E** respostas são concisas mas completas
- **E** respostas mais longas são automaticamente truncadas

#### Cenário: Monitoramento de tokens de entrada
- **QUANDO** enviando requisição para Claude SDK
- **ENTÃO** sistema registra total de tokens de entrada (prompt + contexto de memória)
- **E** se entrada excede 4000 tokens, sistema reduz contexto de memória
- **E** sistema prioriza memórias mais relevantes

---

> "A integração perfeita é aquela que você nem percebe" – made by Sky 🚀
