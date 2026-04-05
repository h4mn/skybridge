# Mapeamento do server.ts → Python

## Visão Geral

O `server.ts` é um MCP Server (Model Context Protocol) que integra o Discord com o Claude Code.

```
┌─────────────────┐     MCP      ┌─────────────────┐
│   Claude Code   │◄────────────►│  Discord MCP    │
│                 │   (stdio)    │    Server       │
└─────────────────┘              └────────┬────────┘
                                          │
                                          ▼
                                 ┌─────────────────┐
                                 │  Discord.js     │
                                 │  (Gateway API)  │
                                 └─────────────────┘
```

---

## Árvore de Componentes Existentes

```
server.ts (894 linhas)
├── 📦 Imports & Config
│   ├── @modelcontextprotocol/sdk → MCP Server
│   ├── discord.js → Client, GatewayIntentBits, Partials, ChannelType
│   ├── fs, path, os, crypto → File system & utilities
│   └── Config: STATE_DIR, ACCESS_FILE, APPROVED_DIR, ENV_FILE
│
├── 🔐 Access Control (access.json)
│   ├── Access types
│   │   ├── dmPolicy: 'pairing' | 'allowlist' | 'disabled'
│   │   ├── allowFrom: string[] (user IDs)
│   │   ├── groups: Record<channelId, GroupPolicy>
│   │   ├── pending: Record<code, PendingEntry>
│   │   └── mentionPatterns: string[]
│   ├── Functions
│   │   ├── defaultAccess() → Access
│   │   ├── readAccessFile() → Access
│   │   ├── loadAccess() → Access
│   │   ├── saveAccess(a: Access)
│   │   └── pruneExpired(a: Access) → boolean
│   └── Gate functions
│       ├── gate(msg: Message) → GateResult
│       ├── isMentioned(msg, patterns) → boolean
│       └── fetchAllowedChannel(id) → Channel
│
├── 📨 Inbound Message Flow
│   ├── client.on('messageCreate') → handleInbound()
│   ├── handleInbound(msg: Message)
│   │   ├── gate() → check access
│   │   ├── pair mode → reply with code
│   │   ├── permission reply → emit notification
│   │   └── deliver → mcp.notification()
│   └── Notification payload
│       ├── content: message text
│       └── meta: { chat_id, message_id, user, ts, attachments }
│
├── 📤 Outbound Tools (MCP)
│   ├── reply (chat_id, text, reply_to?, files[])
│   │   ├── fetchAllowedChannel()
│   │   ├── chunk() → split long messages
│   │   └── ch.send({ content, files, reply })
│   ├── fetch_messages (channel, limit?)
│   │   └── ch.messages.fetch({ limit })
│   ├── react (chat_id, message_id, emoji)
│   │   └── msg.react(emoji)
│   ├── edit_message (chat_id, message_id, text)
│   │   └── msg.edit(text)
│   └── download_attachment (chat_id, message_id)
│       └── downloadAttachment() → inbox path
│
├── 🔑 Permission Relay (experimental)
│   ├── mcp.notification('permission_request')
│   ├── Button handlers (allow/deny/more)
│   └── Permission reply intercept (yes/no + code)
│
├── 🤖 Discord Client
│   ├── Intents: DirectMessages, Guilds, GuildMessages, MessageContent
│   ├── Partials: Channel (for DMs)
│   └── Events: messageCreate, interactionCreate, ready, error
│
└── 🔧 Utilities
    ├── chunk(text, limit, mode) → string[]
    ├── downloadAttachment(att) → path
    ├── safeAttName(att) → string
    ├── assertSendable(path) → void
    ├── noteSent(id) → track recent sent IDs
    └── checkApprovals() → poll approved/ dir
```

---

## Componentes Necessários para `create_thread`

### 1. Estrutura Python Proposta

```
src/core/discord/
├── __init__.py
├── server.py           # MCP Server principal
├── client.py           # Discord client wrapper
├── access.py           # Access control (access.json)
├── tools/
│   ├── __init__.py
│   ├── reply.py        # reply tool
│   ├── fetch_messages.py
│   ├── react.py
│   ├── edit_message.py
│   ├── download_attachment.py
│   └── create_thread.py   # ✨ NOVO
├── models.py           # Pydantic models (Access, GroupPolicy, etc.)
└── utils.py            # chunk, safeAttName, etc.
```

### 2. API Discord.js para Threads

