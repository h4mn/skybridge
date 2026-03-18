---
status: aceito
data: 2025-12-27
---

# PB007 - Ajuste de permissões na Skybridge (Sky-RPC)

## 0) Escopo

Este playbook descreve como ajustar permissões de acesso por **client_id** e **método**
no runtime da Skybridge, usando variáveis de ambiente e validação rápida via ticket/envelope.

## 1) Princípios

- Permissões são aplicadas por **client_id** (resolvido via Bearer/API key).
- A policy define **quais métodos** cada client_id pode executar.
- Rotas públicas (`/openapi` e `/privacy`) não passam pela policy.

## 2) Variáveis de ambiente

As permissões são controladas por:

- `SKYBRIDGE_METHOD_POLICY`: `cliente:metodo1,metodo2;cliente2:metodoA`
- `SKYBRIDGE_BEARER_TOKENS`: `cliente:token;cliente2:token`
- `SKYBRIDGE_API_KEYS`: `cliente:apikey;cliente2:apikey`
- `SKYBRIDGE_API_KEY`: chave única simples (legado)
- `ALLOW_LOCALHOST`: `true|false` (bypass local quando habilitado)

## 3) Como definir a policy

### 3.1 Exemplo (Bearer)

```bash
export SKYBRIDGE_BEARER_ENABLED=true
export SKYBRIDGE_BEARER_TOKENS="sky:token-sky;pm:token-pm"
export SKYBRIDGE_METHOD_POLICY="sky:health,fileops.read;pm:health"
```

### 3.2 Exemplo (API key)

```bash
export SKYBRIDGE_API_KEYS="sky:api-sky;pm:api-pm"
export SKYBRIDGE_METHOD_POLICY="sky:health,fileops.read;pm:health"
```

## 4) Validação rápida (ticket + envelope)

Nota: `method` é o nome da operação Sky-RPC (ex.: `fileops.read`), não é verbo HTTP.

1) **Criar ticket**

```bash
curl -G http://localhost:8000/ticket \
  -H "Authorization: Bearer token-sky" \
  --data-urlencode "method=fileops.read"
```

2) **Enviar envelope**

```bash
curl -X POST http://localhost:8000/envelope \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer token-sky" \
  -d "{\"ticket_id\":\"<id>\",\"detalhe\":\"README.md\"}"
```

## 5) Erros comuns e como corrigir

- `4010 Unauthorized`: credencial ausente/inválida.
  - Verifique `SKYBRIDGE_BEARER_TOKENS` ou `SKYBRIDGE_API_KEYS`.
- `4030 Forbidden`: método não está permitido na policy.
  - Atualize `SKYBRIDGE_METHOD_POLICY` para incluir o método.
- `4040 Ticket not found`: ticket inexistente.
  - Gere um novo ticket.
- `4100 Ticket expired`: ticket expirou.
  - Refaça o `GET /ticket`.
- `4220 Payload inválido`: detalhe não passou na validação do método.
  - Ajuste o `detalhe` conforme o schema.

## 6) Checklist

- [ ] client_id definido nas variáveis (Bearer/API key)
- [ ] policy configurada para o método desejado
- [ ] ticket criado com o mesmo client_id
- [ ] envelope enviado antes do TTL expirar

> "Clareza primeiro, execução depois." – made by Sky ✨
