# Discord MCP Python - Proposal

## Why

O servidor MCP de Discord atual é escrito em TypeScript/Node.js (`server.ts`, 894 linhas), o que cria uma barreira de manutenção em um projeto predominantemente Python. Além disso, o servidor atual **não suporta criar threads** — apenas responder em threads existentes — limitando a capacidade de organização de discussões.

Migrar para Python unifica a stack tecnológica e permite adicionar a funcionalidade de `create_thread`, essencial para organizar conversas por tópico nos canais de trading.

## What Changes

### Migração de Stack
- **REMOVER** `server.ts` (TypeScript/Node.js)
- **ADICIONAR** servidor MCP em Python puro
- **MANTER** compatibilidade total com MCP protocol (stdio transport)
- **MANTER** access.json como fonte de controle de acesso

### Novas Funcionalidades
- **NOVO** Tool `create_thread`: criar threads a partir de mensagens
- **NOVO** Tool `list_threads`: listar threads ativas em um canal
- **NOVO** Tool `archive_thread`: arquivar uma thread

### Refatorações
- Estrutura modular em `src/core/discord/`
- Models Pydantic para validação de tipos
- Separação clara entre client, access, tools e server

## Capabilities

### New Capabilities

- `discord-mcp-server`: Servidor MCP para integração Discord-Claude Code, incluindo controle de acesso, tools de mensagens e gerenciamento de threads
- `discord-thread-manager`: Gerenciamento de threads do Discord (criar, listar, arquivar)

### Modified Capabilities

*Nenhuma capability existente será modificada.* Este é um componente novo.

## Impact

### Código
- **NOVO** `src/core/discord/` — módulo Python completo
- **REMOVE** dependência do plugin Discord oficial (TypeScript)

### Dependências
- `discord.py` >= 2.3.0 — API wrapper para Discord
- `mcp` >= 1.0.0 — MCP SDK para Python
- `pydantic` >= 2.0.0 — Validação de dados

### APIs
- MCP Tools expostos:
  - `reply` (existente)
  - `fetch_messages` (existente)
  - `react` (existente)
  - `edit_message` (existente)
  - `download_attachment` (existente)
  - `create_thread` ✨ **NOVO**
  - `list_threads` ✨ **NOVO**
  - `archive_thread` ✨ **NOVO**

### Configuração
- `~/.claude/channels/discord/access.json` — mantido sem alterações
- `~/.claude/channels/discord/.env` — mantido sem alterações

### Sistemas
- Claude Code — consumidor do MCP server
- Discord Gateway — conexão via discord.py

---

> "Unificar para evoluir" – made by Sky 🚀
