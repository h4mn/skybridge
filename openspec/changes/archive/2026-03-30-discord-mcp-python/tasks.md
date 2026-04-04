# Discord MCP Python - Tasks

## 1. Setup e Estrutura Base

- [x] 1.1 Criar estrutura de diretórios `src/core/discord/`
- [x] 1.2 Criar `src/core/discord/__init__.py` com exports
- [x] 1.3 Adicionar dependências ao `pyproject.toml` (discord.py, mcp, pydantic)
- [x] 1.4 Criar `src/core/discord/models.py` com models Pydantic (Access, GroupPolicy, PendingEntry, etc.)

## 2. Access Control

- [x] 2.1 Implementar `src/core/discord/access.py`
- [x] 2.2 Implementar `default_access()` — retorna Access vazio
- [x] 2.3 Implementar `read_access_file()` — lê access.json
- [x] 2.4 Implementar `save_access()` — escreve access.json atomicamente
- [x] 2.5 Implementar `load_access()` — carrega com cache estático opcional
- [x] 2.6 Implementar `prune_expired()` — remove pending expirados
- [x] 2.7 Escrever testes unitários para access.py

## 3. Discord Client Wrapper

- [x] 3.1 Implementar `src/core/discord/client.py`
- [x] 3.2 Configurar Discord client com intents (DirectMessages, Guilds, GuildMessages, MessageContent)
- [x] 3.3 Configurar partials (Channel para DMs)
- [x] 3.4 Implementar `fetch_text_channel()` — busca canal por ID
- [x] 3.5 Implementar `fetch_allowed_channel()` — valida acesso ao canal
- [x] 3.6 Implementar handlers de eventos (ready, error)
- [x] 3.7 Escrever testes unitários para client.py

## 4. Utilities

- [x] 4.1 Implementar `src/core/discord/utils.py`
- [x] 4.2 Implementar `chunk()` — divide texto longo em chunks
- [x] 4.3 Implementar `safe_attachment_name()` — sanitiza nome de anexo
- [x] 4.4 Implementar `assert_sendable()` — valida path de arquivo
- [x] 4.5 Implementar `download_attachment()` — baixa anexo para inbox
- [x] 4.6 Escrever testes unitários para utils.py

## 5. Tools Existentes

### 5.1 Reply Tool
- [x] 5.1.1 Criar `src/core/discord/tools/reply.py`
- [x] 5.1.2 Implementar validação de entrada com Pydantic
- [x] 5.1.3 Implementar lógica de reply com suporte a files e reply_to
- [x] 5.1.4 Escrever testes unitários

### 5.2 Fetch Messages Tool
- [x] 5.2.1 Criar `src/core/discord/tools/fetch_messages.py`
- [x] 5.2.2 Implementar busca de histórico com limite
- [x] 5.2.3 Formatar output com timestamps e attachments
- [x] 5.2.4 Escrever testes unitários

### 5.3 React Tool
- [x] 5.3.1 Criar `src/core/discord/tools/react.py`
- [x] 5.3.2 Implementar adição de emoji reaction
- [x] 5.3.3 Escrever testes unitários

### 5.4 Edit Message Tool
- [x] 5.4.1 Criar `src/core/discord/tools/edit_message.py`
- [x] 5.4.2 Implementar edição de mensagem do bot
- [x] 5.4.3 Escrever testes unitários

### 5.5 Download Attachment Tool
- [x] 5.5.1 Criar `src/core/discord/tools/download_attachment.py`
- [x] 5.5.2 Implementar download de anexos para inbox
- [x] 5.5.3 Validar tamanho máximo (25MB)
- [x] 5.5.4 Escrever testes unitários

## 6. Novos Tools de Thread

### 6.1 Create Thread Tool
- [x] 6.1.1 Criar `src/core/discord/tools/create_thread.py`
- [x] 6.1.2 Implementar model `CreateThreadInput` em models.py
- [x] 6.1.3 Implementar model `CreateThreadOutput` em models.py
- [x] 6.1.4 Implementar `msg.create_thread()` com validação
- [x] 6.1.5 Escrever testes unitários

