# Skills Disponíveis - Skybridge

## Skills Instaladas

| Skill | Descrição |
|-------|-----------|
| `track` | Rastreador de produtividade — decision table + inference maps. Edge cases em arquivo separado (`edge-cases.md`). Cache de project IDs em `data/state.json` |
| `discord-interaction` | Criação de bots Discord com componentes interativos (botões, menus, modais), tratamento de interações e UIs orientadas a eventos em Python usando discord.py |
| `utf8-check` | Detecta e diagnostica problemas de acentuação UTF-8 em scripts Python, especialmente para Google Sheets API. Use quando houver erros de encoding, caracteres corrompidos (ç, ã, é aparecendo como símbolos), ou ao trabalhar com dados que contenham acentos portugueses brasileiros. |
| `discord-social` | Comportamento social e etiqueta do Discord MCP. Use ao interagir em canais Discord via MCP para manter tom apropriado, organizar threads, e seguir boas práticas de comunicação. |
| `linear-sync` | Gerencia issues Linear com organização por labels e hierarquia. Use ao criar, atualizar ou buscar issues, organizar roadmap com milestones, ou sincronizar codebase com planejamento. |
| `openspec-*` | Conjunto de skills para gerenciamento de changes OpenSpec (explore, new, continue, verify, archive, etc.) |
| `textual-tui` | Interface TUI baseada em Textual para interações interativas |
| `autogrind` | Trabalho autônomo contínuo em ciclos (Overview→Understand→Plan→Work→Reflect) até stop signal explícito. Genérico — escopo passado como argumento (`/autogrind <escopo>`) |

## Como Usar

As skills são ativadas automaticamente com base em gatilhos contextuais. Por exemplo:

- Mencionar "problemas de encoding" ou "acentos estranhos" → `utf8-check`
- Solicitar criação/exploração de changes → `openspec-*`
- Mencionar "crie issue", "busque issues", "mova SKY-XX", "sincronize roadmap" → `linear-sync`

### /track - Rastreador de Produtividade
**Status**: 🟡 Em desenvolvimento (Spike Fase 1)
**Versão**: 0.1.0
**Arquivo**: `.claude/skills/track/skill.md`

**Especialização**: Rastrear tempo, calcular custo em cotas e feedback de produtividade

**Triggers**:
- Comando: `/track`
- Context: Tarefas, estimativas, Pomodoro, produtividade

**O que faz:**
- CRUD completo Toggl: Create, Read, Update, Delete time_entries
- Menu de opções: Nova, Status, Histórico, Continuar, Finalizar, Deletar, Feedback Pomodoro
- Calcula cotas automaticamente: `tempo × 0.625`
- Integra MCP Toggl (CRUD) + RescueTime (produtividade)
- Feedback em intervalos Pomodoro (5min)

**MCPs Integrados:**
- Toggl: CRUD completo de time_entries
- RescueTime: Consulta produtividade do período

**Benefício:**
Você nunca abre o Toggl. `/track` é sua interface única para gerenciar tempo.

**Roadmap:**
- Fase 1: MVP Core + CRUD Toggl (Spike atual)
- Fase 2: Histórico + Estimativas
- Fase 3: Alpha patterns + Contexto auto

---

### utf8-check - Validação UTF-8
**Status**: 🟢 Operacional
**Versão**: 1.0.0
**Arquivo**: `.claude/skills/utf8-check.skill`

**Especialização**: Detectar e diagnosticar problemas de acentuação UTF-8

**Triggers**:
- Keywords: `encoding`, `acentos estranhos`, `utf8-check`, `caracteres corrompidos`
- Context: Scripts Python com dados em português

**O que faz:**
- Detecta problemas de encoding em scripts Python
- Diagnostica caracteres corrompidos (ç, ã, é → símbolos)
- Valida antes de executar scripts Google Sheets API

---

> "Skills são atalhos para sabedoria consolidada." – made by Sky ⚡
