---
status: substituido
data: 2025-12-25
---

# PRD004 — PoC JSON-RPC (Fase 1) + Ajustes de Código

## 1) Problema

A Skybridge tem divergências entre **código**, **ADRs/SPECs/PRDs** e **OpenAPI**, além de **boilerplate** e risco de drift por registro/roteamento manual. Após a decisão de adotar JSON-RPC como transporte canônico (ADR004) e padronizar naming `context.action` + discovery + OpenRPC (ADR005), é necessário um corte mínimo implementado e validado em runtime.

## 2) Objetivo

Entregar um **PoC funcional** do transporte **JSON-RPC** com operações mínimas, e realizar os **ajustes no código atual** necessários para alinhar naming/registry/handlers e reduzir divergências.

## 3) Escopo

### Inclui

* Endpoint **`POST endpoint JSON-RPC`** (JSON-RPC 2.0) com dispatch por `method`.
* Operações mínimas expostas via JSON-RPC:

  * `health`
  * `fileops.read`
* Normalização de naming no registry para **`context.action`** (proibir underscore em `method`).
* Integração com registry (handler lookup) usando o mecanismo existente (Result/Envelope), mapeando para JSON-RPC:

  * sucesso -> `result`
  * falha -> `error`
* Manter endpoints atuais (`/qry/*`) funcionando durante a fase 1.
* Testes automatizados para o fluxo JSON-RPC mínimo.

### Não inclui (por enquanto)

* Tasks BC e event sourcing.
* Commands reais (além do esqueleto de roteamento).
* Plugins e permissões completas.
* Substituição total de OpenAPI por OpenRPC.

## 4) Requisitos Funcionais

### RF1 — JSON-RPC endpoint

* Disponibilizar `POST endpoint JSON-RPC`.
* Validar envelope JSON-RPC 2.0:

  * `jsonrpc == "2.0"`
  * `method` obrigatório
  * `id` opcional (quando ausente, tratar como notification: sem response)

### RF2 — Dispatch por method

* Resolver handler via registry com chave `method`.
* Em caso de método desconhecido, retornar erro JSON-RPC `-32601` (Method not found).

### RF3 — Operações mínimas

* `health`: retorna status/uptime/version (mínimo equivalente ao `/qry/health`).
* `fileops.read`: executa a leitura existente e preserva segurança (allowlist).

### RF4 — Naming canônico

* `fileops.read` passa a ser o nome oficial (sem `fileops_read`).
* Startup falha (ou loga erro crítico) se houver registro com underscore em `method`.


## 5) Requisitos Não-Funcionais

* Observabilidade: logs estruturados devem incluir `method` e `id` (correlação).
* Erros: `result` e `error` são mutuamente exclusivos (JSON-RPC).
* Segurança: `fileops.read` mantém validação allowlist antes do acesso ao disco.

## 6) Critérios de Aceite (DoD)

* `POST endpoint JSON-RPC` funciona para `health` e `fileops.read`.
* Respostas seguem JSON-RPC 2.0:

  * sucesso: `{jsonrpc, id, result}`
  * falha: `{jsonrpc, id, error{code,message,data?}}`
* Métodos mínimos cobertos por testes (happy path + method not found + invalid request).
* Registry não contém métodos snake_case.
* Endpoints legados se tornam vermelhos.

## 7) Plano de Implementação (tarefas)

1. Criar endpoint `POST endpoint JSON-RPC` (delivery FastAPI) + modelos Pydantic do envelope JSON-RPC.
2. Implementar dispatcher: `method -> handler` via registry.
3. Adaptar handlers existentes:

   * `health` registrado como `health`
   * `fileops_read` renomeado/registrado como `fileops.read`
4. Mapear Result/Envelope para JSON-RPC:

   * OK -> `result`
   * FAIL -> `error` com code/message + data (opcional)
5. Testes:

   * `health` ok
   * `fileops.read` ok
   * método inexistente
   * request inválida
6. Ajustes de docs mínimos:

   * anotar em docs que `endpoint JSON-RPC` é canônico (sem reescrever todo o acervo agora)

## 8) Riscos e Mitigações

* **Divergência de contrato** continuar: mitigar definindo `endpoint JSON-RPC` como canônico.
* **Mudança de naming** quebrar consumidores internos: mitigar mantendo alias temporário (opcional) e removendo no próximo ciclo.

> "Primeiro alinhe o contrato; depois acelere o mundo." – made by Sky ✨
