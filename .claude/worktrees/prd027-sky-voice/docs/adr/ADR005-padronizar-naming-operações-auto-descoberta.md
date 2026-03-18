---
status: aceito
data: 2025-12-25
---

# ADR005 — Padronizar naming de operações e auto-descoberta com OpenAPI

**Status:** Aceito

**Data:** 2025-12-25

## Contexto

Com a adoção do Sky-RPC (ADR010), o sistema passa a depender do **nome da operação** (`method`) como chave central de roteamento, observabilidade e documentação.

Hoje há inconsistências de naming (ex.: `fileops_read` vs `fileops.read`) e o registro de handlers ainda depende de etapas manuais (bootstrap/routes), o que aumenta drift entre código e documentação.

## Decisão

1. **Padronizar o identificador canônico de operação** no formato `context.action` (separação por ponto), por exemplo:

* `health`
* `fileops.read`
* `fileops.write`
* `tasks.create`

2. Adotar **registry + decorators + auto-descoberta** como mecanismo oficial de registro:

* Decorators `@query(...)` e `@command(...)` (ou `@rpc_method(...)` com `kind`) registram o handler e metadata no registry.
* O bootstrap executa **discovery controlado por configuração** (lista explícita de pacotes) e importa módulos de handlers.

3. Adotar **OpenAPI como documentação canônica de operações**, publicada em `GET /openapi`.

* O contrato Sky-RPC expõe catálogo via OpenAPI (ADR010).

## Regras (Invariantes)

* **Naming:** `method` deve ser estável e único; é proibido snake_case em `method`.
* **Colisão:** colisões de `method` causam falha no startup (erro explícito).
* **Discovery determinístico:** somente pacotes listados em config são varridos/importados.
* **Idempotência de discovery:** importar/discover duas vezes não duplica registros.
* **Metadata mínima por operação:** `method`, `kind (query|command)`, `description`, `tags`, `auth`, `input_schema`, `output_schema`.

## Alternativas Consideradas

1. Registro manual no bootstrap (atual)

   * Rejeitada: aumenta drift e esforço conforme cresce.

2. Rotas HTTP geradas por handler (sem JSON-RPC)

   * Não elimina o problema de naming e não padroniza documentação por método.

3. Discovery amplo (importar tudo recursivo sem filtro)

   * Rejeitada: aumenta risco de side effects e reduz previsibilidade.

## Consequências

### Positivas

* Um único “nome canônico” destrava: docs, métricas, auth, plugins.
* Operações passam a ser **auto-documentadas** via OpenAPI.
* Adicionar endpoint vira: “criar handler + decorar” (sem mexer em rotas).

### Negativas / Trade-offs

* Discovery exige disciplina: handlers devem ficar em módulos dedicados (convenção) para reduzir side effects.
* OpenAPI vira fonte de verdade; o runtime deve estar alinhado ao contrato.

## DoD (Fase 1)

* Nenhuma operação registrada com underscore (`*_read`) — tudo em `context.action`.
* `GET /openapi` retorna o documento OpenAPI contendo ao menos: `health` e `fileops.read`.
* Discovery roda a partir de config e registra handlers sem intervenção manual.

## Convenções Recomendadas

* Módulo padrão de handlers por contexto: `skybridge.core.contexts.<ctx>.delivery.handlers`.
* Namespaces de plugins devem prefixar `method` (ex.: `pluginX.action`) para evitar colisões.

> "Nome canônico é alavanca: tudo passa a encaixar." – made by Sky ✨
