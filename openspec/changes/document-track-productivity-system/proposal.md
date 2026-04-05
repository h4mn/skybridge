# Proposal: /track Productivity System

## Why

A skill `/track` foi implementada e otimizada (performance < 30s), mas não possui especificação formal. Este change documenta a arquitetura, componentes e funcionalidades já implementadas como especificação OPSX para manutenção, evolução e conhecimento compartilhado.

**Contexto atual:**
- Skill implementada em `.claude/skills/track/`
- Otimizada de 3-5min → < 30s (via orchestrator.py)
- Sistema de Pomodoro 50+10 com CRUD Toggl completo
- Auto-restart para conflitos Desktop/Chrome implementado

## What Changes

**Documentação (não implementação):**
- Mapear arquitetura existente: orchestrator.py + skill.md + state.json + events.log
- Especificar capabilities implementadas: Toggl CRUD, auto-restart, Pomodoro 50+10
- Documentar edge-cases e padrões de performance
- Criar specs formais para cada capability

**Arquivos a documentar:**
```
.claude/skills/track/
├── orchestrator.py      # Lógica de decisão Python
├── skill.md              # Orquestrador MCP
├── blueprint.md          # Arquitetura viva
├── edge-cases.md         # 10 edge cases documentados
├── data/
│   ├── state.json        # Cache local
│   └── events.log        # Logger de debug
└── Relatórios: baseline, optimization, test-protocol
```

## Capabilities

### New Capabilities

**Cada capability abaixo se tornará `specs/<name>/spec.md`:**

- `toggl-crud`: CRUD completo de time entries no Toggl (Create/Read/Update/Delete)
  - start_timer: Inicia nova entry com projeto, tags, descrição
  - get_current: Verifica timer rodando
  - get_entries: Busca histórico por período
  - stop_timer: Para timer e grava duration
  - update_entry: Modifica descrição, tags

- `auto-restart`: Detecção e correção de conflitos Desktop/Chrome
  - consistency_check: Verifica state vs realidade Toggl
  - auto_restart: Reinicia timer parado inesperadamente
  - event_logging: Registra eventos em events.log

- `pomodoro-scheduler`: Sistema 50+10 (trabalho + pausa)
  - resume_logic: Retoma se break ≥ 10min E trabalho ≥ 50min
  - wait_logic: Aguarda se break não terminou
  - state_tracking: Persiste last_stop, last_duration, last_timer

- `performance-cache`: Cache local para otimização (< 30s)
  - state.json: Evita get_time_entries pesado
  - project_cache: IDs de projetos mapeados
  - context_tracking: Projeto, fase atual

- `productivity-feedback`: Feedback estruturado em intervalos
  - cotas_calculator: 0.625 cotas/hora (100 cotas/mês = salário)
  - rescueTime_integration: (futuro) Score de produtividade

### Modified Capabilities

*None - esta change é puramente documental.*

## Impact

**Sistemas afetados:**
- `.claude/skills/track/` → documentado em `openspec/changes/document-track-productivity-system/`
- `openspec/specs/` → novos specs criados para cada capability
- MCP Toggl: dependência externa já utilizada
- MCP RescueTime: integração futura

**Benefícios:**
- Especificação formal para evolução futura
- Onboarding de novos desenvolvedores
- Base para refatorações e migrações
- Histórico de decisões de arquitetura

**Riscos:**
- Documentação pode ficar desincronizada se código mudar sem atualizar specs
- Mitigação: incluir spec update como passo PR review

---

> "Especificar o que existe é o primeiro passo para evoluir com propósito" – made by Sky [blueprint]
