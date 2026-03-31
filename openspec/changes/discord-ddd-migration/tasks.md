# M2: Módulo Integração - Discord DDD Migration

**Milestone:** M2: Módulo Integração: Paper + Discord com Discord UI
**Target:** Semana 3-4 | 2026-04-25
**Change:** `discord-ddd-migration`
**Issue Principal:** SKY-70

---

## ✅ STATUS: ATIVO (Testes)

**Atualizado:** 2026-03-31
**Foco:** Testes (SKY-78) e Cleanup (SKY-79)

### Observações

- **SKY-91** marcada como "Bug Falso Positivo" - método `get_history()` existe e funciona
- **Componentes Discord** 100% funcionais após sessão de debug (2026-03-31)
- **Commit validação:** `f19813b` - fix(discord): componentes interação funcionando

---

## Resumo

| Fase | Tasks | Status |
|------|-------|--------|
| PHASE-1: Estrutura | 3 | ✅ |
| PHASE-2: Domain Layer | 17 | ✅ |
| PHASE-3: Application Layer | 13 | ✅ |
| PHASE-4: Infrastructure Layer | 3 | ✅ |
| PHASE-5: Presentation Layer | 15 | ✅ |
| PHASE-6: Prompts PT-BR | 4 | ✅ |
| PHASE-7: Integration Layer | 3 | ✅ |
| **Total** | **66** | **100%** |

---

## PHASE-1: Estrutura de Pastas DDD

