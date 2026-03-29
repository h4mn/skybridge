# Discord MCP Server

Servidor MCP (Model Context Protocol) para integração entre Claude Code e Discord.

## Visão Geral

Este módulo implementa um servidor MCP que permite ao Claude Code interagir com canais do Discord através de tools padronizados.

### Arquitetura de Channel

Este servidor funciona como um **Channel MCP** - um tipo especial de servidor MCP que:

1. **Declara capability `claude/channel`** - Permite que Claude Code registre um listener de notificações
2. **Envia notificações inbound** - Quando mensagens chegam do Discord, elas são encaminhadas para a sessão Claude Code
3. **Recebe commands outbound** - Claude pode responder via tools MCP (reply, react, etc.)

```
Discord API ←→ discord.py ←→ DiscordMCPServer ←→ stdio ←→ Claude Code
                                    ↓
                         notifications/claude/channel
```

### Fluxo de Mensagens

```
[Usuário no Discord]
       ↓
   Discord Gateway (discord.py)
       ↓
   on_message handler
       ↓
   gate() - Access Control
       ↓
   handle_inbound()
       ↓
   send_notification() → JSONRPCMessage → write_stream
       ↓
   Claude Code recebe <channel source="discord" ...>
```

## Estrutura

```
src/core/discord/
├── __init__.py          # Exports do módulo
├── __main__.py          # Entry point (python -m)
├── server.py            # MCP Server + handlers
├── client.py            # Discord client wrapper
├── access.py            # Access control (access.json)
├── models.py            # Modelos Pydantic
├── utils.py             # Utilitários (chunk, download, etc.)
└── tools/
    ├── reply.py             # Enviar mensagens
    ├── fetch_messages.py    # Buscar histórico
    ├── react.py             # Adicionar reações
    ├── edit_message.py      # Editar mensagens
    ├── download_attachment.py # Baixar anexos
    ├── create_thread.py     # Criar threads
    ├── list_threads.py      # Listar threads
    ├── archive_thread.py    # Arquivar threads
    └── rename_thread.py     # Renomear threads
```

## Configuração

### Variáveis de Ambiente

```bash
# Obrigatório
DISCORD_BOT_TOKEN=your_bot_token_here

# Opcional
DISCORD_STATE_DIR=~/.claude/channels/discord  # Diretório de estado
```

### access.json

O controle de acesso é gerenciado via `~/.claude/channels/discord/access.json`:

```json
{
  "dmPolicy": "pairing",     // "pairing" | "allowlist" | "disabled"
  "allowFrom": ["123456789"], // User IDs permitidos para DM
  "groups": {
    "987654321": {            // Channel ID
      "requireMention": true,
      "allowFrom": []
    }
  },
  "pending": {},
  "mentionPatterns": ["@sky", "Sky,"],
  "ackReaction": "✅"
}
```

Use a skill `/discord:access` para gerenciar este arquivo.

## Tools Disponíveis

### Mensagens

| Tool | Descrição |
|------|-----------|
| `reply` | Envia mensagem para canal/thread |
| `fetch_messages` | Recupera histórico de mensagens |
| `react` | Adiciona reação emoji |
| `edit_message` | Edita mensagem do bot |
| `download_attachment` | Baixa anexos para inbox |

### Threads

| Tool | Descrição |
|------|-----------|
| `create_thread` | Cria thread a partir de mensagem |
| `list_threads` | Lista threads ativas |
| `archive_thread` | Arquiva thread |
| `rename_thread` | Renomeia thread |

## Uso

### Iniciar Servidor

```bash
# Via entry point (recomendado para Windows)
python run_discord_mcp.py

# Via módulo Python
python -m src.core.discord

# Ou diretamente
python -m src.core.discord.__main__
```

### Windows e UTF-8

O arquivo `run_discord_mcp.py` inclui correções para encoding UTF-8 no Windows:

```python
# Forçar UTF-8 no Windows
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
```

### Integração MCP

Configure no `.mcp.json`:

```json
{
  "mcpServers": {
    "discord": {
      "command": "python",
      "args": ["-m", "src.core.discord"],
      "env": {
        "DISCORD_BOT_TOKEN": "your_token"
      }
    }
  }
}
```

## Controle de Acesso

