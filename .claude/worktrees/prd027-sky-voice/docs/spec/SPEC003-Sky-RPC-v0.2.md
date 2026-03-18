---
status: proposta
data: 2025-12-27
versao_anterior: SPEC002-Sky-RPC-v0.1.md
---

# SPEC002 - Sky-RPC v0.2 (Envelope Estruturado)

## 1) Visão geral

Sky-RPC v0.2 evolui o envelope de detalhes flat (`detalhe`, `detalhe_1`) para um formato
estruturado com `context`, `subject`, `action` e `payload`, mantendo compatibilidade
legada via `oneOf`.

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

#### 2.3.1 Schema do Request

```yaml
EnvelopeRequest:
  type: object
  required:
    - ticket_id
    - detail
  properties:
    ticket_id:
      type: string
      description: "Identificador do ticket obtido em GET /ticket"
    detail:
      oneOf:
        - type: string
          description: "Compatibilidade legada - valor simples"
        - type: object
          description: "Envelope estruturado v0.2"
          properties:
            context:
              type: string
              description: "Contexto da operação (ex.: fileops.read)"
            subject:
              type: string
              description: "Entidade-alvo (arquivo, job, secret, etc)"
            action:
              type: string
              description: "Ação dentro do contexto (read, create, list...)"
            payload:
              type: object
              additionalProperties: true
              minProperties: 1
              description: "Dados específicos da execução"
          required:
            - context
            - action
            - payload
```

#### 2.3.2 Exemplos de Request

**Legado (string):**
```json
{
  "ticket_id": "a3f9b1e2",
  "detail": "README.md"
}
```

**v0.2 Estruturado:**
```json
{
  "ticket_id": "a3f9b1e2",
  "detail": {
    "context": "fileops.read",
    "subject": "README.md",
    "action": "read",
    "payload": {
      "encoding": "utf-8",
      "line_limit": 100
    }
  }
}
```

#### 2.3.3 Resposta

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
- `detail` é obrigatório (string ou objeto).
- `payload` no formato estruturado deve ter pelo menos uma propriedade (`minProperties: 1`).

## 3) Erros

- `4010`: Unauthorized (sem credencial / credencial inválida)
- `4030`: Forbidden (método não autorizado)
- `4040`: Ticket não encontrado
- `4100`: Ticket expirado
- `4220`: Payload inválido para o método
- `4221`: Payload vazio (minProperties: 1 violado)

## 4) Segurança

- Autenticação obrigatória (Bearer).
- `method` validado contra allowlist.
- Rate limit por `client_id`.
- Validação estrita do envelope estruturado.

## 5) Observabilidade

- Logs com `method`, `ticket_id`, `client_id`, `status`, `latency_ms`.
- Campos adicionais para envelope v0.2: `context`, `action`, `subject`.

## 6) Migração de v0.1 para v0.2

### 6.1 Compatibilidade

- v0.1 (`detalhe` como string) continua suportado via `oneOf` → mapeado para `detail` (string).
- **Breaking change:** campo `detalhe` (pt-BR) substituído por `detail` (en).
- Novos clientes devem usar o envelope estruturado.

### 6.2 Exemplo de Migração

**Antes (v0.1):**
```json
{
  "ticket_id": "abc123",
  "detalhe": "config.json"
}
```

**Depois (v0.2):**
```json
{
  "ticket_id": "abc123",
  "detail": {
    "context": "fileops.read",
    "subject": "config.json",
    "action": "read",
    "payload": {}
  }
}
```

## 7) Changelog

### v0.2 (2025-12-27)
- ✨ Envelope estruturado com `context`, `subject`, `action`, `payload`
- ✨ `payload` obrigatório no formato estruturado
- ✨ `minProperties: 1` para payload não-vazio
- 💥 **Breaking:** `detalhe` → `detail` (padronização keywords em inglês)
- ⬅️ Compatibilidade legada mantida via `oneOf` (mapeamento interno)

### v0.1 (2025-12-27)
- 🎉 Versão inicial com detalhes flat

---

> "Estrutura clara é a base de escalabilidade saudável." – made by Sky 🏗️
