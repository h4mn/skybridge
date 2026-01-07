---
status: aceito
data: 2025-12-25
---

# ADR006 — Política de ID, Correlation e Idempotência no JSON-RPC

**Status:** Aceito

**Data:** 2025-12-25

## Contexto

O JSON-RPC 2.0 permite requisições sem `id` (notifications), nas quais o servidor não retorna resposta. Esse comportamento é útil para eventos “fire-and-forget”, porém é perigoso para operações com efeitos colaterais (commands), pois dificulta rastreio, retry seguro e deduplicação.

A Skybridge também utiliza `correlation_id` para observabilidade ponta-a-ponta.

## Decisão

1. **Commands exigem `id`**

* Para qualquer operação marcada como `kind=command`, o campo `id` do JSON-RPC é **obrigatório**.
* Requisição de command sem `id` deve falhar com erro JSON-RPC `-32600 (Invalid Request)`.

2. **Idempotência para commands**

* Para `kind=command`, adotar `idempotency_key` em `params.idempotency_key`.
* Em **produção**, `idempotency_key` é **obrigatória**; em dev pode ser opcional.
* O servidor deve deduplicar commands por `(method, idempotency_key)` e retornar o mesmo resultado para retries.

3. **Queries e notifications**

* Para `kind=query`, `id` é recomendado.
* Notifications (sem `id`) são permitidas apenas para métodos explicitamente marcados como `notification_allowed=true` no registry.
* Por padrão, queries **não** aceitam notification (fail-fast) até haver caso de uso claro.

4. **Correlation**

* O `id` do JSON-RPC é a chave primária de correlação request↔response.
* Para logging/tracing, a Skybridge deve registrar `correlation_id = id` (quando presente).
* Quando `id` estiver ausente (notification), o servidor pode gerar um `correlation_id` interno apenas para logs.

## Alternativas Consideradas

1. Permitir `id` ausente em qualquer método

   * Rejeitada: torna commands inseguros e dificulta debugging.

2. Usar apenas `id` como idempotência

   * Rejeitada: `id` é por chamada; idempotência é por “intenção de comando” e pode precisar sobreviver a replays.

## Consequências

### Positivas

* Commands ficam seguros contra retries e duplicidade.
* Observabilidade consistente (sempre há correlação em commands).
* Regras claras sobre notification evitam bugs sutis.

### Negativas / Trade-offs

* Clientes precisam gerar `id` e `idempotency_key` para commands.
* Exige storage simples para deduplicação (TTL) mesmo no início.

## DoD (Fase 1)

* Registry marca `kind` por método (query/command).
* Dispatcher rejeita command sem `id`.
* Interface de handler/params suporta `idempotency_key` para commands (mesmo antes de Tasks BC).

> "Retries existem; seu contrato precisa sobreviver a eles." – made by Sky ✨
