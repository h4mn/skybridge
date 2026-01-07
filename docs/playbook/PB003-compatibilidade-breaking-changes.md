---
status: aceito
data: 2025-12-25
---

# PB001 — Playbook de Compatibilidade e Breaking Changes (JSON-RPC/OpenRPC)

## 0) Escopo

Este playbook define como evoluir **operações** expostas via **JSON-RPC** (métodos `method`) e documentadas via **OpenRPC** sem quebrar consumidores.

Aplica-se a:

* métodos `kind=query` e `kind=command` (registry)
* schemas de `params` e `result`
* códigos de erro e semântica observável
* (opcional) façades HTTP geradas a partir do registry (quando existirem)

Não substitui ADRs; operacionaliza a evolução após as decisões.

## 1) Objetivo

* Minimizar quebras acidentais.
* Tornar breaking changes **explícitas** e **planejadas**.
* Permitir evolução rápida com previsibilidade (clientes/CLI/agentes).

## 2) Definições

* **Operação**: método canônico (`method`) ex.: `fileops.read`.
* **Compatível (backward compatible)**: um cliente existente continua funcionando sem mudanças.
* **Breaking**: um cliente existente pode falhar ou ter comportamento incorreto.
* **Contrato**: conjunto {method, kind, params schema, result schema, erros esperados} publicado via OpenRPC.

## 3) Fonte de verdade e invariantes

1. O **registry** é a fonte de verdade das operações e metadata.
2. O documento **OpenRPC** é gerado do registry e é o contrato publicado.
3. Mudanças em operação devem sempre atualizar:

   * handler
   * schema (params/result)
   * OpenRPC gerado
   * testes de contrato

## 4) Modelo de versionamento

### 4.1 Regra principal

* Mudança **breaking** exige **novo método versionado**.

### 4.2 Formato recomendado de método

Use um destes padrões (escolher 1 e padronizar no repo):

* **Sufixo por ponto:** `context.action.vN` (ex.: `tasks.create.v2`)
* **Sufixo por arroba:** `context.action@v2`

Recomendação: `context.action.vN` (mais fácil de navegar e grepar).

### 4.3 Estados de lifecycle

Cada método pode estar em um estado (metadata do registry e OpenRPC):

* `experimental` (pode mudar sem compat; evitar para uso amplo)
* `stable`
* `deprecated` (com `replaced_by`)
* `removed`

Regra: apenas métodos `stable` podem ser considerados “API pública” interna.

## 5) Compatibilidade: o que é permitido vs breaking

### 5.1 Mudanças compatíveis (permitidas no mesmo método)

**Params**

* Adicionar campo **opcional** em `params`.
* Ampliar enum aceitando novos valores (mantendo antigos válidos).
* Relaxar validação (mais permissivo), sem mudar significado.

**Result**

* Adicionar campo novo em `result`.
* Adicionar novos códigos de erro (não removendo os antigos em cenários comuns).

**Docs/Metadata**

* Melhorar descrição/exemplos.
* Adicionar tags.

### 5.2 Mudanças breaking (exigem novo método versionado)

**Schema**

* Remover/renomear qualquer campo em `params` ou `result`.
* Tornar campo opcional em obrigatório.
* Mudar tipo (string→object, int→string etc.).
* Restringir enum removendo valores aceitos.

**Semântica**

* Mudar significado de um campo (mesmo mantendo tipo).
* Alterar efeitos colaterais observáveis (ex.: `fileops.read` passar a registrar algo, bloquear casos antes permitidos sem versionar).
* Alterar garantias (ordem, atomicidade, consistência, idempotência).

**Erros**

* Alterar códigos de erro já usados como contrato (domínio ou protocolo) em fluxos comuns.

## 6) Política de erros e códigos

### 6.1 Protocolo JSON-RPC

Manter os códigos padrão do JSON-RPC para erros de envelope:

* `-32600` Invalid Request
* `-32601` Method not found
* `-32602` Invalid params
* `-32603` Internal error

### 6.2 Domínio (Skybridge)

* Reservar faixa **1000–1999** para erros de domínio (ex.: segurança, allowlist, permissão).
* Reservar faixa **2000–2999** para erros de infra (filesystem, timeout, IO).

Regra: mudar um `error.code` de domínio em cenário comum é **breaking**.

`error.data` deve ser estruturado e estável (ex.: `{"correlation_id":..., "details": {...}}`).

## 7) Processo para mudanças

### 7.1 Mudança compatível (mesmo método)

1. Alterar handler + schema.
2. Regenerar OpenRPC.
3. Atualizar/Adicionar testes de contrato.
4. Registrar nota curta no changelog interno (seção “Compatibility”).

### 7.2 Mudança breaking (novo método)

1. Criar método novo (ex.: `fileops.read.v2`).
2. Implementar handler v2.
3. Manter v1 funcionando.
4. Marcar v1 como `deprecated: true` e `replaced_by: <v2>`.
5. Regenerar OpenRPC (deve refletir depreciação e substituição).
6. Criar seção “Migration Notes” (ver template abaixo).
7. Testes de contrato:

   * v1 continua passando (congelado)
   * v2 passa

## 8) Depreciação e remoção

### 8.1 Janela mínima

* **Padrão interno:** 2 ciclos de release **ou** 30 dias (o que for maior).

### 8.2 Regras para remover

Remover (estado `removed`) apenas quando:

* OpenRPC mostra método como deprecated por pelo menos a janela mínima;
* telemetria/logs mostram uso próximo de zero (ou decisão explícita);
* existe nota no changelog de remoção.

### 8.3 Sinalização de depreciação em runtime

Quando um método deprecated for chamado, retornar `result.metadata` (ou `error.data`) com:

* `deprecated: true`
* `replaced_by: <method>`

## 9) Tooling e enforcement (CI)

### 9.1 Testes de contrato

Cada método `stable` deve ter:

* testes de schema (`params` e `result`)
* testes de erros essenciais

### 9.2 Diff de contrato

Em PRs que alteram registry/schemas:

* gerar OpenRPC antes/depois
* executar um “diff de contrato”
* falhar CI se detectar breaking change **sem** novo método versionado

(Implementação pode começar simples: script que compara JSON Schemas e lista removidos/renomeados/tipos alterados.)

## 10) Template de Migration Notes (para breaking)

Em um arquivo curto (ou seção no PRD/Changelog):

* **De:** `method.v1`
* **Para:** `method.v2`
* **O que mudou:** bullets
* **Como migrar:** exemplo de request/response
* **Prazo de remoção v1:** data/versão

## 11) Exemplos rápidos

### Exemplo A (compatível): adicionar campo opcional

* `params`: adiciona `encoding?: "utf-8" | "latin-1"` (opcional)
* Mantém v1.

### Exemplo B (breaking): renomear `path` para `filepath`

* Criar `fileops.read.v2` aceitando `filepath`.
* Marcar `fileops.read` deprecated com `replaced_by=fileops.read.v2`.

## 12) Checklist (antes de merge)

* [ ] Mudança é compatível ou breaking?
* [ ] Se breaking: método v2 criado e v1 deprecated + replaced_by.
* [ ] OpenRPC regenerado e revisado.
* [ ] Testes de contrato cobrindo v1 e v2.
* [ ] Erros/códigos revisados (não quebrou contrato).
* [ ] Migration Notes incluídas.

> "Compatibilidade é um contrato com o seu eu do futuro." – made by Sky ✨
