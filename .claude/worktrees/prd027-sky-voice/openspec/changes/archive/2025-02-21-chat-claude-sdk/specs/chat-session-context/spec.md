# Spec: Contexto de Sessão de Chat

## ADDED Requirements

### Requirement: Histórico de mensagens mantido durante sessão

O sistema DEVERÁ manter histórico de mensagens (usuário e Sky) durante a sessão ativa de chat.

#### Cenário: Mensagem do usuário adicionada ao histórico
- **QUANDO** usuário envia mensagem
- **ENTÃO** mensagem é armazenada no histórico com timestamp
- **E** role é marcado como "user"
- **E** conteúdo é preservado exatamente como enviado

#### Cenário: Resposta da Sky adicionada ao histórico
- **QUANDO** Sky gera resposta
- **ENTÃO** resposta é armazenada no histórico com timestamp
- **E** role é marcada como "sky"
- **E** conteúdo completo é preservado

#### Cenário: Histórico usado para contexto de conversa
- **QUANDO** gerando nova resposta
- **ENTÃO** mensagens anteriores do histórico são incluídas no contexto
- **E** Claude usa contexto para manter coerência conversacional
- **E** referências a mensagens anteriores são compreendidas

---

### Requirement: Limite de histórico para controle de contexto

O sistema DEVERÁ limitar tamanho do histórico para evitar estourar limite de tokens do modelo.

#### Cenário: Histórico limitado às últimas N mensagens
- **QUANDO** histórico excede 20 mensagens (10 turnos)
- **ENTÃO** mensagens mais antigas são removidas do contexto
- **E** apenas últimas 20 mensagens são enviadas para Claude
- **E** usuário é notificado sobre truncamento de contexto

#### Cenário: Mensagens do sistema não contam para limite
- **QUANDO** contando mensagens para limite
- **ENTÃO** apenas mensagens de usuário e Sky são contadas
- **E** mensagens do sistema (thinking, tools) são excluídas da contagem
- **E** contexto conversacional é preservado

#### Cenário: Preservação de contexto importante
- **QUANDO** removendo mensagens antigas por limite
- **ENTÃO** sistema tenta preservar mensagens com informações-chave
- **E** resumo de contexto antigo pode ser incluído se necessário

---

### Requirement: Continuidade de referência na conversa

O sistema DEVERÁ manter capacidade de referenciar mensagens anteriores dentro da sessão.

#### Cenário: Referência a "isso", "aquilo", "lá"
- **QUANDO** usuário usa pronomes demonstrativos
- **ENTÃO** Sky resolve referência baseado no contexto do histórico
- **E** resposta demonstra compreensão do tópico anterior

#### Cenário: Seguimento de pergunta anterior
- **QUANDO** usuário faz pergunta de seguimento ("e então?", "por que?")
- **ENTÃO** Sky identifica tópico da mensagem anterior
- **E** resposta continua naturalmente a partir do contexto

#### Cenário: Multi-turno em tópico complexo
- **QUANDO** conversa explora tópico complexo através de múltiplas trocas
- **ENTÃO** Sky mantém coerência do tópico através das mensagens
- **E** Sky não perde fio da meada mesmo após 5+ turnos

---

### Requirement: Sessão resetada com comando /new

O sistema DEVERÁ permitir resetar sessão limpar histórico.

#### Cenário: Comando /new limpa histórico
- **QUANDO** usuário digita comando "/new" ou "/clear"
- **ENTÃO** histórico de mensagens é limpo
- **E** notificação "Nova sessão iniciada" é exibida
- **E** próxima mensagem inicia contexto novo

#### Cenário: Confirmação antes de limpar
- **QUANDO** histórico contém 5+ mensagens e usuário digita /new
- **ENTÃO** sistema solicita confirmação "Limpar sessão? (s/N)"
- **E** apenas limpa se usuário confirmar com "s" ou "y"

#### Cenário: /cancel cancela /new pendente
- **QUANDO** solicitação de confirmação de /new está ativa
- **ENTÃO** usuário pode digitar /cancel para cancelar operação
- **E** sessão continua intacta sem alterações

---

### Requirement: Persistência de sessão (opcional, futuro)

O sistema DEVERÁ suportar persistência de sessão para retomada posterior (FORA DO ESCOPO desta implementação).

#### Cenário: Sessão salva ao encerrar
- **QUANDO** usuário encerra chat com "sair" ou Ctrl+C
- **ENTÃO** sistema salva histórico em arquivo `.sky_session.json`
- **E** timestamp e metadados são incluídos
- **NOTA**: Este cenário está FORA DO ESCOPO inicial

#### Cenário: Sessão anterior pode ser retomada
- **QUANDO** usuário inicia chat com flag `--resume`
- **ENTÃO** sistema carrega última sessão salva
- **E** histórico é restaurado para continuidade
- **NOTA**: Este cenário está FORA DO ESCOPO inicial

---

### Requirement: Multi-turn memory integration

O sistema DEVERÁ integrar novas memórias aprendidas durante a sessão ao contexto de busca.

#### Cenário: Nova memória fica disponível imediatamente
- **QUANDO** Sky aprende nova informação durante conversa
- **ENTÃO** memória é persistida via `PersistentMemory.learn()`
- **E** memória está disponível para busca nas próximas mensagens
- **E** Sky pode referenciar o que acabou de aprender

#### Cenário: Aprendizado incremental em sessão
- **QUANDO** usuário ensina múltiplos fatos durante sessão
- **ENTÃO** cada fato é armazenado separadamente na memória
- **E** busca RAG recupera fatos relevantes de qualquer momento da sessão
- **E** Sky constrói conhecimento incrementalmente

---

> "O contexto é o que transforma palavras em conversa" – made by Sky 🚀
