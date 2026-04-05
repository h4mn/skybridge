# Design: /track Productivity System

## Context

**Estado atual:** Skill `/track` implementada e otimizada em `.claude/skills/track/`, mas sem especificação formal.

**Arquitetura existente:**
```
┌─────────────────────────────────────────────────────────────┐
│                        /track Skill                          │
├─────────────────────────────────────────────────────────────┤
│  Usuário → SKILL.md → orchestrator.py → state.json          │
│                ↓              ↓            ↓                 │
│            MCP Toggl      JSON output   Cache local          │
│                ↓              ↓            ↓                 │
│           Timer CRUD    Decision       Event log            │
└─────────────────────────────────────────────────────────────┘
```

**Componentes implementados:**
- `orchestrator.py` (107 linhas): Lógica de decisão em Python
- `skill.md` (51 palavras): Orquestrador MCP slim
- `state.json`: Cache local com project_ids, context, last_timer
- `events.log`: Logger para debug (timestamp | type | message)
- `blueprint.md`: Arquitetura viva com roadmap
- `edge-cases.md`: 10 edge cases documentados

**Performance:**
| Cenário | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Retoma | 72-319s | 30s | -96% |
| Nova | 60-180s | 30s | -83% |
| Status | 30-60s | 0.1s | -99.7% |

**Stakeholders:**
- Usuário final: Desenvolvedor que usa /track para rastrear produtividade
- Sky (IA): Companheira de desenvolvimento que mantém a skill

## Goals / Non-Goals

**Goals:**
1. Documentar arquitetura existente como especificação formal OPSX
2. Criar specs para cada capability (toggl-crud, auto-restart, pomodoro-scheduler, etc.)
3. Mapear componentes e seus contratos
4. Preservar knowledge para evolução futura

**Non-Goals:**
1. Implementar novas funcionalidades (fora do escopo)
2. Refatorar código existente (apenas documentar)
3. Mudar arquitetura (apenas descrever)

## Decisões

### 1. Orchestrator Python como Fonte de Verdade

**Decisão:** `orchestrator.py` contém a lógica de decisão; `skill.md` é apenas wrapper.

**Racional:**
- Externalizar lógica para Python reduziu overhead LLM de 3-5min → 30s
- Cache local (state.json) evita MCP calls pesados (get_time_entries)
- Testável independente de MCP

**Alternativas consideradas:**
- SKILL.md com toda lógica ❌ (testado: piorou performance para 319s)
- JS/Node orchestrator ❌ (ecossistema Python já estabelecido)

### 2. State.json como Cache Local

**Decisão:** Persistir estado localmente em vez de depender apenas de API Toggl.

**Racional:**
- Performance: < 300ms vs 3-5min
- Disponibilidade: funciona se API Toggl falhar
- Contexto: preserva projeto, fase, cotas entre sessões

**Estrutura:**
```json
{
  "running": bool,
  "last_stop": "ISO timestamp",
  "last_duration": int (segundos),
  "last_timer": {project, tags, description},
  "context": {projeto, fase},
  "project_cache": {nome: id}
}
```

### 3. Auto-Restart com Consistency Check

**Decisão:** Verificar consistência state vs realidade Toggl antes de cada ação.

**Racional:**
- Detecta conflitos Desktop/Chrome que param timer MCP
- Reinicia automaticamente sem intervenção manual
- Event logging para debug futuro

**Fluxo:**
```
1. get_current_entry() → toggl_is_running
2. orchestrator.py start(toggl_is_running=False)
3. consistency_check() detecta: state.running=True mas Toggl=False
4. Retorna {"action": "auto_restart", ...}
5. Log em events.log
```

### 4. Pomodoro 50+10 vs 25+5

**Decisão:** Adotar ciclo de 50min trabalho + 10min pausa para trabalho com IA.

**Racional:**
- Tempo suficiente para contexto + execução + revisão
- IA acelera mas precisa de setup (contexto é caro)
- Menos trocas de contexto = mais deep work

**Heurística:**
> "Com IA no loop, menos ciclos mas mais profundos. 50+10 > 25+5."

### 5. Optimistic Start (NOVO)

**Decisão:** Implementar modo optimistic-start para melhorar perceived performance.

**Racional:**
- Verify-first: 50s (usuário espera tudo)
- Optimistic: 25s perceived (50% mais rápido)
- Usuário vê resposta imediata, verificações em background

**Implementação:**
```python
# Modo otimista
orchestrator.py start --optimistic
→ Retorna {"action": "start_optimistic", "verify_after": True}

# Skill action:
1. toggl_start_timer() imediato (background)
2. Confirma usuário: "Timer iniciado!"
3. Verifica em background (se verify_after=True)
4. Se falhar: rollback (toggl_stop_timer)
```

**Alternativas:**
- Verify-first (atual) ❌ Mais lento mas mais seguro
- Optimistic-start ✅ 50% mais rápido percebido

## Risks / Trade-offs

| Risk | Mitigação |
|------|-----------|
| Docs desincronizadas | Incluir spec update no PR review |
| state.json corrompido | Backup events.log como fonte de verdade |
| API Toggl timeout | Retry + fallback local |
| Conflito Desktop/Chrome | Auto-restart já implementado |
| Pomodoro fixo não funciona para todos | Configurável via state.json |

## Migration Plan

**N/A** - Documentação de sistema existente, sem migração.

## Open Questions

1. **RescueTime integração:** Deve ser implementada como capability separada?
   - Decisão pendente: depende de requisitos do usuário

2. **Webhook Toggl → Skybridge:** Vale o custo de implementação?
   - Alternativa: polling atual via consistency_check

3. **Multi-workspace:** Suporte necessário?
   - Atualmente: DEFAULT_WORKSPACE fixo

---

> "O código é a verdade última, mas a especificação é o contrato" – made by Sky [design]
