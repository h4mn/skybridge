# Inbox - Design

## Context

**Estado atual:**
- Discord MCP já configurado e funcional
- Linear MCP já integrado para issues/projects
- Toggl MCP disponível para time tracking
- Não existe captura estruturada de ideias rápidas

**Restrições:**
- Evitar nova infraestrutura de persistência (zero SQLite/JSON)
- Aproveitar integrações MCP existentes
- Workflow deve ser simples e de baixa fricção

**Stakeholders:**
- Desenvolvedor Skybridge (usuário primário)
- Equipe Skybridge (acesso às ideias capturadas)

## Goals / Non-Goals

**Goals:**
- Capturar ideias em < 10 segundos via Discord ou Claude Code
- Processar entradas semanalmente em sessão focada
- Zero manutenção de infraestrutura de storage
- Interface nativa para visualizar/buscar ideias
- Multi-plataforma: mesmo comando `/inbox` funciona em ambos os ambientes

**Non-Goals:**
- Interface web customizada (Linear UI é suficiente)
- Notificações push de lembrete (uso espontâneo)
- Colaboração multi-usuário no Inbox (uso individual)
- Integração com outros canais além de Discord/Claude Code (MVP)

## Decisions

### D1: Linear como Storage (vs SQLite/JSON)

**Decisão:** Usar Linear issues como armazenamento do Inbox.

**Justificativa:**
- Zero infraestrutura adicional (sem migrations, backups, etc.)
- Interface nativa (web + mobile) já pronta
- Busca e filtros poderosos embutidos
- Comentários para discussão sobre ideias
- Já dependemos do Linear para roadmap

**Alternativas consideradas:**
| Alternativa | Por que não |
|-------------|-------------|
| SQLite | Requer migrations, backup, interface customizada |
| JSON | Escala mal, busca ineficiente, sem interface nativa |
| Notion | Depende de outro serviço, MCP inexistente |
| Dedicated service | Overkill para uso individual |

### D2: Multi-plataforma - Discord e Claude Code (MVP)

**Decisão:** MVP com comando `/inbox add` disponível tanto no Discord quanto no Claude Code.

**Justificativa:**
- Discord já é o canal principal do Skybridge
- Claude Code é onde o desenvolvimento acontece (contexto natural)
- MCP Discord e Linear já configurados e testados
- Baixa fricção em ambos os ambientes
- Mesmo comportamento independentemente do canal

**Alternativas consideradas:**
| Alternativa | Por que não (no MVP) |
|-------------|---------------------|
| Apenas Discord | Perde captura durante sessões de desenvolvimento |
| Apenas Claude Code | Perde captura durante conversas assíncronas |
| CLI separada | Requer abrir terminal, contexto extra |
| Web form | Requer construir UI, hosting |

**Implementação:**
- **Discord**: MCP tool `/inbox` integrado ao Discord MCP
- **Claude Code**: Skill `/inbox` que usa Linear MCP diretamente
- Ambos compartilham mesma lógica de criação de issue

**Futuro:** Web form e mobile widget podem ser adicionados sem mudar arquitetura.

### D3: Descrição Estruturada vs Campos Customizados

**Decisão:** Usar descrição Markdown com campos estruturados (Fonte, Inspiração, Ação, Expires).

**Justificativa:**
- Linear não suporta campos customizados arbitrários
- Descrição Markdown é flexível e legível
- Labels complementam para metadados indexáveis
- Mantém compatibilidade com fluxo padrão do Linear

**Formato padrão:**
```markdown
**Fonte:** Discord #dev-chat
**Inspiração:** Contexto do que motivou

---

**Ação sugerida:** Implementar | Pesquisar | Arquivar | Descartar
**Expires:** YYYY-MM-DD (60 dias)
```

### D4: Triagem Manual dentro do Linear

**Decisão:** Workflow de triagem usando movimentação de issues dentro do Linear UI.

**Justificativa:**
- Linear já suporta drag-and-drop entre projetos
- Familiaridade com interface do Linear
- Não requer construção de UI de triagem
- Comentários naturais para discussão

**Alternativa rejeitada:** Bot de triagem automática
- Requer heurísticas complexas
- Risco de falsos positivos
- Perde valor de reflexão manual

### D5: Label Groups para Categorização

