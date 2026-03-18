---
status: substituido
data: 2025-12-25
---

# ADR004 — Adotar JSON-RPC como contrato canônico de transporte

**Status:** Substituída pela ADR010

**Data:** 2025-12-25

## Contexto

Hoje existem divergências entre **código**, **PRDs/SPECs/ADRs** e o **OpenAPI** publicado. O roteamento HTTP CQRS atual exige rotas e registro manual no bootstrap, aumentando boilerplate e risco de drift conforme crescem os contexts e handlers.

Além disso, o naming das operações não está totalmente padronizado (ex.: `fileops_read` vs `fileops.read`), o que dificulta discovery, documentação e observabilidade consistentes.

## Decisão

Adotar **JSON-RPC 2.0** via um endpoint HTTP único `POST endpoint JSON-RPC` como **transporte canônico** para execução de operações (dispatch por `method`, ex.: `fileops.read`).

Durante a transição (Fase 1), os endpoints HTTP CQRS existentes (`/qry/*`, e futuros `/cmd/*`) serão refatorados para responder ao **contrato canônico** que passa a ser o JSON-RPC.

## Alternativas Consideradas

1. **Manter HTTP CQRS por rotas** (um endpoint por handler)

   * Prós: OpenAPI forte por operação.
   * Contras: cresce boilerplate; aumenta drift entre rotas/registry/docs.

2. **RPC custom** (payload próprio em `POST /qry` e `POST /cmd`)

   * Prós: simples e controlável.
   * Contras: reinventa padrão; menos interoperabilidade.

3. **Híbrido: JSON-RPC canônico + façade HTTP gerada**

   * Prós: melhor dos dois mundos (RPC + OpenAPI por operação).
   * Contras: mais manutenção (geração e compat entre transportes).

## Consequências

### Positivas

* Consolida execução por **`method`** e reduz boilerplate de roteamento.
* Facilita auto-descoberta, plugins e clientes inteligentes (CLI/agentes).
* Permite que políticas (auth, observabilidade, compat) sejam definidas **por operação**, independentemente de rota.

### Negativas / Trade-offs

* Semântica HTTP por endpoint (cache/idempotência/status codes por rota) deixa de ser central; as políticas passam a ser **por `method`**.
* OpenAPI passa a documentar principalmente o **transporte** (`endpoint JSON-RPC`), não cada operação individualmente; documentação de operações deve migrar para **OpenRPC**.

## Escopo

* **Inclui:** `POST endpoint JSON-RPC`, dispatch por `method`, validação básica de envelope JSON-RPC, integração com registry.
* **Não inclui (nesta ADR):** regras detalhadas de naming, auto-descoberta, geração de OpenRPC, políticas de compat/breaking changes (tratadas em ADR/Playbook separados).

## DoD (Fase 1)

* `POST endpoint JSON-RPC` funcionando com **2 métodos** mínimos: `health` e `fileops.read`.
* Implementação respeita JSON-RPC 2.0: `result` **ou** `error`, com `id` ecoado quando aplicável.
* Endpoints legados se tornam vermelhos.
* Logs/métricas incluem `method` e `id` (correlação).


> "Padronize o transporte, libere o crescimento." – made by Sky ✨
