## Context

**Estado atual:** O Discord MCP (`src/core/discord/`) suporta mensagens, threads e interações, mas não expõe operações para **Fóruns**. O `discord.py` 2.7.1 já tem suporte completo a fóruns (`ForumChannel`, `ForumTag`, `ForumPost`, `ForumComment`), mas essas funcionalidades não estão expostas como tools MCP.

**Arquitetura existente:**
- Presentation Layer: `src/core/discord/presentation/tools/` — tools MCP atuais
- Application Layer: `DiscordService` — fachada para operações Discord
- Infrastructure Layer: Cliente discord.py via `create_discord_client()`

## Goals / Non-Goals

**Goals:**
- Adicionar 7 novas tools MCP para operações dentro de fóruns (posts, comentários)
- Adicionar 4 novas tools MCP para moderação de fóruns (criar, arquivar, deletar, configurar)
- Suportar notificações push de posts e comentários de fórum
- Integrar controle de acesso via `access.json`

**Non-Goals:**
- Modificar a estrutura DDD existente — apenas adicionar novos tools
- Moderação de usuários (banir, kick) — fora do escopo, use moderação nativa do Discord

## Decisions

**1. Localização das novas tools**
- **Decisão:** Adicionar tools em `src/core/discord/presentation/tools/forum_tools.py`
- **Racional:** Mantém consistência com estrutura DDD atual (cada domínio tem seu arquivo de tools)

**2. DTOs para fórum**
- **Decisão:** Criar DTOs específicos em `src/core/discord/presentation/dto/forum_dto.py`
- **Racional:** Fóruns têm estrutura diferente de mensagens — precisam de `ForumPost`, `ForumComment`, `ForumTag` DTOs

**3. Handler de notificações**
- **Decisão:** Estender `on_message()` para detectar `ForumChannel` e despachar para `handle_forum_post()`
- **Racional:** Reutiliza infraestrutura existente de notificações

**4. Controle de acesso**
- **Decisão:** Estender `access.json` grupos com propriedade `is_forum: boolean`
- **Racional:** Mantém consistência com controle de acesso atual de canais

**5. Moderação de fóruns (guild-level)**
- **Decisão:** Usar `guild.create_forum()` do discord.py para criar fóruns
- **Racional:** API nativa do Discord para criação de canais de fórum
- **Decisão:** `archive_forum` usa `channel.edit(archived=True)`
- **Decisão:** `delete_forum` usa `channel.delete()` com confirmação obrigatória
- **Racional:** Operação destrutiva requer proteção contra acidentes

## Risks / Trade-offs

[Risco] **Rate limiting da API do Discord** → Mitigation: Implementar cache local para listagem de posts

[Risco] **Posts de fórum podem ser muito longos** → Mitigation: Paginação obrigatória em `list_forum_posts`

[Trade-off] **Tags são específicas de cada fórum** → Não podemos padronizar globalmente; cada fórum tem suas próprias tags

[Risco] **Deletar fórum é irreversível** → Mitigation: `delete_forum` requer parâmetro `confirm=true` explícito

[Risco] **Criar fórum usa quota de canais da guild** → Mitigation: Validar limite de canais antes de criar

## Migration Plan

1. Criar `forum_tools.py` com 11 novas tools (7 posts + 4 moderação)
2. Criar `forum_dto.py` com DTOs específicos (incluindo `ForumSettingsDTO`)
3. Estender `DiscordService` com métodos de fórum e moderação
4. Atualizar `server.py` para registrar novas tools
5. Testar com fórum real do PyroPaws — criar, arquivar, deletar

**Rollback:** Remover registro das tools — código antigo continua funcionando
