# PRD018 Fase 2: Problemas Encontrados e Próximos Passos

## Contexto

Issue relacionada: #55 - PRD018 Fase 2: Redis/DragonflyDB

Durante a implementação e testes da **Fase 2 do PRD018** (SQLite Job Queue), vários problemas foram identificados e corrigidos. Esta issue documenta os gaps e define próximos passos para chegar à autonomia 40%.

---

## ✅ Problemas Resolvidos (2026-01-22)

### P1: CLAUDE_CODE_PATH não configurado
**Problema:** Agente Claude Code não iniciava porque o caminho não estava configurado.
- **Erro:** `claude` não encontrado como executável
- **Causa:** `CLAUDE_CODE_PATH` não estava no `.env`
- **Solução:** Adicionado `CLAUDE_CODE_PATH=C:\Users\hadst\.local\bin\claude.exe` ao `.env` e `.env.example`
- **Arquivos:** `.env`, `.env.example`

### P2: TrelloEventListener não inicializado
**Problema:** Trello foi desacoplado via Domain Events (ARCH-08), mas o listener não estava ativo.
- **Erro:** Cards não eram criados no Trello ao receber webhooks
- **Causa:** `TrelloEventListener` não era instanciado no bootstrap
- **Solução:** Adicionado inicialização em `src/runtime/bootstrap/app.py`
- **Arquivos:** `src/runtime/bootstrap/app.py`

### P3: WebhookSource Enum serialização
**Problema:** `SQLiteJobQueue` salvava `source` como string, mas código esperava Enum.
- **Erro:** `AttributeError: 'str' object has no attribute 'value'`
- **Causa:** SQLite não preserva tipos Python, precisa converter manualmente
- **Solução:**
  - `dequeue()`: string → `WebhookSource` Enum
  - `get_job()`: string → `WebhookSource` Enum
  - `webhook_worker.py`: usar `str(job.event.source)` em logs
- **Arquivos:** `src/infra/webhooks/adapters/sqlite_job_queue.py`, `src/runtime/background/webhook_worker.py`

---

## ⚠️ Problemas Pendentes

### P4: Limpeza de banco entre execuções de demo
**Impacto:** Demo E2E acumula jobs de execuções anteriores, causando confusão.
- **Solução Proposta:** Adicionar comando `python -m runtime.demos cleanup`
- **Prioridade:** Média

### P5: Recuperação de jobs após restart
**Impacto:** Jobs em "processing" ficam travados se a API reiniciar.
- **Solução Proposta:** Job recovery no startup (marcar como failed se > timeout)
- **Prioridade:** Alta

### P6: Tratamento de erro no agente
**Impacto:** Se agente falhar/travar, job fica preso para sempre.
- **Solução Proposta:** Timeout + kill + marcação automática como failed
- **Prioridade:** Alta

---

## 📊 Status Atual da Fase 2

| Componente | Status | Observações |
|------------|--------|-------------|
| SQLiteJobQueue | ✅ 100% | Implementado e testado |
| JobQueueFactory | ✅ 100% | Suporta sqlite, redis, dragonfly, file |
| WebhookProcessor | ✅ 100% | Integrado com SQLite |
| WebhookWorker | ✅ 95% | Funciona, precisa de P5-P6 |
| TrelloEventListener | ✅ 100% | Desacoplado e ativo |
| Demo E2E | ⚠️ 80% | Funciona, precisa de P4 |
| Autonomia Atual | **40%** | +5% desde Fase 1 |

---

## 🎯 Próximos Passos (Ordem de Prioridade)

### Críticos (Esta Semana)
1. **P5 - Job Recovery:** Implementar recuperação de jobs órfãos no startup
2. **P6 - Agent Timeout:** Adicionar timeout + kill automático
3. **Validar:** Executar demo E2E completa 3x consecutivas sem erros

### Importantes (Próxima Semana)
4. **P4 - Demo Cleanup:** Script de limpeza para demo
5. **Métricas:** Adicionar métricas de recovery/timeout
6. **Testes:** Test suite para cenários de falha

### Desejáveis (Fase 3)
7. **Commit/Push:** Implementar CODE-01 e CODE-02 (ver PRD018)
8. **PR Automation:** Implementar CODE-03 a CODE-06
9. **Dashboard:** Métricas em tempo real

---

## 🔗 Referências

- **PRD018:** `docs/prd/PRD018-roadmap-autonomia-incidente.md`
- **Playbook Fase 2:** `docs/playbook/PB018-Fase2-SQLite.md`
- **Issue #55:** PRD018 Fase 2: Redis/DragonflyDB

---

## Checklist

- [x] P1 resolvido: CLAUDE_CODE_PATH configurado
- [x] P2 resolvido: TrelloEventListener ativo
- [x] P3 resolvido: WebhookSource Enum serialização
- [ ] P4 pendente: Limpeza de banco
- [ ] P5 pendente: Job recovery após restart
- [ ] P6 pendente: Agent timeout + kill
- [ ] Validar: Demo E2E 3x consecutivas sem erros
- [ ] Fase 3: Iniciar implementação (Commit/Push/PR)

---

> "Cada problema resolvido é um degrau a menos na escada da autonomia" – made by Sky 🪜
