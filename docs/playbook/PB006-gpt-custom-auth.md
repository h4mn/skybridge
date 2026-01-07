---
status: aceito
data: 2025-12-26
---

# PB006 - GPT Custom: Autenticação e chamadas Sky-RPC

## 0) Escopo

Este playbook descreve como configurar autenticação no GPT Custom Actions para
chamar a Skybridge via `/openapi`, `/ticket` e `/envelope`.

## 1) Pre-requisitos

- Servidor Skybridge acessível (local ou ngrok).
- Endpoint `/openapi` publicado e atualizado.
- Credencial válida (API key ou bearer token).

## 2) Configurar o OpenAPI no GPT Custom

1. Use a URL pública do `/openapi` (ex.: `https://<ngrok>/openapi`).
2. Garanta que o OpenAPI declara `securitySchemes` e `security`.
3. Nota: por limitação do GPT Custom Actions, o OpenAPI público deve expor
   **apenas um** esquema de segurança. Para este fluxo, manter **Bearer**.
   A API key continua suportada no runtime, mas não aparece no OpenAPI público.

## 3) Configurar a autenticação (tela "Autenticação")

Na tela de autenticação:

- Para **API key**:
  - Tipo de autenticação: **Chave API**.
  - Campo "Chave API": informe o valor real.
- Para **Bearer**:
  - Tipo de autenticação: **Bearer**.
  - Salve.

## 4) Fluxo Sky-RPC (ticket + envelope)

1) **Criar ticket**

`GET /ticket?method=dominio.caso`

Nota: `method` é o nome da operação Sky-RPC (ex.: `fileops.read`), não é verbo HTTP.

Resposta esperada:
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

2) **Enviar envelope**

`POST /envelope`

Request:
```json
{
  "ticket_id": "a3f9b1e2",
  "detalhe": "README.md"
}
```

## 5) Erros comuns

- `4010 Unauthorized`: credencial ausente ou inválida.
- `4030 Forbidden`: policy não permite o método para o `client_id`.
- `4040 Ticket not found`: ticket inválido.
- `4100 Ticket expired`: ticket expirado.
- `4220 Detalhe inválido`: detalhe não passou na validação do método.

## 6) Checklist rápido

- [ ] `/openapi` aponta para o contrato atual.
- [ ] `securitySchemes` e `security` presentes no OpenAPI.
- [ ] Credencial configurada na tela de autenticação.
- [ ] Ticket criado via `GET /ticket`.
- [ ] Envelope enviado via `POST /envelope`.

> "Clareza primeiro, execução depois." - made by Sky
