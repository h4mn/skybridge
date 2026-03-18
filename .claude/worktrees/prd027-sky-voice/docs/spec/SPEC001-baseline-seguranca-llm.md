---
status: aceito
data: 2025-12-25
---

# SPEC001 — Baseline de Segurança para Sky-RPC (Skybridge)

## 1) Objetivo

Definir o contrato técnico mínimo para acesso seguro às operações Sky-RPC por clientes (incluindo LLMs), alinhado a **ADR006** (ID/Correlation/Idempotência) e **ADR007** (baseline de segurança).

## 2) Escopo

Inclui:

* Autenticação por header.
* Identidade de cliente (`client_id`).
* Autorização por `method` (policy allowlist).
* Rate limit e quotas básicas.
* Erros padronizados (protocolo e domínio).
* Observabilidade mínima.

Não inclui:

* Billing, UI de gestão, SIEM.
* Multi-tenant final (JWT/OAuth) — apenas prepara o caminho.

## 3) Terminologia

* **Sky-RPC**: fluxo `GET /ticket` + `POST /envelope`.
* **ticket_id**: identificador para correlação request↔response.
* **correlation_id**: identificador para rastreamento em logs (gerado pelo middleware).
* **client_id**: identidade do consumidor usada para policy e rate limit (derivada da credencial).

## 4) Autenticação (Headers)

### 4.1 Header primário (baseline)

* `X-API-Key: <api_key>`

### 4.2 Header secundário (futuro / opcional por config)

* `Authorization: Bearer <token>`

### 4.3 Regras

* Em fase inicial, **X-API-Key é o mecanismo oficial**.
* `Authorization: Bearer` pode ser habilitado posteriormente (tenant/JWT/OAuth).
* Se ambos estiverem presentes, **Authorization tem precedência** (quando habilitado).

### 4.4 Falhas

* Credencial ausente ou inválida: retornar erro de domínio **4010**.

## 5) Identidade do Cliente (`client_id`)

* `client_id` **DEVE** ser derivado da credencial (ex.: API key → client associado).
* `X-Client-Id` é **opcional** e apenas informativo; se enviado, pode ser logado,
  mas **não deve substituir** a identidade derivada da credencial sem política explícita.

Headers opcionais:

* `X-Client-Id: <string>` (debug/telemetria)

## 6) Autorização por método (Policy)

* Cada `method` possui uma policy de acesso configurada.
* Por padrão, a policy é **deny-by-default**.
* `method` não autorizado: retornar erro de domínio **4030**.

## 7) Rate limit e quotas

* Limites devem ser aplicados por **client_id** e, opcionalmente, por **method**.
* Estouro de limite: retornar erro de domínio **4290**.
* `error.data.retry_after` (segundos) deve ser retornado quando aplicável.

## 8) Localhost para testes (bypass controlado)

* Para execução de testes locais (ex.: Codex), pode existir bypass de auth quando:

  * `ALLOW_LOCALHOST=true` e
  * origem é `127.0.0.1`/`localhost`.

* Mesmo com bypass, `method`/rate limit podem continuar ativos (recomendado).

## 9) Erros

### 9.1 Erros de protocolo (Sky-RPC)

Erros de fluxo/ticket:

* `4040` Ticket not found
* `4100` Ticket expired
* `4220` Payload inválido

### 9.2 Erros de domínio (Skybridge)

Para falhas de segurança e limites (publicação):

* `4010` Unauthorized
* `4030` Forbidden
* `4290` Rate limit / quota exceeded

### 9.3 Formato do erro

Em respostas Sky-RPC com erro:

* `error.code`: código (protocolo ou domínio)
* `error.message`: mensagem curta e estável
* `error.data` (opcional): objeto estruturado

Campos recomendados em `error.data`:

* `correlation_id`
* `method`
* `client_id`
* `retry_after` (quando 4290)

## 10) Observabilidade

Logs estruturados por request devem incluir:

* `timestamp`
* `method`
* `id` (ticket_id)
* `correlation_id`
* `client_id`
* `status` (success/error)
* `latency_ms`

## 11) Compatibilidade

Breaking changes em métodos/schemas seguem o playbook **PB003 — Compatibilidade e Breaking Changes**:

* breaking change exige novo método versionado
* métodos antigos passam por depreciação antes de remoção

> "Clareza no contrato evita caos no crescimento." – made by Sky ✨
