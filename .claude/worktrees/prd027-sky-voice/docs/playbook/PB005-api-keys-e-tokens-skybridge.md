---
status: aceito
data: 2025-12-26
---

# PB005 - Gerenciar API keys e tokens na Skybridge

## 0) Escopo

Este playbook define como configurar, rotacionar e validar API keys e bearer tokens
da Skybridge via variáveis de ambiente.

## 1) Princípios

- Não versionar chaves em repositório.
- Usar `.env` apenas em ambiente local.
- Em produção, usar secrets do ambiente (CI/CD, vault, etc.).

## 2) Variáveis suportadas

As configurações de segurança são carregadas por variáveis de ambiente:

- `SKYBRIDGE_API_KEY`: chave única simples (legado).
- `SKYBRIDGE_API_KEYS`: múltiplas chaves no formato `nome:valor;nome2:valor2`.
- `SKYBRIDGE_BEARER_ENABLED`: `true|false` para habilitar bearer token.
- `SKYBRIDGE_BEARER_TOKENS`: tokens no formato `nome:valor;nome2:valor2`.
- `ALLOW_LOCALHOST`: permite chamadas sem autenticação para `localhost` (quando `true`).
- `SKYBRIDGE_IP_ALLOWLIST`: lista de IPs permitidos (separados por vírgula).
- `SKYBRIDGE_METHOD_POLICY`: política por cliente no formato
  `cliente:method1,method2;cliente2:methodA`.
- `SKYBRIDGE_RATE_LIMIT_PER_MINUTE`: limite de requisições por minuto.

## 3) Exemplos de configuração

### 3.1 API key simples

```bash
export SKYBRIDGE_API_KEY="minha-chave"
```

### 3.2 Múltiplas API keys

```bash
export SKYBRIDGE_API_KEYS="cli:abc123;postman:xyz789"
```

### 3.3 Bearer tokens

```bash
export SKYBRIDGE_BEARER_ENABLED=true
export SKYBRIDGE_BEARER_TOKENS="cli:token-1;postman:token-2"
```

### 3.4 Policy por cliente

```bash
export SKYBRIDGE_METHOD_POLICY="cli:health,fileops.read;postman:health"
```

## 4) Uso no cliente

### 4.1 API key (header)

```
x-api-key: <valor>
```

### 4.2 Bearer token (header)

```
Authorization: Bearer <valor>
```

## 5) Rotação de chaves

1. Adicionar nova chave em `SKYBRIDGE_API_KEYS` ou `SKYBRIDGE_BEARER_TOKENS`.
2. Atualizar clientes para usar a nova chave.
3. Remover a chave antiga após confirmar migração.
4. Validar acessos e logs.

## 6) Validação rápida (curl)

Nota: `method` é o nome da operação Sky-RPC (ex.: `fileops.read`), não é verbo HTTP.

```bash
# solicitar ticket
curl -G http://localhost:8000/ticket \
  -H "x-api-key: <valor>" \
  --data-urlencode "method=health"

# enviar envelope
curl -X POST http://localhost:8000/envelope \
  -H "Content-Type: application/json" \
  -H "x-api-key: <valor>" \
  -d "{\"ticket_id\":\"<id>\"}"
```

## 7) Checklist

- [ ] Chaves/tokens definidos via env.
- [ ] `SKYBRIDGE_BEARER_ENABLED` consistente com uso de bearer.
- [ ] `SKYBRIDGE_METHOD_POLICY` aplicada quando necessário.
- [ ] Rotação feita sem downtime.

> "Clareza primeiro, execução depois." – made by Sky ✨