### 6.2 List Threads Tool
- [x] 6.2.1 Criar `src/core/discord/tools/list_threads.py`
- [x] 6.2.2 Implementar listagem de threads ativas
- [x] 6.2.3 Implementar opção `include_archived`
- [x] 6.2.4 Escrever testes unitários

### 6.3 Archive Thread Tool
- [x] 6.3.1 Criar `src/core/discord/tools/archive_thread.py`
- [x] 6.3.2 Implementar arquivamento de thread
- [x] 6.3.3 Escrever testes unitários

### 6.4 Rename Thread Tool
- [x] 6.4.1 Criar `src/core/discord/tools/rename_thread.py`
- [x] 6.4.2 Implementar renomeação de thread
- [x] 6.4.3 Adicionar models `RenameThreadInput` e `RenameThreadOutput` em models.py
- [x] 6.4.4 Registrar tool no server.py
- [x] 6.4.5 Atualizar documentação

## 7. MCP Server

- [x] 7.1 Criar `src/core/discord/server.py`
- [x] 7.2 Configurar MCP Server com capabilities (tools, claude/channel, claude/channel/permission)
- [x] 7.3 Implementar `ListToolsRequestSchema` handler — registra todos os tools
- [x] 7.4 Implementar `CallToolRequestSchema` handler — despacha para tools
- [x] 7.5 Implementar `handle_inbound()` — processa mensagens recebidas
- [x] 7.6 Implementar `gate()` — controla acesso às mensagens
- [x] 7.7 Implementar `is_mentioned()` — detecta menções ao bot
- [x] 7.8 Implementar `check_approvals()` — poll de aprovações pendentes
- [x] 7.9 Implementar shutdown graceful
- [x] 7.10 Configurar instructions do MCP Server
- [x] 7.11 Escrever testes de integração

## 8. Gate e Mensagens Inbound

- [x] 8.1 Implementar `gate()` — retorna deliver/pair/drop
- [x] 8.2 Implementar `is_mentioned()` — verifica menções e patterns
- [x] 8.3 Implementar `handle_inbound()` — fluxo completo de mensagem
- [x] 8.4 Implementar tratamento de pairing (código de 6 chars)
- [x] 8.5 Implementar typing indicator
- [x] 8.6 Implementar ack reaction
- [x] 8.7 Escrever testes unitários

## 9. Entry Point

- [x] 9.1 Criar entry point `src/core/discord/__main__.py`
- [x] 9.2 Carregar .env com token
- [x] 9.3 Inicializar Discord client
- [x] 9.4 Conectar MCP Server via stdio transport
- [x] 9.5 Login no Discord Gateway

## 10. Testes e Validação

- [x] 10.1 Configurar pytest para módulo discord
- [x] 10.2 Criar fixtures de teste (mock client, mock access)
- [x] 10.3 Testes unitários: access.py (cobertura > 90%)
- [x] 10.4 Testes unitários: tools (cobertura > 90%)
- [x] 10.5 Testes unitários: server.py (cobertura > 80%)
- [x] 10.6 Teste de integração com Claude Code real
- [x] 10.7 Validar compatibilidade com access.json existente

## 11. Documentação

- [x] 11.1 Atualizar README do módulo discord
- [x] 11.2 Documentar configuração (.env, access.json)
- [x] 11.3 Documentar tools disponíveis
- [x] 11.4 Documentar migração do server.ts
- [x] 11.5 Documentar arquitetura de Channel MCP
- [x] 11.6 Documentar implementação de notificações MCP
- [x] 11.7 Documentar troubleshooting

## 12. Deploy

- [x] 12.1 Validar funcionamento em paralelo ao server.ts
- [x] 12.2 Atualizar configuração MCP para apontar para Python
- [x] 12.3 Testar rollout em ambiente de desenvolvimento
- [ ] 12.4 Monitorar logs e erros por 48h
- [x] 12.5 Remover dependência do plugin Discord oficial (opcional)

---

> "Tarefas bem definidas são meio caminho andado" – made by Sky 🚀

## Correções de Regressão (2026-03-30)

