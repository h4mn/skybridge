---
status: aceito
data: 2025-12-25
---

﻿# PRD005 — Baseline de Segurança LLM (Fase 1)

## 1) Problema

LLMs/agents acessando a Skybridge exigem controle de acesso, limites e auditoria. HTTPS cobre transporte, mas não cobre **autenticação**, **autorização** e **abuso**.

## 2) Objetivo

Entregar um baseline funcional de segurança para consumo **JSON-RPC** por LLMs, com políticas mínimas (auth/authz/rate limit/logs) sem bloquear evolução futura (JWT/OAuth, multi-tenant).

## 3) Escopo

### Inclui

* Autenticação obrigatória por **`X-API-Key`** (baseline).
* Autenticação opcional por **`Authorization: Bearer`** apenas se habilitada via config.
* Autorização por `method` (policy allowlist por `client_id`, deny-by-default).
* Rate limit por `client_id` (e opcionalmente por `method`).
* Logs estruturados com `method`, `client_id`, `id`/`correlation_id`, `latency_ms`.
* Bypass controlado para testes locais via `ALLOW_LOCALHOST=true`.

### Não inclui

* UI de gestão de credenciais.
* Billing/quotas pagas.
* Multi-tenant completo.
* WAF/allowlist de IP como requisito obrigatório (pode ser adotado em fase posterior).

## 4) Requisitos Funcionais

* **RF1 (Auth):** requests remotos sem credencial devem falhar com `error.code=4010`.
* **RF2 (AuthZ):** `method` não autorizado deve falhar com `error.code=4030`.
* **RF3 (Rate limit):** estouro de limite deve falhar com `error.code=4290` e `error.data.retry_after` (segundos) quando aplicável.
* **RF4 (Logging):** logs estruturados devem incluir no mínimo: `method`, `client_id`, `id` (quando presente) e/ou `correlation_id`, `status`, `latency_ms`.
* **RF5 (Localhost tests):** quando `ALLOW_LOCALHOST=true` e origem for `localhost/127.0.0.1`, permitir execução sem credencial (mantendo authz/rate limit se configurados).

## 5) Requisitos Não Funcionais

* Não quebrar operações existentes (endpoints atuais continuam funcionando).
* Baixa latência adicional (overhead mínimo).
* Configurável via environment variables.

## 6) DoD (Critérios de Aceite)

* Auth e policy por `method` funcionando para `health` e `fileops.read`.
* Rate limit configurável via env e ativo por `client_id`.
* Testes cobrindo:

  * sem auth → 4010
  * method proibido → 4030
  * rate limit → 4290 (+ retry_after)
  * localhost bypass (ALLOW_LOCALHOST) → sucesso
* Logs confirmados contendo os campos mínimos.

## 7) Plano de Implementação

1. Definir config de auth/policy/limits (env).
2. Middleware/guard de auth + resolução de `client_id` via credencial.
3. Guard de autorização por `method` (deny-by-default).
4. Rate limit simples (in-memory) por `client_id` (+ opcional por `method`).
5. Ajustar logs estruturados.
6. Testes automatizados.

> "Controle mínimo antes de escala." – made by Sky ✨
