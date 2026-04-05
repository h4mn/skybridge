# ⚠️ ATENÇÃO: ESTA CHANGE FOI ARQUIVADA INDEVIDAMENTE
## APENAS O LEAD PODE ARQUIVAR UMA CHANGE
## Status: EM PROGRESSO (41/45 tasks - 91%)

---

## 1. DTOs e Estruturas de Dados

- [x] 1.1 Criar `src/core/discord/presentation/tools/dto/forum_dto.py` com DTOs:
  - `ForumPostDTO` — id, title, content, author, tags, created_at
  - `ForumCommentDTO` — id, content, author, created_at
  - `ForumTagDTO` — id, name, emoji, moderated
  - `ForumSettingsDTO` — layout, default_tags, default_sort_order

## 2. Tools MCP de Fórum (Posts/Comentários)

- [x] 2.1 Criar `src/core/discord/presentation/tools/forum_tools.py`
- [x] 2.2 Implementar `list_forum_posts` — listagem com paginação e filtro por tag
- [x] 2.3 Implementar `create_forum_post` — criar post com título, conteúdo e tags
- [x] 2.4 Implementar `get_forum_post` — obter detalhes completos do post
- [x] 2.5 Implementar `add_forum_comment` — adicionar comentário a post
- [x] 2.6 Implementar `list_forum_comments` — listar comentários de um post
- [x] 2.7 Implementar `update_forum_post` — editar post existente (apenas autor)
- [x] 2.8 Implementar `close_forum_post` — fechar post como resolvido

## 3. Tools MCP de Moderação de Fóruns (Guild-Level)

- [x] 3.1 Implementar `create_forum` — criar novo canal de fórum na guild
- [x] 3.2 Implementar `archive_forum` — arquivar canal de fórum
- [x] 3.3 Implementar `delete_forum` — deletar canal (requer confirm=true)
- [x] 3.4 Implementar `update_forum_settings` — configurar tags, layout, permissões

## 4. Application Layer

- [x] 4.1 Adicionar métodos de fórum em `DiscordService`:
  - Posts: `list_forum_posts`, `create_forum_post`, `get_forum_post`, `add_forum_comment`, `list_forum_comments`, `update_forum_post`, `close_forum_post`
  - Moderação: `create_forum`, `archive_forum`, `delete_forum`, `update_forum_settings`

## 5. Integração MCP Server

- [x] 5.1 Registrar novas tools em `src/core/discord/server.py` — adicionar ao `TOOL_HANDLERS`
- [x] 5.2 Atualizar `get_tool_definitions()` para incluir as 11 novas tools (7 posts + 4 moderação)

## 6. Notificações de Fórum

- [x] 6.1 Adicionar handler `on_thread_create()` para detectar criação de posts via Gateway
- [x] 6.2 Adicionar handler `on_raw_message_update()` para detectar comentários
- [x] 6.3 Implementar formatação de notificação no formato `<channel source="discord" chat_id="..." forum_post_id="..." ...>`

## 7. Controle de Acesso

- [x] 7.1 Extender `access.json` schema para suportar `is_forum: boolean` em grupos
- [x] 7.2 Atualizar `gate_group()` em `access.py` para considerar canais de fórum

## 8. Testes

- [x] 8.1 Criar testes unitários para cada tool de fórum
- [x] 8.2 Criar testes de integração com fórum real do PyroPaws
- [x] 8.3 Testar notificações de posts e comentários
- [x] 8.4 Testar moderação de fóruns (criar, arquivar, deletar)

## 9. Documentação

- [x] 9.1 Atualizar `docs/spec/SPEC010-discord-ddd-migration.md` com novas tools
- [x] 9.2 Adicionar exemplos de uso das tools de fórum na documentação
