## Why

O Discord MCP atual suporta mensagens, threads e interações com botões/menus, mas não expõe operações para **Fóruns** — um recurso importante do Discord para discussões estruturadas. Fóruns permitem criar posts organizados por tags, com sistema de aprovação e melhor estrutura para discussões longas. Adicionar suporte a fóruns possibilita usar essa estrutura no Skybridge.

## What Changes

- **Novas ferramentas MCP** para operações de fórum:
  - `list_forum_posts` — listar posts em um canal de fórum
  - `create_forum_post` — criar novo post com tags
  - `get_forum_post` — obter detalhes de um post específico
  - `add_forum_comment` — adicionar comentário a um post
  - `list_forum_comments` — listar comentários de um post
  - `update_forum_post` — editar post existente
  - `close_forum_post` — fechar/post como resolvido
- **Moderação de fóruns** (guild-level):
  - `create_forum` — criar novo canal de fórum na guild
  - `archive_forum` — arquivar canal de fórum
  - `delete_forum` — deletar canal de fórum
  - `update_forum_settings` — configurar tags, layout, permissões
- **Suporte a notificações** de fórum — posts e comentários chegam como push
- **Integração com access.json** — controle de acesso por fórum

## Capabilities

### New Capabilities
- `discord-forum`: Suporte a Fóruns do Discord no MCP — listar posts, criar, comentar, gerenciar tags

### Modified Capabilities
- Nenhuma — as capacidades existentes de Discord MCP permanecem inalteradas

## Impact

- **Código afetado:** `src/core/discord/` — novas ferramentas MCP na camada de Presentation
- **Dependências:** `discord.py` 2.7.1 já suporta fóruns (`ForumChannel`, `ForumTag`, etc.)
- **MCP:** Novas tools expostas via `list_tools()` e `call_tool()`
- **Configuração:** `access.json` pode estender grupos para incluir fóruns