**Issue:** [SKY-71](https://linear.app/skybridge/issue/SKY-71)
**Status:** ✅ Completo

### Tarefas

- [x] 1.1 Criar estrutura de pastas DDD em `src/core/discord/`
- [x] 1.2 Criar pasta `src/core/integrations/discord_paper/`
- [x] 1.3 Mover `models.py` existente para `presentation/dto/legacy_dto.py`

---

## PHASE-2: Domain Layer

**Issue:** [SKY-72](https://linear.app/skybridge/issue/SKY-72)
**Status:** ✅ Completo

### Entidades (4)

- [x] 2.1 `domain/entities/message.py` (Aggregate Root)
- [x] 2.2 `domain/entities/channel.py`
- [x] 2.3 `domain/entities/thread.py`
- [x] 2.4 `domain/entities/attachment.py`

### Value Objects (5)

- [x] 3.1 `domain/value_objects/channel_id.py`
- [x] 3.2 `domain/value_objects/message_id.py`
- [x] 3.3 `domain/value_objects/user_id.py`
- [x] 3.4 `domain/value_objects/message_content.py` com chunking
- [x] 3.5 `domain/value_objects/access_policy.py`

### Services (2)

- [x] 4.1 `domain/services/access_service.py`
- [x] 4.2 `domain/services/message_chunker.py`

### Events (4)

- [x] 5.1 `domain/events/base.py`
- [x] 5.2 `domain/events/message_received.py`
- [x] 5.3 `domain/events/message_sent.py`
- [x] 5.4 `domain/events/button_clicked.py`

### Repositories (2)

- [x] 6.1 `domain/repositories/message_repository.py`
- [x] 6.2 `domain/repositories/channel_repository.py`

---

## PHASE-3: Application Layer

**Issue:** [SKY-73](https://linear.app/skybridge/issue/SKY-73)
**Status:** ✅ Completo

### Commands (9)

- [x] 7.1 `application/commands/send_message_command.py`
- [x] 7.2 `application/commands/send_embed_command.py`
- [x] 7.3 `application/commands/send_buttons_command.py`
- [x] 7.4 `application/commands/send_progress_command.py`
- [x] 7.5 `application/commands/send_menu_command.py`
- [x] 7.6 `application/commands/update_component_command.py`
- [x] 7.7 `application/commands/react_command.py`
- [x] 7.8 `application/commands/edit_message_command.py`
- [x] 7.9 `application/commands/create_thread_command.py`

### Queries (2)

- [x] 8.1 `application/queries/fetch_messages_query.py`
- [x] 8.2 `application/queries/list_threads_query.py`

### Handlers (5)

- [x] 9.1-9.5 Command e Query Handlers

### Services (1)

- [x] 10.1 `application/services/discord_service.py` (fachada)

---

## PHASE-4: Infrastructure Layer

**Issue:** [SKY-74](https://linear.app/skybridge/issue/SKY-74)
**Status:** ✅ Completo

### Persistence

- [x] 11.1 `infrastructure/persistence/access_repository.py` (JSON)

### Adapters

- [x] 12.1 `infrastructure/adapters/discord_adapter.py` (discord.py wrapper)
- [x] 12.2 `infrastructure/adapters/mcp_adapter.py` (MCP Server config)

---

## PHASE-5: Presentation Layer

**Issue:** [SKY-75](https://linear.app/skybridge/issue/SKY-75)
**Status:** ✅ Completo

### Tools Existentes (migrar)

- [x] 13.1 reply.py
- [x] 13.7 fetch_messages.py
- [x] 13.8 react.py
- [x] 13.9 edit_message.py
- [x] 13.10 create_thread.py
- [x] 13.11 list_threads.py
- [x] 13.12 archive_thread.py
- [x] 13.13 rename_thread.py
- [x] 13.14 download_attachment.py

### Novos Tools MCP

- [x] 13.2 send_embed.py
- [x] 13.3 send_progress.py
- [x] 13.4 send_buttons.py
- [x] 13.5 send_menu.py
- [x] 13.6 update_component.py

### DTOs

- [x] 14.1 `presentation/dto/tool_schemas.py`

---

## PHASE-6: Prompts Modulares PT-BR

**Issue:** [SKY-76](https://linear.app/skybridge/issue/SKY-76)
**Status:** ✅ Completo

### Módulos

- [x] 15.1 `prompts/identidade.py` - Personalidade e estilo
- [x] 15.2 `prompts/contexto.py` - Continuidade de conversa
- [x] 15.3 `prompts/tools_guide.py` - Guia de seleção de tools
- [x] 15.4 `prompts/seguranca.py` - Regras de segurança
- [x] 15.5 `prompts/__init__.py` - Consolidado (get_discord_system_prompt)

### Templates

- [x] 16.1 `prompts/templates/saudacao.py`
- [x] 16.2 `prompts/templates/erro.py`
- [x] 16.3 `prompts/templates/progresso.py`

---

## PHASE-7: Integration Layer

**Issue:** [SKY-77](https://linear.app/skybridge/issue/SKY-77)
**Status:** ✅ Completo

### Projections

- [x] 17.1 `integrations/discord_paper/projections/portfolio_projection.py`
- [x] 17.2 `integrations/discord_paper/projections/ordem_projection.py`

### Handlers

- [x] 18.1 `integrations/discord_paper/handlers/portfolio_ui_handler.py`
- [x] 18.2 `integrations/discord_paper/handlers/ordem_ui_handler.py`

---

## Entregáveis

- [x] Módulo Discord reestruturado em 4 camadas DDD
- [x] Novos Tools MCP: send_embed, send_progress, send_buttons, send_menu, update_component
- [x] Prompts modulares em PT-BR
- [x] Integration Layer Paper ↔ Discord desacoplada

---

## Implementação Verificada ✅

### Domain Layer
- ✅ Entities: Message, Channel, Thread, Attachment
- ✅ VOs: ChannelId, MessageId, UserId, MessageContent, AccessPolicy
- ✅ Services: AccessService, MessageChunker
- ✅ Events: MessageReceived, MessageSent, ButtonClicked
- ✅ Repositories: MessageRepository, ChannelRepository (interfaces)

### Application Layer
- ✅ Commands: 9 commands implementados
- ✅ Queries: 2 queries implementadas
- ✅ Handlers: Command/Query handlers implementados
- ✅ Services: DiscordService (fachada com 30 métodos)

### Infrastructure Layer
- ✅ Adapters: DiscordAdapter, MCPAdapter
- ✅ Persistence: AccessRepository (JSON, 21 testes passando)

### Presentation Layer
- ✅ 14 Tools MCP: reply, send_embed, send_buttons, send_progress, send_menu, update_component, fetch_messages, react, edit_message, create_thread, list_threads, archive_thread, rename_thread, download_attachment
- ✅ DTOs: tool_schemas.py com validação Pydantic

### Prompts
- ✅ Módulos: identidade, contexto, tools_guide, segurança
- ✅ Templates: saudação, erro, progresso

### Integration Layer
- ✅ Projections: PortfolioProjection, OrdemProjection
- ✅ Handlers: PortfolioUIHandler, OrdemUIHandler

---

## Links Úteis

- **Milestone:** [M2 no Linear](https://linear.app/skybridge/project/paper-trading-bot-mvp?a=ba299ef4-edde-45da-a441-66d3bb993625)
- **Issue Principal:** [SKY-70](https://linear.app/skybridge/issue/SKY-70)
- **Change Directory:** `openspec/changes/discord-ddd-migration/`

---

> "A arquitetura DDD transforma complexidade em clareza" – made by Sky 🏗️✨
