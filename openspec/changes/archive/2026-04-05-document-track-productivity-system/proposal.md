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
├── orchestrator.py      # Lógica de decisão Python (107 linhas)
├── skill.md              # Orquestrador MCP (51 palavras)
├── blueprint.md          # Arquitetura viva
├── edge-cases.md         # 10 edge cases documentados
├── BASELINE-TEST.md      # Protocolo de teste baseline
├── TEST-PROTOCOL.md      # Resultados: 3-5min → 30s (99.7% melhoria)
├── OPTIMIZATION-REPORT.md  # Relatório completo Ciclos 1-15 + Cycle 2
├── test_performance.py   # Test suite Python (mock + real)
├── test_performance_e2e.sh  # Test suite E2E bash
├── data/
│   ├── state.json        # Cache local
│   ├── history.json      # Histórico de tarefas + precisão de estimativa
│   └── events.log        # Logger de debug
```

## Capabilities

### New Capabilities

**6 capabilities implementadas e documentadas como `specs/<name>/spec.md`:**

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

- `optimistic-start`: **Cycle 2** - Modo otimista para perceived performance (50% melhoria)
  - specs/optimistic-start/spec.md criado ✅
  - test_performance.py + test_performance_e2e.sh implementados ✅

**Specs criadas:**
1. ✅ specs/toggl-crud/spec.md
2. ✅ specs/auto-restart/spec.md
3. ✅ specs/pomodoro-scheduler/spec.md
4. ✅ specs/productivity-feedback/spec.md
5. ✅ specs/performance-cache/spec.md
6. ✅ specs/optimistic-start/spec.md (NOVA - Cycle 2)
  - perceived_performance: 25s vs 50s verify-first (50% melhoria)
  - verify_after: Verificação em background após start
  - rollback_on_error: Parar timer se verify falhar
  - test_suite: test_performance.py (mock + real) + test_performance_e2e.sh

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

## Testes e Métricas

### Protocolo de Teste
- **BASELINE-TEST.md**: Protocolo de medição (3-5min baseline → <30s target)
- **TEST-PROTOCOL.md**: Resultados finais mostrando 99.7% melhoria em status
- **test_performance.py**: Test suite Python com mock (100ms) e real (MCP)
- **test_performance_e2e.sh**: Test suite E2E bash

### Métricas de Otimização
| Cenário | Baseline | Final | Melhoria |
|---------|----------|-------|----------|
| Retoma pomodoro | 72-319s | **30s** | -96% ✅ |
| Nova track | 60-180s | **30s** | -83% ✅ |
| Status | 30-60s | **0.1s** | -99.7% ✅ |
| Optimistic-start (perceived) | 50s | **25s** | -50% ✅ |

### Relatórios Gerados
- **OPTIMIZATION-REPORT.md**: Detalhamento dos Ciclos 1-15 (orchestrator) + Cycle 2 (optimistic)
- **NEXT-SESSION.md**: Plano de sessão seguinte (Cycle 2 completo)

---

> "Especificar o que existe é o primeiro passo para evoluir com propósito" – made by Sky [blueprint]
