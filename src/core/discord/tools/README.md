# MIGRAÇÃO DDD COMPLETA (2026-03-30)

## Estrutura Removida

Esta pasta (`src/core/discord/tools/`) foi a estrutura original de MCP tools.
Foi **completamente migrada** para a arquitetura DDD definida em SPEC010.

## Localização Nova

Todos os tools agora estão em:
```
src/core/discord/presentation/tools/
```

## Arquitetura DDD (SPEC010)

```
src/core/discord/
├── domain/           # Domain Layer (Entities, Value Objects, Events)
├── application/      # Application Layer (Commands, Handlers, Services)
├── infrastructure/   # Infrastructure Layer (Adapters, External Integrations)
├── presentation/     # Presentation Layer (MCP Tools)
│   └── tools/        # ← TODOS os MCP tools estão aqui agora
└── server.py         # MCP Server (usa presentation/tools)
```

## Tools Migrados

| Tool | Nova Localização |
|------|-----------------|
| reply | presentation/tools/reply.py |
| fetch_messages | presentation/tools/fetch_messages.py |
| react | presentation/tools/react.py |
| edit_message | presentation/tools/edit_message.py |
| download_attachment | presentation/tools/download_attachment.py |
| create_thread | presentation/tools/create_thread.py |
| list_threads | presentation/tools/list_threads.py |
| archive_thread | presentation/tools/archive_thread.py |
| rename_thread | presentation/tools/rename_thread.py |
| send_buttons | presentation/tools/send_buttons.py |
| send_embed | presentation/tools/send_embed.py |
| send_menu | presentation/tools/send_menu.py |
| send_progress | presentation/tools/send_progress.py |

## Mudanças na Assinatura

### Antes (Client direto)
```python
async def handle_reply(client: discord.Client, args: dict) -> SendReplyOutput:
    ...
```

### Depois (DiscordService - Application Layer)
```python
async def handle_reply(discord_service: DiscordService, args: dict) -> dict:
    ...
```

## Por que a migração?

1. **Separação de responsabilidades:** Presentation layer não conhece implementação do Discord
2. **Testabilidade:** DiscordService pode ser mockado facilmente
3. **Flexibilidade:** Mudanças no discord.py não afetam MCP tools
4. **DDD compliance:** Segue SPEC010 rigorosamente

## DOC Referente

- `docs/spec/SPEC010-discord-ddd-migration.md`
- `docs/spec/DDD-correcoes-implementadas.md`

---

**NOTA:** Esta pasta é mantida temporariamente para referência histórica.
Pode ser removida completamente após validação da migração.

> "Arquitetura é a arte de esconder complexidade, não de expô-la." – made by Sky 🏗️
