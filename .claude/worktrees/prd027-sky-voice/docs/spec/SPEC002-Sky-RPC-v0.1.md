---
status: aceito
data: 2025-12-27
---

# SPEC002 - Sky-RPC v0.1 (Ticket + Envelope)

## 1) Visão geral

Sky-RPC define um fluxo em dois passos para executar operações por método com
payloads arbitrários, mantendo validação e isolamento via ticket.

## 2) Rotas

### 2.1 GET /openapi

Retorna o contrato OpenAPI atualizado com os endpoints Sky-RPC.

### 2.2 GET /ticket?method=<dominio.caso>

Solicita um ticket de execução para o método informado.

Resposta (exemplo):
```json
{
  "ok": true,
  "ticket": {
    "id": "a3f9b1e2",
    "method": "fileops.read",
    "expires_in": 30,
    "accepts": "application/json"
  }
}
```

Regras:
- `method` é obrigatório.
- `ticket_id` expira em `expires_in` segundos.
- `method` identifica a operação, não o verbo HTTP.

### 2.3 POST /envelope

Executa a operação referenciada pelo ticket.

Request:
```json
{
  "ticket_id": "a3f9b1e2",
  "detalhe": "README.md"
}
```

Resposta (exemplo):
```json
{
  "ok": true,
  "id": "a3f9b1e2",
  "result": {
    "path": "README.md",
    "content": "...",
    "size": 123
  }
}
```

Regras:
- `ticket_id` é obrigatório.
- `detalhe` é obrigatório para operações com argumento único.
- Para múltiplos argumentos, usar `detalhe_1`, `detalhe_2`, etc.

## 3) Erros

- `4010`: Unauthorized (sem credencial / credencial inválida)
- `4030`: Forbidden (método não autorizado)
- `4040`: Ticket não encontrado
- `4100`: Ticket expirado
- `4220`: Payload inválido para o método

## 4) Segurança

- Autenticação obrigatória (Bearer).
- `method` validado contra allowlist.
- Rate limit por `client_id`.

## 5) Observabilidade

- Logs com `method`, `ticket_id`, `client_id`, `status`, `latency_ms`.
