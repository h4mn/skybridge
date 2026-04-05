# Inbox - Backlog de Ideias com Linear

## Why

O Skybridge hoje não tem um lugar estruturado para capturar ideias rápidas, inspirações e oportunidades de melhoria que surgem durante conversas, leituras ou work. Ideias se perdem em threads de Discord, notas esparsas ou memória volátil. Um Inbox estruturado permite capturar rápido e processar depois, garantindo que nada valioso seja esquecido.

## What Changes

- **Nova capability**: `inbox-discord-slash` - Discord slash command `/inbox` para capturar ideias
- **Nova capability**: `inbox-claude-code-skill` - Claude Code skill `/inbox` para capturar ideias
- **Nova capability**: `inbox-triage-workflow` - Workflow de triagem semanal usando Linear como storage
- **Novo projeto Linear**: "Inbox" - Backlog de ideias não processadas
- **BREAKING**: Nenhuma - é funcionalidade nova

### Anti-requisitos

- Bugs → Criar diretamente como issue Linear
- Tasks com prazo → Toggl/Kanban
- Ideias sem ação → Archive ou delete

## Capabilities

### New Capabilities

#### `inbox-discord-slash`
Captura rápida de ideias via Discord slash command `/inbox add <título>`. Cada entrada cria uma issue no projeto "Inbox" do Linear com descrição estruturada (fonte, inspiração, ação sugerida, expires em 60 dias). Label `fonte:discord` é aplicado automaticamente.

#### `inbox-claude-code-skill`
Captura rápida de ideias via Claude Code skill `/inbox add <título>`. Cada entrada cria uma issue no projeto "Inbox" do Linear com descrição estruturada (fonte, inspiração, ação sugerida, expires em 60 dias). Label `fonte:claude-code` é aplicado automaticamente. Usa Linear MCP diretamente.

#### `inbox-triage-workflow`
Workflow semanal de processamento de entradas do Inbox. Entradas são movidas ou transformadas:
- **Implementar** → Mover para projeto real ou criar issue com escopo
- **Pesquisar** → Criar doc em `docs/research/` ou reference em `memory/`
- **Arquivar** → Mover para status "Archived"
- **Descartar** → Delete

### Modified Capabilities

- Nenhuma - funcionalidade nova isolada

## Impact

### Código

- **Discord**: Nova tool MCP em `src/core/discord/presentation/tools/inbox.py`
- **Claude Code**: Nova skill em `.claude/skills/inbox/skill.md`

### APIs

- Nenhuma API pública nova (MCP Linear já expõe tudo)

### Dependências

- MCP Discord existente
- MCP Linear (já configurado)

### Sistemas

- **Linear**: Novo projeto "Inbox", status customizado "Inbox Entry", label groups
- **Discord**: Novo comando `/inbox`
- **Claude Code**: Nova skill `/inbox`