**Decisão:** Criar 3 label groups no Linear:
- `fonte:` (discord, conversa, artigo, twitter, etc.)
- `domínio:` (paper, discord, autokarpa, etc.)
- `ação:` (implementar, pesquisar, arquivar, descartar)

**Justificativa:**
- Labels são nativos do Linear
- Filtros por label são eficientes
- Hierarquia de groups organizada
- Visibilidade imediata na UI

### D6: Status "Inbox Entry" Customizado

**Decisão:** Criar status "Inbox Entry" no workflow do time Skybridge.

**Justificativa:**
- Distingue visualmente entradas não processadas
- Filtros por status são triviais
- Mantém semântica clara no backlog

## Risks / Trade-offs

### R1: [Poluição do Linear] → Mitigação

**Risco:** Issues do Inbox podem poluir o backlog do time.

**Mitigação:**
- Projeto dedicado "Inbox" (não espalhado)
- Status "Inbox Entry" distintivo
- Triagem semanal para limpar acumulado

### R2: [Dependência do Linear] → Mitigação

**Risco:** Se Linear ficar indisponível, Inbox não funciona.

**Mitigação:**
- Discord continua aceitando comandos (fila temporária)
- Requisição é simples (retry se falhar)
- Uso é individual, não crítico

### R3: [Labels Inconsistentes] → Mitigação

**Risco:** Usuário pode criar labels fora do padrão.

**Mitigação:**
- Slash command preenche labels automaticamente
- Label groups restringem opções na UI
- Documentação no proposal

## Migration Plan

### Setup Linear (one-time, manual)

1. Criar projeto "Inbox" no time Skybridge
2. Criar status "Inbox Entry" no workflow
3. Criar label groups: `fonte:`, `domínio:`, `ação:`
4. (Opcional) Criar template "Inbox Entry" para padronizar

### Implementação

**Discord MCP Tool (Fase 2-3):**
1. Criar `src/core/discord/presentation/tools/inbox.py`
2. Registrar tool `/inbox` no Discord MCP (`presentation/tools/__init__.py`)
3. Testar criação de issue via Discord

**Claude Code Skill (Fase 4):**
1. Criar skill `.claude/skills/inbox/skill.md`
2. Implementar handler que usa Linear MCP diretamente
3. Testar criação de issue via Claude Code

**Discord Slash Command Nativo (Fase 8):**
1. Criar `src/core/discord/commands/inbox_slash.py`
2. Criar `src/core/discord/infrastructure/linear_client.py` (GraphQL client)
3. Registrar comando no CommandTree do discord.py
4. Configurar `LINEAR_API_KEY` no `~/.claude/settings.json` ou `.env`
5. Testar comando `/inbox` em canal do Discord

**Comum:**
6. Documentar workflow de triagem
7. Garantir comportamento idêntico em ambos canais

### Rollback

- Remover tool `/inbox` do Discord MCP
- Remover skill `/inbox` do Claude Code
- Remover comando `/inbox` do CommandTree
- Manter issues criadas no Inbox (não há efeitos colaterais)

## Notas de Implementação

### Fase 8 - Slash Command Nativo

**Decisão de Arquitetura:** O Discord bot não tem acesso direto ao Linear MCP (processo separado). Solução: criar cliente GraphQL direto para a API do Linear.

**Arquivos Criados:**
- `src/core/discord/commands/inbox_slash.py` - Handler do comando
- `src/core/discord/infrastructure/linear_client.py` - Cliente GraphQL
- `docs/research/inbox-setup.md` - Guia de configuração

**Configuração Necessária:**
```json
// Adicionar ao ~/.claude/settings.json
{
  "env": {
    "LINEAR_API_KEY": "lin_api_xxxxxxxxxxxx"
  }
}
```

**Alternativa:** `LINEAR_API_KEY=lin_api_xxxxxxxxxxxx` no `.env` do projeto.

**Fluxo:**
```
Discord /inbox → inbox_slash.py → linear_client.py → Linear GraphQL API
```

## Open Questions

1. **Q1:** Automatizar expiração de 60 dias ou lembrete?
   - **Resposta pendente:** Sugestão é lembrete via comment (não auto-delete)

2. **Q2:** Criar issue em outro projeto ou mover na triagem?
   - **Resposta pendente:** Mover preserva histórico, criar nova é mais limpo

3. **Q3:** Integrar com `/track` para tempo de triagem?
   - **Resposta pendente:** Sim, mas manual (`/track inbox-triagem`)
