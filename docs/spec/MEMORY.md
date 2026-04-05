# MEMORY - Especificações Técnicas

Este arquivo registra o histórico de atividades e decisões relacionadas às especificações técnicas do projeto.

---

## [2026-03-28 10:38] - Sky usando Roo Code via GLM-5

**Tarefa:** Criar especificações técnicas para migração do módulo Discord para arquitetura DDD com padrões de UI.

**Arquivos Criados:**
- `docs/spec/SPEC010-discord-ddd-migration.md` - Migração do Discord para DDD
- `docs/spec/SPEC011-discord-ui-patterns.md` - Padrões de UI Discord
- `docs/spec/SPEC012-discord-prompts.md` - Prompts MCP Discord
- `docs/spec/SPEC013-discord-paper-integration.md` - Integração Discord + Paper Trading

**Resumo das Alterações:**

### SPEC010 - Migração Discord para DDD

Decisão de migrar o módulo `src/core/discord` de Tool-Based Architecture para Domain-Driven Design completo com 4 camadas:

1. **Domain Layer**: Entidades (Message, Channel), Value Objects, Domain Events, Repository Interfaces
2. **Application Layer**: Commands, Queries, Handlers, Application Services
3. **Infrastructure Layer**: Repository Impl, Adapters (discord.py, MCP)
4. **Presentation Layer**: MCP Tools, DTOs

**Motivação**: O módulo se tornou exportável para outras aplicações, justificando arquitetura robusta.

### SPEC011 - Padrões de UI Discord

Definição de padrões de apresentação compatíveis com DDD:

| Padrão | Tool MCP | Uso |
|--------|----------|-----|
| DTO Projection | `send_embed` | Informação estruturada |
| State Machine | `send_buttons` | Confirmações |
| Observer | `send_progress` + `update` | Tempo real |
| Template Method | Múltiplos `send_embed` | Relatórios |
| Conversation Flow | `send_menu` → `send_buttons` | Wizards |

**Abordagem**: Tool-Based UI Selection - Claude escolhe explicitamente qual componente usar.

### SPEC012 - Prompts MCP Discord

Criação de prompts modulares em Português Brasileiro:

```
prompts/
├── identidade.py      # Personalidade e estilo
├── contexto.py        # Continuidade de conversa Discord
├── tools_guide.py     # Guia de seleção de tools
├── seguranca.py       # Regras de segurança
└── templates/         # Templates de mensagens
```

**Idioma**: Português Brasileiro OBRIGATÓRIO em todos os prompts.

### SPEC013 - Integração Discord + Paper Trading

Criação de camada de integração em `src/core/integrations/discord_paper/`:

```
integrations/discord_paper/
├── projections/        # Paper → Discord UI
├── handlers/           # Orquestração de fluxo
└── events/             # Event bridge
```

**Princípio**: Paper não conhece Discord, Discord não conhece Paper. Integration Layer faz a tradução via Projections.

**Cenários cobertos**:
1. Consulta de Portfolio → Embed
2. Criação de Ordem → Buttons (confirmação)
3. Monitoramento de Posição → Progress Live

**Próximos Passos**:
1. Revisar SPECs com time/líder
2. Aprovar SPECs para implementação
3. Criar tarefas de implementação no backlog
4. Priorizar migração em fases (Domain → Application → Infrastructure → Presentation)

---