**Causa**: A change `discord-ddd-migration-bug` (SKY-70) fez uma refatoração arquitetural completa do módulo Discord para DDD. Durante a migração, 5 regressões foram introduzidas que quebraram funcionalidades implementadas por esta change.

### B1 — `fetch_messages` quebrado: `get_history()` ausente (SKY-91)

**Arquivos**: `presentation/tools/fetch_messages.py`, `application/services/discord_service.py`

O método `discord_service.get_history()` era chamado por `fetch_messages.py` mas nunca foi implementado no `DiscordService`. Além disso, o serializer usava campos de entidades de domínio (`msg.message_id`, `msg.author_name`, `msg.occurred_at`) em vez dos campos reais de `discord.Message` (`msg.id`, `msg.author.name`, `msg.created_at`).

**Correção**:
- Adicionado `DiscordService.get_history(channel_id, limit)` que usa `channel.history()` do discord.py e retorna `List[discord.Message]`
- Corrigido serializer em `fetch_messages.py` para usar campos de `discord.Message`

### B2 — `ImportError` no `mcp_adapter.py`: `ButtonConfig`/`EmbedField` no lugar errado

**Arquivo**: `infrastructure/adapters/mcp_adapter.py`

O adapter importava `ButtonConfig` e `EmbedField` de `domain.value_objects`, mas essas dataclasses estão definidas em `application.services.discord_service`. O módulo explodía no import.

**Correção**:
```python
# Antes
from ...domain.value_objects import ChannelId, ButtonConfig, EmbedField
# Depois
from ...domain.value_objects import ChannelId
from ...application.services.discord_service import ButtonConfig, EmbedField
```

### B3 — `interaction.response.acknowledge()` não existe em discord.py 2.x

**Arquivo**: `server.py`

O handler `on_interaction_create` chamava `interaction.response.acknowledge()` que foi removido no discord.py 2.x. O código caia no `except` e tentava `defer()`, mas a estrutura try/try aninhada era frágil.

**Correção**: Removido `acknowledge()`, usando `defer()` diretamente com um único try/except.

### B4 — `send_message(components=...)` inválido na API do discord.py

**Arquivo**: `application/services/discord_service.py`

O `DiscordService.send_message()` passava `components=` para `channel.send()`, mas a API do discord.py 2.x não aceita esse parâmetro diretamente (espera `view=` do tipo `discord.ui.View`).

**Correção**: Parâmetro `components` removido e substituído por `reply_to` (ver B5).

### B5 — `reply_to` ignorado: quote-reply quebrado

**Arquivos**: `presentation/tools/reply.py`, `application/services/discord_service.py`

A tool `reply` aceitava `reply_to` no schema MCP mas não propagava o parâmetro para o `DiscordService`, e o `DiscordService` também não suportava quote-reply.

**Correção**:
- Adicionado `reply_to: Optional[str] = None` no `DiscordService.send_message()`
- Implementado `discord.MessageReference` quando `reply_to` é fornecido
- Propagado `reply_to=reply_to` no call de `handle_reply()`

---

## Notas de Implementação (2026-03-26)

### Problema Resolvido: Notificações MCP

**Sintoma**: Mensagens chegavam ao servidor Discord, mas não apareciam na sessão Claude Code.

**Causa Raiz**:
1. MCP SDK Python não possui método `server.notify()` como o TypeScript
2. Faltava declarar a capability `claude/channel` nas experimental capabilities

**Solução**:
```python
# DiscordMCPServer.send_notification()
async def send_notification(self, method: str, params: dict) -> None:
    notification = JSONRPCNotification(
        jsonrpc="2.0",
        method=method,
        params=params,
    )
    message = JSONRPCMessage(notification)
    await self._write_stream.send(message)

# No run()
experimental_capabilities = {"claude/channel": {}}
await self.mcp_server.run(
    read_stream, write_stream,
    self.mcp_server.create_initialization_options(
        experimental_capabilities=experimental_capabilities
    ),
)
```

**Resultado**: Canal Discord MCP Python 100% funcional - mensagens inbound e outbound funcionando perfeitamente.
