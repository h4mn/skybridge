## Why

O módulo `src/core/discord` se tornou um componente exportável e reutilizável do projeto Skybridge, mas sua arquitetura atual (Tool-Based com Service Layer) não oferece separação clara de responsabilidades, dificultando testes, manutenção e extensão. Além disso, há necessidade de:

1. **Padrões de UI ricos** - Claude só pode enviar texto bruto; faltam Embeds, Buttons, Progress indicators
2. **Prompts em Português Brasileiro** - Atualmente em inglês, violando preferência do projeto
3. **Integração com Paper Trading** - Paper precisa enviar notificações Discord sem acoplamento

## What Changes

### Discord DDD Migration
- **BREAKING**: Reestruturação completa do módulo `src/core/discord` em 4 camadas DDD
- Novas entidades de domínio: `Message`, `Channel`, `Thread`, `Attachment`
- Value Objects: `MessageContent`, `AccessPolicy`, `ChannelId`, `MessageId`
- Repository Interfaces (Ports) para persistência
- Domain Events para mensageria interna

### UI Components
- Novas tools MCP: `send_embed`, `send_progress`, `send_buttons`, `send_menu`, `update_component`
- Padrões de projeção: DTO Projection, Strategy Pattern, Template Method, Builder
- Matriz de decisão para seleção de componente UI

### Prompts MCP
- Prompts modulares em Português Brasileiro
- Módulos: identidade, contexto, tools_guide, seguranca
- Templates de mensagem reutilizáveis

### Integração Discord + Paper
- Nova camada em `src/core/integrations/discord_paper/`
- Projections: `PortfolioEmbedProjection`, `OrdemButtonsProjection`
- Handlers de integração para orquestrar fluxos Paper → Discord

## Capabilities

### New Capabilities

- `discord-domain`: Entidades, Value Objects, Domain Events e Repository Interfaces do módulo Discord
- `discord-application`: Commands, Queries, Handlers e Application Services do Discord
- `discord-infrastructure`: Adapters (discord.py, MCP), Repository implementations
- `discord-presentation`: MCP Tools, DTOs, Projections, Builders, Templates
- `discord-prompts`: Prompts MCP modulares em Português Brasileiro
- `discord-paper-integration`: Camada de integração entre Paper Trading e Discord

### Modified Capabilities

*(Nenhum - esta é uma migração arquitetural, não alteração de requisitos funcionais)*

## Impact

### Código Afetado
- `src/core/discord/` - Reestruturação completa
- `src/core/integrations/` - Nova pasta de integração
- `src/core/paper/` - Adição de Facade MCP (sem alteração de domínio)

### Dependências
- Sem novas dependências externas (usa discord.py e pydantic existentes)

### APIs
- Tools MCP existentes mantêm assinatura compatível (exceto internalidades)
- Novas tools MCP de UI adicionadas ao servidor

### Sistemas
- Discord MCP Server recebe novos tools e prompts
- Paper Trading pode notificar via Discord através de Integration Layer
