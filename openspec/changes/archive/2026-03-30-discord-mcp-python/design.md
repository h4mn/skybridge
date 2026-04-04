# Discord MCP Python - Design

## Context

### Estado Atual
O servidor MCP de Discord é um arquivo TypeScript monolítico (`server.ts`, 894 linhas) que roda como plugin oficial do Claude Code. Ele gerencia:
- Conexão com Discord Gateway via `discord.js`
- Controle de acesso via `access.json`
- 5 tools MCP: `reply`, `fetch_messages`, `react`, `edit_message`, `download_attachment`
- Permission relay (experimental)

### Constraints
- Deve manter compatibilidade 100% com MCP protocol (stdio transport)
- `access.json` deve permanecer inalterado para não quebrar o skill `/discord:access`
- O servidor roda como subprocesso do Claude Code via MCP

### Stakeholders
- Claude Code — consumidor principal do MCP server
- Usuários do Discord — interagem via canais configurados
- Skill `/discord:access` — gerencia access.json

---

## Goals / Non-Goals

**Goals:**
- Migrar server.ts para Python modular e testável
- Adicionar funcionalidade de criar threads (`create_thread`)
- Adicionar `list_threads` e `archive_thread` para gestão completa
- Manter 100% de compatibilidade com tools existentes
- Estrutura que permita extensibilidade futura

**Non-Goals:**
- Permission relay (feature experimental, será descontinuado)
- Interface web ou CLI para gerenciamento
- Persistência adicional além de `access.json`
- Suporte a Voice/Video do Discord

---

## Decisions

### D1: Framework Discord → `discord.py`

**Decisão:** Usar `discord.py` (não `nextcord` ou `disnake`)

**Racional:**
- `discord.py` é a biblioteca oficial e mais estável
- Comunidade ativa e documentação extensa
- Suporte nativo a threads via `Thread` objects

**Alternativas consideradas:**
- `nextcord`: fork mais rápido, mas menos documentação
- `disnake`: foco em slashes commands, não necessário aqui

### D2: Estrutura Modular

**Decisão:** Separar em módulos por responsabilidade

```
src/core/discord/
├── __init__.py
├── server.py           # MCP Server + handlers
├── client.py           # Discord client wrapper
├── access.py           # Access control (access.json)
├── models.py           # Pydantic models
├── utils.py            # chunk, safeAttName, etc.
└── tools/
    ├── __init__.py
    ├── reply.py
    ├── fetch_messages.py
    ├── react.py
    ├── edit_message.py
    ├── download_attachment.py
    ├── create_thread.py    ✨ NOVO
    ├── list_threads.py     ✨ NOVO
    └── archive_thread.py   ✨ NOVO
```

**Racional:**
- Cada tool em arquivo próprio → fácil de testar e estender
- Separação clara entre Discord client e MCP server
- Models centralizados para validação consistente

### D3: MCP SDK → `mcp` (oficial)

**Decisão:** Usar o SDK oficial `mcp` para Python

**Racional:**
- Mesmo protocolo do server.ts atual
- Suporte a stdio transport nativo
- Tipagem consistente com TypeScript SDK

### D4: Validação → Pydantic v2

**Decisão:** Usar Pydantic para todos os models de entrada/saída

**Racional:**
- Validação automática de tipos
- Serialização/deserialização consistente
- Mensagens de erro claras para debugging

```python
# models.py
class Access(BaseModel):
    dm_policy: Literal['pairing', 'allowlist', 'disabled'] = 'pairing'
    allow_from: list[str] = Field(default_factory=list)
    groups: dict[str, GroupPolicy] = Field(default_factory=dict)
    pending: dict[str, PendingEntry] = Field(default_factory=dict)
    mention_patterns: list[str] | None = None

class CreateThreadInput(BaseModel):
    channel_id: str
    message_id: str
    name: str
    auto_archive_duration: Literal[60, 1440, 4320, 10080] = 1440

class CreateThreadOutput(BaseModel):
    thread_id: str
    thread_name: str
    parent_channel_id: str
    message_id: str
```

### D5: Threading API → Discord.js ThreadManager

**Decisão:** Implementar 3 tools para gestão completa de threads

**API Discord.py equivalente:**
```python
# create_thread
thread = await message.create_thread(
    name=thread_name,
    auto_archive_duration=1440  # 24h
)

# list_threads
threads = channel.threads  # Active threads

# archive_thread
await thread.edit(archived=True)
```

**Racional:**
- CRUD completo para threads
- Alinha com necessidade de organização de discussões
- Auto-archive duration configurável (1h, 24h, 3d, 7d)

---

## Risks / Trade-offs

### R1: Compatibilidade MCP
**Risk:** Diferenças sutis entre SDK TypeScript e Python podem causar incompatibilidades
**Mitigation:** Testes de integração com Claude Code real antes de deploy

### R2: Performance
**Risk:** Python pode ser mais lento que Node.js para I/O intensivo
**Mitigation:** Discord.py usa asyncio nativo, performance equivalente para este use case

### R3: Discord.py vs discord.js
**Risk:** APIs ligeiramente diferentes entre bibliotecas
**Mitigation:** Mapear equivalências antes de implementar, documentar diferenças

### R4: Migration Path
**Risk:** Quebrar funcionalidade existente durante migração
**Mitigation:**
1. Implementar em paralelo ao server.ts
2. Testar exhaustivamente
3. Trocar apenas quando 100% funcional
4. Manter server.ts como fallback temporário

---

## Migration Plan

### Fase 1: Estrutura Base
1. Criar estrutura de diretórios `src/core/discord/`
2. Implementar `models.py` com Pydantic
3. Implementar `access.py` (leitura/escrita access.json)
4. Implementar `client.py` (Discord client wrapper)

### Fase 2: Tools Existentes
5. Implementar `reply.py`
6. Implementar `fetch_messages.py`
7. Implementar `react.py`
8. Implementar `edit_message.py`
9. Implementar `download_attachment.py`

### Fase 3: Novos Tools
10. Implementar `create_thread.py`
11. Implementar `list_threads.py`
12. Implementar `archive_thread.py`

### Fase 4: Integração
13. Implementar `server.py` (MCP Server)
14. Testes de integração
15. Validar com Claude Code real
16. Trocar plugin oficial → implementação Python

### Rollback Strategy
- Manter server.ts original intacto
- Trocar configuração MCP aponta para novo servidor
- Em caso de problema, reverter configuração

---

## Open Questions

1. **Onde rodará o servidor Python?**
   - Opção A: Como plugin MCP local (mesmo padrão atual)
   - Opção B: Como serviço standalone com HTTP transport
   - **Recomendação:** Opção A para manter compatibilidade

2. **Permission Relay será mantido?**
   - Feature experimental no server.ts
   - **Decisão:** Não migrar, descontinuar

3. **Logging estruturado?**
   - Usar `structlog` ou `logging` padrão?
   - **Recomendação:** `logging` padrão com JSON formatter opcional

---

> "Design é a arte de tornar complexo simples" – made by Sky 🚀
