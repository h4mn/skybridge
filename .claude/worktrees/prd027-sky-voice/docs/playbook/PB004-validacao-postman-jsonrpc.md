---
status: aceito
data: 2025-12-26
---

# PB004 - Validação manual via Postman (Sky-RPC)

## 0) Escopo

Este playbook descreve como validar manualmente a Skybridge usando o Postman,
com foco no fluxo Sky-RPC (`/ticket` + `/envelope`).

## 1) Pré-requisitos

- Servidor Skybridge rodando (local ou via ngrok).
- URL base conhecida (ex.: `http://localhost:8000` ou `https://<ngrok>/`).
- Se a segurança estiver ativa: API key ou bearer token.

## 2) Preparar ambiente no Postman

1. Crie um Environment (ex.: `Skybridge`).
2. Adicione variáveis:
   - `base_url` = `http://localhost:8000`
   - `api_key` = valor da chave (opcional)
   - `bearer_token` = token (opcional)

## 3) Request de ticket

Crie uma request `GET` para `{{base_url}}/ticket` e configure:

Headers:
- `Accept: application/json`
- `x-api-key: {{api_key}}` (opcional, se ativo)
- `Authorization: Bearer {{bearer_token}}` (opcional, se ativo)

Query params:
- `method` = `health` ou `fileops.read`
- `method` é o nome da operação Sky-RPC, não o verbo HTTP.

## 4) Request de envelope

Crie uma request `POST` para `{{base_url}}/envelope` e configure:

Headers:
- `Content-Type: application/json`
- `Accept: application/json`
- `x-api-key: {{api_key}}` (opcional, se ativo)
- `Authorization: Bearer {{bearer_token}}` (opcional, se ativo)

Body (raw JSON):
```json
{
  "ticket_id": "<id>",
  "detalhe": "README.md"
}
```

## 5) Validações recomendadas (Postman Tests)

Para `/ticket`:
```javascript
pm.test("status 200", () => pm.response.code === 200);
pm.test("ok=true", () => pm.response.json().ok === true);
pm.test("ticket id presente", () => pm.response.json().ticket.id);
```

Para `/envelope`:
```javascript
pm.test("status 200", () => pm.response.code === 200);
pm.test("ok=true", () => pm.response.json().ok === true);
```

## 6) Cenários de validação

### 6.1 health

1. `GET /ticket?method=health`
2. `POST /envelope` com:
```json
{"ticket_id":"<id>"}
```

Esperado:
- `result.status = "healthy"`.

### 6.2 fileops.read (quando permitido)

1. `GET /ticket?method=fileops.read`
2. `POST /envelope` com:
```json
{"ticket_id":"<id>","detalhe":"README.md"}
```

Esperado:
- `result` com conteúdo do arquivo.
- Se bloqueado, erro de domínio (ex.: allowlist).

## 7) Erros comuns

- `4010 Unauthorized`: credencial ausente ou inválida.
- `4030 Forbidden`: método não autorizado na policy.
- `4040 Ticket not found`: ticket inexistente.
- `4100 Ticket expired`: ticket expirado.
- `4220 Detalhe inválido`: detalhe não passou na validação.
- `4290 Rate limited`: limite excedido.

## 8) Checklist rápido

- [ ] Ticket criado via `GET /ticket`.
- [ ] Envelope enviado via `POST /envelope`.
- [ ] `ok=true` nas respostas.

> "Clareza primeiro, execução depois." - made by Sky