### Políticas DM

- **pairing**: Usuários não autorizados recebem código de pareamento
- **allowlist**: Apenas usuários em `allowFrom` podem enviar DMs
- **disabled**: Todas as DMs são ignoradas

### Canais de Grupo

- Canais devem estar em `groups` para serem processados
- `requireMention`: Se true, bot só responde quando mencionado
- `mentionPatterns`: Regex patterns para detectar menções indiretas

## Migração do server.ts

Este módulo substitui o servidor TypeScript (`server.ts`) mantendo 100% de compatibilidade:

1. Mesmo protocolo MCP (stdio transport)
2. Mesmo formato de `access.json`
3. Mesmos tools com mesma assinatura
4. **NOVO**: 3 tools de thread adicionados

### Diferenças

- Implementação Python em vez de TypeScript
- Uso de `discord.py` em vez de `discord.js`
- Estrutura modular (um arquivo por tool)

## Implementação Técnica

### Notificações MCP

O MCP SDK Python não possui método `server.notify()` como o TypeScript. A implementação usa:

```python
# server.py - Classe DiscordMCPServer

async def send_notification(self, method: str, params: dict) -> None:
    """Envia notificação MCP para Claude Code."""
    notification = JSONRPCNotification(
        jsonrpc="2.0",
        method=method,
        params=params,
    )

    # Envelopa em JSONRPCMessage para enviar pelo stream
    message = JSONRPCMessage(notification)
    await self._write_stream.send(message)
```

### Capability Declaration

Para Claude Code registrar o listener de channel, é necessário declarar a capability:

```python
# No método run()
experimental_capabilities = {
    "claude/channel": {},  # Registra listener de notificações
}

await self.mcp_server.run(
    read_stream,
    write_stream,
    self.mcp_server.create_initialization_options(
        experimental_capabilities=experimental_capabilities
    ),
)
```

### Formato da Notificação

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/claude/channel",
  "params": {
    "content": "mensagem do usuário",
    "meta": {
      "chat_id": "1344276935504826408",
      "message_id": "1486555332103897228",
      "user": ".dobrador",
      "user_id": "165531471266840577",
      "ts": "2026-03-26T02:40:10.036000+00:00"
    }
  }
}
```

### Flag de Desenvolvimento

Durante a preview de pesquisa, canais personalizados precisam da flag:

```bash
claude --dangerously-load-development-channels server:discord
```

Onde `server:discord` referencia a entrada no `.mcp.json`.

## Testes

```bash
# Executar todos os testes do módulo
pytest tests/unit/core/discord_mcp/ -v

# Com cobertura
pytest tests/unit/core/discord_mcp/ --cov=src/core/discord --cov-report=html
```

### Cobertura de Testes

| Módulo | Testes | Descrição |
|--------|--------|-----------|
| `test_server.py` | 14 | Gate, inbound, mentions, permission replies |
| `test_download_attachment.py` | 13 | Validação, download, erros |
| `test_access.py` | - | Access control policies |
| `test_models.py` | - | Validação de modelos Pydantic |

### Cenários Testados

- ✅ Menção direta e indireta (mentionPatterns)
- ✅ Reply a mensagem do bot
- ✅ Políticas DM (disabled, pairing, allowlist)
- ✅ Políticas de grupo (requireMention)
- ✅ Interceptação de permission replies
- ✅ Download de anexos com validação de tamanho
- ✅ Typing indicator e ack reaction

## Dependências

- `discord.py` - Cliente Discord
- `mcp` - SDK MCP oficial
- `pydantic` - Validação de dados
- `httpx` - HTTP client para downloads

## Troubleshooting

### Mensagens não chegam na sessão

1. Verifique se a flag `--dangerously-load-development-channels` está sendo usada
2. Verifique se `access.json` tem `dmPolicy: "allowlist"` e seu user ID em `allowFrom`
3. Verifique logs do servidor para erros de notificação

### Erro de encoding no Windows

Use `run_discord_mcp.py` em vez de `-m src.core.discord` para garantir UTF-8.

### Typing indicator aparece mas mensagem não chega

Verifique se `send_notification()` está sendo chamado sem erros nos logs.

---

> "A comunicação é a chave que abre todas as portas" – made by Sky 🚀
