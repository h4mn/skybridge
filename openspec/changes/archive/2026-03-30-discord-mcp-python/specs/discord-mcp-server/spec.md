# Discord MCP Server - Specification

## ADDED Requirements

### Requirement: MCP Server expõe tools de mensagens Discord
O sistema SHALL implementar um servidor MCP compatível com o protocolo stdio transport que expõe tools para interação com o Discord.

#### Scenario: Servidor inicia e registra tools
- **WHEN** o servidor MCP é iniciado
- **THEN** os tools `reply`, `fetch_messages`, `react`, `edit_message`, `download_attachment` são registrados

#### Scenario: Servidor conecta ao Discord Gateway
- **WHEN** o token DISCORD_BOT_TOKEN está configurado
- **THEN** o cliente Discord conecta ao Gateway com intents: DirectMessages, Guilds, GuildMessages, MessageContent

---

### Requirement: Controle de acesso via access.json
O sistema SHALL gerenciar acesso usando o arquivo `~/.claude/channels/discord/access.json`.

#### Scenario: DM com usuário allowlisted
- **WHEN** mensagem privada é recebida de usuário em `allowFrom`
- **THEN** mensagem é entregue ao Claude via notificação MCP

#### Scenario: DM com usuário não autorizado em modo pairing
- **WHEN** mensagem privada é recebida de usuário NÃO em `allowFrom` E `dmPolicy` é "pairing"
- **THEN** sistema gera código de pareamento e responde com instruções

#### Scenario: Canal de grupo com menção
- **WHEN** mensagem em canal de grupo é recebida E canal está em `groups` E `requireMention` é true E bot é mencionado
- **THEN** mensagem é entregue ao Claude via notificação MCP

#### Scenario: Canal não configurado
- **WHEN** mensagem é recebida em canal não listado em `groups`
- **THEN** mensagem é ignorada (drop)

---

### Requirement: Tool reply envia mensagens
O sistema SHALL fornecer tool `reply` para enviar mensagens para canais autorizados.

#### Scenario: Resposta simples
- **WHEN** `reply(chat_id, text)` é chamado com canal autorizado
- **THEN** mensagem é enviada para o canal Discord

#### Scenario: Resposta em thread
- **WHEN** `reply(chat_id, text, reply_to=message_id)` é chamado
- **THEN** mensagem é enviada como resposta/thread à mensagem especificada

#### Scenario: Resposta com anexos
- **WHEN** `reply(chat_id, text, files=["/path/file.png"])` é chamado
- **THEN** mensagem é enviada com anexos (máximo 10 arquivos, 25MB cada)

#### Scenario: Canal não autorizado
- **WHEN** `reply` é chamado com canal não autorizado
- **THEN** erro é retornado indicando canal não allowlisted

---

### Requirement: Tool fetch_messages recupera histórico
O sistema SHALL fornecer tool `fetch_messages` para recuperar histórico de mensagens.

#### Scenario: Busca com limite padrão
- **WHEN** `fetch_messages(channel)` é chamado
- **THEN** últimas 20 mensagens são retornadas em ordem cronológica

#### Scenario: Busca com limite customizado
- **WHEN** `fetch_messages(channel, limit=50)` é chamado
- **THEN** últimas 50 mensagens são retornadas (máximo 100)

---

### Requirement: Tool react adiciona reação
O sistema SHALL fornecer tool `react` para adicionar reações emoji.

#### Scenario: Reação com emoji unicode
- **WHEN** `react(chat_id, message_id, "👍")` é chamado
- **THEN** emoji é adicionado como reação à mensagem

#### Scenario: Reação com emoji customizado
- **WHEN** `react(chat_id, message_id, "<:name:id>")` é chamado
- **THEN** emoji customizado é adicionado como reação

---

### Requirement: Tool edit_message edita mensagem
O sistema SHALL fornecer tool `edit_message` para editar mensagens enviadas pelo bot.

#### Scenario: Edição bem-sucedida
- **WHEN** `edit_message(chat_id, message_id, "novo texto")` é chamado em mensagem do bot
- **THEN** mensagem é editada com novo conteúdo

#### Scenario: Edição de mensagem de outro usuário
- **WHEN** `edit_message` é chamado em mensagem que não é do bot
- **THEN** erro é retornado indicando permissão negada

---

### Requirement: Tool download_attachment baixa anexos
O sistema SHALL fornecer tool `download_attachment` para baixar anexos de mensagens.

#### Scenario: Download de anexo único
- **WHEN** `download_attachment(chat_id, message_id)` é chamado em mensagem com anexo
- **THEN** anexo é baixado para `~/.claude/channels/discord/inbox/` e caminho é retornado

#### Scenario: Anexo muito grande
- **WHEN** anexo excede 25MB
- **THEN** erro é retornado indicando tamanho excedido

---

### Requirement: Suporte a threads herdado
O sistema SHALL reconhecer threads como parte do canal pai para controle de acesso.

#### Scenario: Mensagem em thread
- **WHEN** mensagem é recebida em thread
- **THEN** `parent_channel_id` é usado para lookup em `groups` (não thread_id)

#### Scenario: Resposta em thread
- **WHEN** `reply` é chamado com `chat_id` de uma thread
- **THEN** resposta é enviada dentro da thread

---

### Requirement: Capability declaration para Claude Code
O sistema SHALL declarar capabilities experimentais para integração com Claude Code channels.

#### Scenario: Declaração de claude/channel
- **WHEN** servidor MCP é inicializado
- **THEN** capability experimental `claude/channel` é declarada

#### Scenario: Declaração de claude/channel/permission
- **WHEN** servidor MCP é inicializado
- **THEN** capability experimental `claude/channel/permission` é declarada para permission relay

---

> "Especificação é o contrato do código" – made by Sky 🚀
