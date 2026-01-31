---
status: aceito
data: 2026-01-31
aprovada_por: usuário
data_aprovacao: 2026-01-31
implementacao: src/runtime/delivery/routes.py
data_implementacao: 2026-01-31
relacionado: PRD022
abolida: ADR010
---

# ADR023 — Padrão de Prefixos para Rotas API e Web

**Status:** ✅ **ACEITO**

**Data:** 2026-01-31
**Data de Aprovação:** 2026-01-31
**Relacionado:** PRD022 (Servidor Unificado)
**Abolida:** ADR010 (Sky-RPC) — **completamente removida**

## Contexto

O Skybridge está em transição de uma arquitetura fragmentada (`apps/api/main.py`, `apps/web/`) para um servidor unificado (`apps.server.main`). Durante essa transição, identificamos inconsistência nos padrões de rotas:

```
ATUAL (inconsistente):
├── /webhooks/jobs           ← Sem prefixo
├── /observability/logs      ← Sem prefixo
├── /metrics                 ← Sem prefixo
├── /api/agents/executions   ← Com prefixo /api/
└── /health                  ← Sem prefixo

FUTURO (PRD022 - Servidor Unificado):
├── /api/*        → FastAPI endpoints
├── /web/assets/* → Static files
└── /web/{path}   → SPA fallback
```

A **ADR010 (Sky-RPC)** foi abolida, removendo completamente o contrato `/ticket`/`/envelope`. Todas as rotas backend agora seguem REST padrão.

## Decisão

**Todas as rotas do Skybridge devem seguir o padrão de prefixos:**

1. **`/api/*`** → **TODAS** as rotas da API FastAPI (backend)
2. **`/web/*`** → Arquivos estáticos do frontend

**IMPORTANTE:** Não existem mais exceções. Sky-RPC foi abolida.

### Padrão de Nomes

| Tipo | Padrão | Exemplos |
|------|--------|----------|
| **Backend API** | `/api/{recurso}` | `/api/agents/executions`, `/api/webhooks/jobs`, `/api/health` |
| **Frontend** | `/web/{path}` | `/web/`, `/web/assets/*` |

## Alternativas Consideradas

### Opção A: Sem prefixo `/api/`

**Padrão:** Todas as rotas direto na raiz (`/agents`, `/webhooks`, etc.)

**Vantagens:**
- ✅ Simples e limpo
- ✅ URLs mais curtas

**Desvantagens:**
- ❌ Conflito com servidor unificado (não distingue backend de frontend)
- ❌ Dificulta migração para PRD022
- ❌ Inconsistente com convenção REST `/api/`

**Decisão:** ❌ **REJEITADA** — não suporta arquitetura unificada

### Opção B: Prefixo `/api/` para tudo (Escolhida)

**Padrão:** Backend com `/api/*`, frontend com `/web/*`

**Vantagens:**
- ✅ Suporta servidor unificado (PRD022)
- ✅ Claridade entre backend e frontend
- ✅ Convenção REST padrão da indústria
- ✅ Prepara para proxy/gateway futuro
- ✅ Simples, sem exceções

**Desvantagens:**
- ⚠️ URLs ligeiramente mais longas
- ⚠️ Requer migração de rotas existentes

**Decisão:** ✅ **ESCOLHIDA** — prepara para futuro e mantém clareza

## Consequências

### Positivas

- **Claridade:** URLs indicam claramente se é backend ou frontend
- **Preparação:** Alinhado com PRD022 (servidor unificado)
- **Padrão:** Segue convenção REST `/api/` amplamente adotada
- **Simplicidade:** Sem exceções, regra única
- **Flexibilidade:** Facilita adicionar proxy/gateway no futuro

### Negativas / Trade-offs

- **Migração:** Rotas existentes precisam ser atualizadas
- **Compatibilidade:** Quebra contratos com clientes usando URLs antigas

## Plano de Migração

### Fase 1: Adicionar `/api/` em rotas backend (2026-01-31)

- [ ] `/webhooks/*` → `/api/webhooks/*`
- [ ] `/observability/*` → `/api/observability/*`
- [ ] `/metrics` → `/api/metrics`
- [ ] `/health` → `/api/health`
- [ ] `/logs/*` → `/api/logs/*`
- [ ] `/agents/*` → `/api/agents/*`
- [ ] `/discover` → `/api/discover`
- [ ] `/openapi` → `/api/openapi`

### Fase 2: Remover rotas Sky-RPC (ABOLIDAS)

- [x] `/ticket` — **ABOLIDA** (remover)
- [x] `/envelope` — **ABOLIDA** (remover)

### Fase 3: Atualizar clientes

- [ ] Frontend WebUI (`apps/web/src/api/endpoints.ts`)
- [ ] Scripts e ferramentas internas
- [ ] Documentação

## Exemplos

### Backend (API)

```python
# ANTES
@router.get("/webhooks/jobs")
@router.get("/agents/executions")
@router.get("/metrics")
@router.get("/health")
@router.get("/openapi")

# DEPOIS
@router.get("/api/webhooks/jobs")
@router.get("/api/agents/executions")
@router.get("/api/metrics")
@router.get("/api/health")
@router.get("/api/openapi")
```

### Frontend (estático)

```python
# Servidor unificado (PRD022)
@router.get("/web/assets/{filepath}")
@router.get("/web/{path:path}")
```

## DoD (Definition of Done)

- [x] ADR aprovada e documentada
- [x] ADR010 marcada como ABOLIDA
- [ ] Rotas backend migradas para `/api/*`
- [ ] Rotas Sky-RPC removidas (`/ticket`, `/envelope`)
- [ ] Frontend atualizado com novos endpoints
- [ ] Documentação atualizada
- [ ] Testes E2E ajustados

## Referências

- [ADR010 — Adoção do Sky-RPC (ABOLIDA)](../adr/ADR010-adotar-sky-rpc.md)
- [PRD022 — Servidor Unificado](../prd/PRD022-servidor-unificado.md)
- [REST API naming conventions](https://restfulapi.net/resource-naming/)

---

> "Prefixos claros hoje evitam confusão amanhã" – made by Sky 🛣️
