---
status: aceito
data: 2025-12-27
---

# PRD007 — Sky-RPC Ticket + Envelope

## 1) Problema

O contrato anterior baseado em JSON-RPC enfrenta limitações em ambientes de GPT
Custom Actions (schema rígido) e para payloads maiores. Isso bloqueia chamadas
com dados estruturados e gera divergência entre contrato e execução.

## 2) Objetivo

Adotar o fluxo Sky-RPC com ticket + envelope como contrato canônico:

- `GET /openapi` como catálogo oficial.
- `GET /ticket?method=<dominio.caso>` para criação de ticket.
- `POST /envelope` para envio do payload real.

## 3) Escopo

### Inclui

- Criação e validação de tickets com expiração.
- Execução por `method` via detalhes flat (`detalhe`, `detalhe_1`, `detalhe_2`).
- Segurança via bearer token e policy por método.
- Logs e métricas por ticket.

### Não inclui

- UI de gestão de tickets.
- Multi-tenant completo (fase futura).
- Assinaturas digitais de envelope.

## 4) Requisitos Funcionais

* **RF1 (Ticket):** `GET /ticket` retorna `ticket_id`, `method`, `expires_in`.
* **RF2 (Envelope):** `POST /envelope` executa o método referenciado.
* **RF3 (Expiração):** ticket expirado retorna erro `4100`.
* **RF4 (Auth):** autenticação obrigatória por bearer.
* **RF5 (AuthZ):** método fora da policy retorna `4030`.

## 5) Requisitos Não Funcionais

* Baixa latência no handshake.
* Tickets armazenados in-memory com TTL (fase 1).
* Compatibilidade com GPT Custom Actions.

## 6) DoD (Critérios de Aceite)

* `GET /ticket?method=health` funciona com auth válida.
* `POST /envelope` executa `health` e `fileops.read`.
* Ticket expirado retorna erro correto.
* Logs incluem `ticket_id`, `method`, `client_id`, `latency_ms`.
* Rota /privacy funcionando.

## 7) Plano de Implementação

1. Criar endpoints `/ticket` e `/envelope`.
2. Implementar store in-memory com TTL para tickets.
3. Integrar auth/policy com `client_id`.
4. Atualizar `/openapi` para o novo contrato.
5. Criar testes de integração para tickets e envelope.

> "Clareza primeiro, execução depois." – made by Sky ✨