```typescript
// Criar thread a partir de uma mensagem
const thread = await msg.startThread({
  name: 'Thread Name',
  autoArchiveDuration: 60,  // 60, 1440, 4320, 10080 (minutos)
  reason: 'Optional reason'
});

// Tipos de autoArchiveDuration
// 60   = 1 hora
// 1440 = 24 horas (1 dia)
// 4320 = 3 dias
// 10080 = 7 dias
```

### 3. Tool `create_thread` - Especificação

```python
# tools/create_thread.py

class CreateThreadInput(BaseModel):
    channel_id: str  # Canal onde criar a thread
    message_id: str  # Mensagem base para a thread
    name: str  # Nome da thread
    auto_archive_duration: int = 1440  # minutos (default: 24h)

async def create_thread(
    channel_id: str,
    message_id: str,
    name: str,
    auto_archive_duration: int = 1440
) -> dict:
    """
    Cria uma thread a partir de uma mensagem.

    Returns:
        {
            "thread_id": str,
            "thread_name": str,
            "parent_channel_id": str,
            "message_id": str
        }
    """
```

### 4. Diagrama do Fluxo create_thread

```
┌─────────────────────────────────────────────────────────────┐
│                    CREATE_THREAD FLOW                        │
└─────────────────────────────────────────────────────────────┘

  Claude (via Discord)          MCP Server              Discord API
        │                           │                        │
        │  "Sky, cria thread X"     │                        │
        │──────────────────────────►│                        │
        │                           │                        │
        │                           │  fetchAllowedChannel() │
        │                           │───────────────────────►│
        │                           │◄───────────────────────│
        │                           │      Channel object    │
        │                           │                        │
        │                           │  messages.fetch(id)    │
        │                           │───────────────────────►│
        │                           │◄───────────────────────│
        │                           │      Message object    │
        │                           │                        │
        │                           │  msg.startThread()     │
        │                           │───────────────────────►│
        │                           │◄───────────────────────│
        │                           │      Thread object     │
        │                           │                        │
        │  "Thread criada: {id}"    │                        │
        │◄──────────────────────────│                        │
        │                           │                        │
```

### 5. Mudanças Necessárias no server.ts

```typescript
// Adicionar novo tool no ListToolsRequestSchema
{
  name: 'create_thread',
  description: 'Create a new thread from a message in a Discord channel.',
  inputSchema: {
    type: 'object',
    properties: {
      channel_id: { type: 'string', description: 'Channel ID' },
      message_id: { type: 'string', description: 'Message to thread from' },
      name: { type: 'string', description: 'Thread name' },
      auto_archive_duration: {
        type: 'number',
        enum: [60, 1440, 4320, 10080],
        default: 1440,
        description: 'Auto-archive duration in minutes'
      }
    },
    required: ['channel_id', 'message_id', 'name']
  }
}

// Adicionar handler no CallToolRequestSchema
case 'create_thread': {
  const ch = await fetchAllowedChannel(args.channel_id as string)
  const msg = await ch.messages.fetch(args.message_id as string)
  const thread = await msg.startThread({
    name: args.name as string,
    autoArchiveDuration: args.auto_archive_duration as 60 | 1440 | 4320 | 10080
  })
  return {
    content: [{
      type: 'text',
      text: JSON.stringify({
        thread_id: thread.id,
        thread_name: thread.name,
        parent_channel_id: ch.id,
        message_id: msg.id
      })
    }]
  }
}
```

---

## Dependências Python

```toml
# pyproject.toml
[project.dependencies]
"mcp" = ">=1.0.0"           # MCP SDK for Python
"discord.py" = ">=2.3.0"    # Discord API wrapper
"pydantic" = ">=2.0.0"      # Data validation
"aiofiles" = ">=23.0.0"     # Async file operations
```

---

## Checklist de Migração

- [ ] Estrutura de diretórios Python
- [ ] Models Pydantic (Access, GroupPolicy, PendingEntry)
- [ ] Access control (load/save access.json)
- [ ] Discord client setup (intents, partials)
- [ ] MCP Server setup
- [ ] Tool: reply
- [ ] Tool: fetch_messages
- [ ] Tool: react
- [ ] Tool: edit_message
- [ ] Tool: download_attachment
- [ ] **Tool: create_thread** ✨
- [ ] Inbound message handling
- [ ] Permission relay (opcional)
- [ ] Shutdown handling

---

> "Cada thread é uma nova conversa" – made by Sky 🚀
