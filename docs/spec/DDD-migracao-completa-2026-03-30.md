# Migração DDD Completa - Discord MCP (2026-03-30)

## Resumo

Migração COMPLETA de todos os MCP tools da estrutura antiga (`tools/`) para a arquitetura DDD (`presentation/tools/`), conforme definido em SPEC010.

## Mudança Principal

### Antes (Estrutura Mista)
```python
# server.py importava de lugares DIFERENTES
from .tools import (reply, fetch_messages, ...)  # ESTRUTURA ANTIGA
from .presentation.tools.send_buttons import handle_send_buttons  # DDD
```

### Depois (Estrutura Unificada DDD)
```python
# server.py importa TUDO de presentation/tools
from .presentation.tools import TOOL_HANDLERS, get_tool_definitions
```

## Arquivos Removidos

```
src/core/discord/tools/*.py  ← TODOS removidos
├── __init__.py
├── reply.py
├── fetch_messages.py
├── react.py
├── edit_message.py
├── download_attachment.py
├── create_thread.py
├── list_threads.py
├── archive_thread.py
├── rename_thread.py
├── send_buttons.py
├── send_embed.py
├── send_menu.py
└── send_progress.py
```

**Substituído por:** `src/core/discord/presentation/tools/*.py`

## Assinatura de Handlers

### Antes (Pydantic + Client)
```python
async def handle_reply(client: discord.Client, args: dict) -> SendReplyOutput:
    ...
    return SendReplyOutput(message_id=..., status=...)
```

### Depois (Dict + DiscordService)
```python
async def handle_reply(discord_service: DiscordService, args: dict) -> dict:
    ...
    return {"message_id": ..., "status": ...}
```

## call_tool Simplificado

### Antes
```python
# Decidia entre DDD e antigo
ddd_handlers = {"send_buttons"}
if name in ddd_handlers:
    result = await handler(self._discord_service, arguments)
else:
    result = await handler(self.discord_client, arguments)

# Tratava retorno diferente
if isinstance(result, dict):
    return json.dumps(result)
else:
    return result.model_dump_json()
```

### Depois
```python
# TODO usa DiscordService
result = await handler(self._discord_service, arguments)

# TODO retornam dict
import json
return [TextContent(type="text", text=json.dumps(result))]
```

## Arquitetura Final

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code (MCP Client)                │
└──────────────────────────────┬──────────────────────────────┘
                               │ MCP Protocol
                               ↓
┌─────────────────────────────────────────────────────────────┐
│  server.py (DiscordMCPServer)                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ @mcp_server.call_tool()                             │   │
│  │   → handler(discord_service, arguments)             │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────┐
│  presentation/tools/*.py (MCP Tool Handlers)                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ handle_reply(discord_service, args) → dict          │   │
│  │ handle_send_buttons(discord_service, args) → dict    │   │
│  │ ... (14 tools)                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────┐
│  application/services/discord_service.py (Fachada)           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ send_message(), send_embed(), send_buttons()        │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────┐
│  discord.py Client (Infrastructure)                         │
└─────────────────────────────────────────────────────────────┘
```

## Lista de Tools Migrados

| Tool | Presentation Handler | DiscordService Method |
|------|---------------------|----------------------|
| reply | handle_reply | send_message |
| fetch_messages | handle_fetch_messages | - |
| react | handle_react | add_reaction |
| edit_message | handle_edit_message | edit_message |
| download_attachment | handle_download_attachment | - |
| create_thread | handle_create_thread | - |
| list_threads | handle_list_threads | - |
| archive_thread | handle_archive_thread | - |
| rename_thread | handle_rename_thread | - |
| send_buttons | handle_send_buttons | send_buttons |
| send_embed | handle_send_embed | send_embed |
| send_menu | handle_send_menu | - |
| send_progress | handle_send_progress | send_progress |

## Estrutura de Pastas Final

```
src/core/discord/
├── domain/                    # Domain Layer
│   ├── events/
│   │   └── button_clicked.py
│   └── value_objects/
│       └── channel_id.py
│
├── application/               # Application Layer
│   ├── commands/
│   │   └── handle_button_click.py
│   ├── handlers/
│   │   └── button_click_handler.py
│   └── services/
│       ├── discord_service.py      ← Fachada principal
│       └── event_publisher.py
│
├── infrastructure/            # Infrastructure Layer
│   └── mcp_button_adapter.py
│
├── presentation/              # Presentation Layer
│   └── tools/                 ← TODOS os MCP tools (14)
│       ├── reply.py
│       ├── send_buttons.py
│       └── ... (12 mais)
│
├── tools/                     ← REMOVIDO (apenas README.md)
│   └── README.md              ← Documento de migração
│
├── client.py
├── access.py
├── server.py                  ← MCP Server (usa presentation)
└── __main__.py
```

## Benefícios da Migração

1. **Unidade:** Todos os tools seguem o mesmo padrão
2. **Testabilidade:** DiscordService pode ser mockado
3. **Separação:** Presentation não conhece discord.py diretamente
4. **Manutenibilidade:** Mudanças no Discord ficam isoladas em DiscordService
5. **DDD Compliance:** Segue SPEC010 rigorosamente

## Correções Implementadas (Histórico)

| # | Correção | Arquivo | Status |
|---|----------|---------|--------|
| 1 | HandleButtonClickCommand.from_discord_interaction | application/commands/handle_button_click.py | ✅ |
| 2 | server.py usar presentation/tools | server.py | ✅ |
| 3 | DiscordService.create_view com callbacks | application/services/discord_service.py | ✅ |
| 4 | Migrar todos tools para presentation/tools | server.py + tools/ | ✅ |

## Próximos Passos

1. ✅ **Migrar todos tools** - FEITO
2. **Remover tools/ completamente** - Aguardando validação
3. **Testar integração** - Pendente (requer reinício do servidor)
4. **Atualizar SPEC010** - Documentar migração completa

## Como Validar

1. **Reiniciar servidor MCP:**
   ```bash
   # Parar servidor atual (Ctrl+C)
   # Limpar cache
   rm -rf src/core/discord/**/__pycache__
   # Reiniciar
   python -m src.core.discord
   ```

2. **Verificar logs:**
   ```
   [MARCADOR v5 __main__] Carregando __main__.py NOVO
   [MARCADOR v5] Iniciando servidor DDD com handlers ANTES de conectar
   ```

3. **Testar tool:**
   ```python
   # Enviar botões
   await send_buttons(
       chat_id="...",
       title="Teste DDD",
       buttons=[...]
   )
   ```

4. **Verificar notificação MCP:**
   - Clicar no botão
   - Notificação deve chegar em Claude Code

---

> "A melhor arquitetura é aquela que você não precisa pensar duas vezes para modificar." – made by Sky 🏗️
