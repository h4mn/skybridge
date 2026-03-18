---
status: aceito
data: 2025-12-25
---

﻿# ADR007 — Baseline de Segurança para Acesso LLM (JSON-RPC)

**Status:** Aceito

**Data:** 2025-12-25

## Contexto

A Skybridge expõe operações via JSON-RPC e será consumida por LLMs/agents (clientes automatizados). HTTPS protege o transporte, mas não controla **quem** acessa, **o que** pode executar e **quanto** pode executar. Precisamos de um baseline mínimo de segurança, observabilidade e limites por método, com uma estratégia de transição para multi-tenant.

## Decisão

Adotar um baseline mínimo para acesso LLM que inclui:

1. **Autenticação**

* Em fase inicial, exigir **API key global** para chamadas remotas.
* Exceção controlada: **localhost liberado** para testes (ver DoD).

2. **Autorização por método**

* Policy por `method` (allowlist) por cliente.
* `method` não autorizado retorna erro padrão.

3. **Rate limit e quotas**

* Limites por `client_id` (e opcionalmente por `method`).

4. **Auditoria e observabilidade**

* Logs estruturados obrigatórios por request com: `method`, `client_id`, `id`/`correlation_id`, `idempotency_key` (para commands), `status`, `latency_ms`.
* Reservar ganchos para integração futura (Sentry/Prometheus) como integração core.

5. **Restrições de FileOps**

* Manter allowlist de paths e bloqueio de path traversal antes de qualquer acesso ao disco.

## Alternativas Consideradas

1. **Apenas allowlist de IP (WAF/edge)**

* Prós: simples e barato; reduz exposição externa.
* Contras: não identifica cliente (sem `client_id`), frágil com NAT/VPN; não resolve autorização por método.

2. **API key global apenas**

* Prós: implementação rápida; funciona em qualquer rede.
* Contras: chave única é risco operacional; sem segmentação por cliente.

3. **Combinar (1) + (2) agora; evoluir para JWT/OAuth em fase tenant** (decisão escolhida)

* Prós: defesa em profundidade; reduz exposição e habilita evolução para multi-tenant.
* Contras: requer disciplina de config/infra (WAF em fase tenant/allowlist IP) e rotação de chave.

## Consequências

### Positivas

* Reduz risco de acesso indevido e abuso.
* Estabelece base para multi-tenant (JWT/OAuth) sem travar o MVP.
* Observabilidade “pronta” facilita troubleshooting e auditoria.

### Negativas / Trade-offs

* Aumenta complexidade inicial (headers/config/limites).
* Allowlist de IP pode incomodar em ambientes com IP variável.

## Escopo

**Inclui:** auth por API key, allowlist de IP (quando disponível), policy por método, rate limit básico, logging estruturado, códigos de erro padronizados, e enforcement das restrições de FileOps.

**Não inclui:** billing, UI de gestão, SIEM completo, multi-tenant final (JWT/OAuth) nesta fase.

## Contrato de Erros (publicação)

Quando publicado para consumo externo, padronizar:

* **4010**: Unauthorized (sem credencial / credencial inválida)
* **4030**: Forbidden (método não autorizado)
* **4290**: Rate limited / quota exceeded

Recomendação: retornar também os códigos JSON-RPC padrão para erros de protocolo (ex.: `-32600`, `-32601`, `-32602`, `-32603`) quando aplicável.

## DoD (Fase 1)

* Requests remotos sem credencial falham com `error.code=4010`.
* `method` não autorizado falha com `error.code=4030`.
* Rate limit ativo por `client_id` (retorna `error.code=4290`).
* Logs incluem `method`, `client_id`, `id` (ou `correlation_id`), `status`, `latency_ms`.
* **Localhost liberado** para testes automatizados (ex.: Codex) via configuração (ex.: `ALLOW_LOCALHOST=true`).

> "Segurança mínima antes de escala." – made by Sky ✨
