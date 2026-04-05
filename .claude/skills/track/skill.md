---
name: productivity-track
description: Use when executing /track command to check time tracking status, or when user asks "what am I doing now", or when productivity tracking needs to sync with actual conversation context
---

# Productivity Track

## Action

**0. Verificar status atual Toggl:** `toggl_get_current_entry`
- Retorna `{"running": false}` ou `{"running": true, ...}`

**1. Executar orquestrator:** `python orchestrator.py <comando> --toggl-running <true|false> --optimistic`
- `--optimistic`: Ativa modo optimistic-start (50% mais rápido perceived)
- Passa status real do Toggl para verificação de consistência

**2. Ler JSON output:**
- `action: "report"` → mostra status
- `action: "start"` → chama `toggl_start_timer` com params do JSON
- `action: "start_optimistic"` ⚡ **NOVO** → inicia timer PRIMEIRO, verifica depois
- `action: "wait"` → break não terminou
- `action: "auto_restart"` → timer parou inesperadamente, auto-restart

**3. Atualizar state.json** com resultado do Toggl (se aplicável).

## Workspace ID Otimizado

O `orchestrator.py` retorna `workspace_id: 20989145` e `project_id` mapeado do `PROJECT_CACHE` em todas as ações de start.

**Não chamar `toggl_list_workspaces` nem `toggl_list_projects`** - ambos os IDs já estão disponíveis localmente.

Isso elimina **duas chamadas MCP** no fluxo optimistic-start.

## Optimistic-Start (Modo Rápido)

**Quando usar:** Para resposta perceived mais rápida (50% melhoria).

**Fluxo:**
1. Se `action: "start_optimistic"`:
   - Chamar `toggl_start_timer` **imediatamente** (perceived performance)
   - Se verify_after=true: chamar `toggl_get_current_entry` após
   - Se rollback_on_error=true: parar timer se verify falhar

**Exemplo:**
```bash
python orchestrator.py start --optimistic
# Retorna: {"action": "start_optimistic", "verify_after": true, ...}
```

## Auto-Restart (Conflito Desktop/Chrome)

Quando `action: "auto_restart"`:
1. Mostrar aviso: "⚠️ Timer parado inesperadamente (possível conflito Desktop/Chrome)"
2. Executar `toggl_start_timer` com params do JSON
3. Registrar em `data/events.log` para debug

## Events Log

Formato:
```
2026-04-04T10:53:15Z | auto_restart | Timer parado inesperadamente, reiniciado
2026-04-04T12:26:59Z | stop | Duration: 3000s (50min)
```

Orquestrator usa state.json local (evita get_time_entries pesado).
