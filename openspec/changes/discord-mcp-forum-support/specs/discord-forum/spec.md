# Discord Forum Support

Especificação para suporte a Fóruns do Discord no MCP — listar posts, criar, comentar, gerenciar tags.

## ADDED Requirements

### Requirement: Listar posts de fórum
O sistema SHALL fornecer ferramenta MCP para listar posts em um canal de fórum do Discord, com suporte a paginação e filtros por tags.

#### Scenario: Listagem bem-sucedida
- **WHEN** cliente MCP chama `list_forum_posts` com channel_id válido
- **THEN** sistema retorna lista de posts com id, título, autor, tags, timestamp e status
- **AND** cada post contém informações de tag (id, nome, emoji, moderado)

#### Scenario: Filtro por tag
- **WHEN** cliente MCP chama `list_forum_posts` com tag_id específico
- **THEN** sistema retorna apenas posts com essa tag aplicada

#### Scenario: Paginação
- **WHEN** fórum contém mais de 50 posts
- **THEN** sistema retorna primeiros 50 posts
- **AND** inclui cursor para próxima página

### Requirement: Criar post em fórum
O sistema SHALL fornecer ferramenta MCP para criar novo post em canal de fórum, com título, conteúdo e tags.

#### Scenario: Criação bem-sucedida
- **WHEN** cliente MCP chama `create_forum_post` com channel_id, título, conteúdo e tags válidas
- **THEN** sistema cria novo post no fórum
- **AND** retorna id do post criado, URL e timestamps

#### Scenario: Tags inválidas
- **WHEN** cliente MCP chama `create_forum_post` com tag_id que não existe no fórum
- **THEN** sistema retorna erro com mensagem descrevendo tags disponíveis

### Requirement: Obter detalhes de post
O sistema SHALL fornecer ferramenta MCP para obter detalhes completos de um post específico, incluindo conteúdo e comentários.

#### Scenario: Obtenção bem-sucedida
- **WHEN** cliente MCP chama `get_forum_post` com post_id válido
- **THEN** sistema retorna título, conteúdo, autor, tags, status, timestamps
- **AND** inclui lista de comentários do post

#### Scenario: Post não encontrado
- **WHEN** cliente MCP chama `get_forum_post` com post_id inválido
- **THEN** sistema retorna erro indicando post não encontrado

### Requirement: Adicionar comentário a post
O sistema SHALL fornecer ferramenta MCP para adicionar comentário a um post existente.

#### Scenario: Comentário bem-sucedido
- **WHEN** cliente MCP chama `add_forum_comment` com post_id e conteúdo válidos
- **THEN** sistema adiciona comentário ao post
- **AND** retorna id do comentário criado e timestamp

#### Scenario: Post fechado
- **WHEN** cliente MCP tenta comentar em post fechado/arquivado
- **THEN** sistema retorna erro indicando post não aceita mais comentários

### Requirement: Listar comentários de post
O sistema SHALL fornecer ferramenta MCP para listar comentários de um post específico, com paginação.

#### Scenario: Listagem bem-sucedida
- **WHEN** cliente MCP chama `list_forum_comments` com post_id válido
- **THEN** sistema retorna lista de comentários com id, autor, conteúdo e timestamp
- **AND** ordena do mais recente para o mais antigo

### Requirement: Atualizar post
O sistema SHALL fornecer ferramenta MCP para editar título e conteúdo de post existente (apenas pelo autor).

#### Scenario: Atualização bem-sucedida
- **WHEN** autor do post chama `update_forum_post` com post_id, novo título e/ou conteúdo
- **THEN** sistema atualiza o post
- **AND** retorna timestamp da edição

#### Scenario: Edição por não-autor
- **WHEN** usuário que não é o autor tenta chamar `update_forum_post`
- **THEN** sistema retorna erro indicando falta de permissão

### Requirement: Fechar post como resolvido
O sistema SHALL fornecer ferramenta MCP para fechar post, marcando como resolvido.

#### Scenario: Fechamento bem-sucedido
- **WHEN** cliente MCP chama `close_forum_post` com post_id válido
- **THEN** sistema marca post como fechado/resolvido
- **AND** adiciona tag de "resolvido" se configurada no fórum

### Requirement: Notificações de fórum
O sistema SHALL enviar notificações push MCP quando novos posts ou comentários são criados em fóruns monitorados.

#### Scenario: Notificação de novo post
- **WHEN** usuário cria novo post em fórum com acesso configurado
- **THEN** sistema envia notificação ao canal Claude com dados do post
- **AND** notificação inclui channel_id, post_id, título, autor, tags

#### Scenario: Notificação de novo comentário
- **WHEN** usuário adiciona comentário em post monitorado
- **THEN** sistema envia notificação ao canal Claude com dados do comentário
- **AND** notificação inclui post_id, comment_id, autor, conteúdo

### Requirement: Controle de acesso para fóruns
O sistema SHALL respeitar configurações de acesso do `access.json` para canais de fórum.

#### Scenario: Fórum sem configuração explícita
- **WHEN** fórum não tem entrada em `access.json` grupos
- **THEN** sistema aplica política padrão (drop ou allowlist baseada em configuração global)

#### Scenario: Fórum com tags obrigatórias
- **WHEN** fórum requer tags específicas para criar posts
- **THEN** sistema valida que tags fornecidas correspondem às tags do fórum

### Requirement: Criar canal de fórum
O sistema SHALL fornecer ferramenta MCP para criar novo canal de fórum na guild.

#### Scenario: Criação bem-sucedida
- **WHEN** cliente MCP chama `create_forum` com guild_id, nome e configurações válidas
- **THEN** sistema cria novo canal de fórum
- **AND** retorna channel_id, URL e configurações aplicadas

#### Scenario: Nome duplicado
- **WHEN** cliente MCP chama `create_forum` com nome que já existe na guild
- **THEN** sistema retorna erro indicando nome já em uso

### Requirement: Arquivar canal de fórum
O sistema SHALL fornecer ferramenta MCP para arquivar canal de fórum (torná-lo somente leitura).

#### Scenario: Arquivamento bem-sucedido
- **WHEN** cliente MCP chama `archive_forum` com channel_id válido
- **THEN** sistema arquiva o canal de fórum
- **AND** posts permanecem acessíveis mas não permitem novas interações

#### Scenario: Fórum já arquivado
- **WHEN** cliente MCP chama `archive_forum` em canal já arquivado
- **THEN** sistema retorna sucesso (idempotente)

### Requirement: Deletar canal de fórum
O sistema SHALL fornecer ferramenta MCP para deletar permanentemente canal de fórum.

#### Scenario: Deleção bem-sucedida
- **WHEN** cliente MCP chama `delete_forum` com channel_id e confirm=true
- **THEN** sistema deleta permanentemente o canal de fórum
- **AND** todos os posts e comentários são removidos

#### Scenario: Confirmação obrigatória
- **WHEN** cliente MCP chama `delete_forum` sem confirm=true
- **THEN** sistema retorna erro exigindo confirmação explícita

### Requirement: Atualizar configurações de fórum
O sistema SHALL fornecer ferramenta MCP para configurar tags, layout e permissões de fórum.

#### Scenario: Atualização bem-sucedida
- **WHEN** cliente MCP chama `update_forum_settings` com channel_id e novas configurações
- **THEN** sistema atualiza as configurações do fórum
- **AND** retorna configurações aplicadas

#### Scenario: Adicionar nova tag
- **WHEN** cliente MCP chama `update_forum_settings` para adicionar tag ao fórum
- **THEN** sistema cria nova tag no fórum
- **AND** retorna tag_id, nome, emoji e configurações
