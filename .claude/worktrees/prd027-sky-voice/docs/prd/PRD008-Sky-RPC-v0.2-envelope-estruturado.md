---
status: proposta
data: 2025-12-27
relacionado:
  - PRD007-Sky-RPC-ticket-envelope.md
  - SPEC002-Sky-RPC-v0.2.md
  - ADR010-adotar-sky-rpc.md
---

# PRD008 — Sky-RPC v0.2 (Envelope Estruturado)

## 1) Problema

A v0.1 do Sky-RPC utiliza `detalhe` e `detalhe_N` como campos flat, o que:
- Dificulta validação estrita de schemas complexos
- Não expressa semanticamente a intenção da operação
- Gera ambiguidade em operações com múltiplos parâmetros
- Usa keyword em português (`detalhe`), fugindo de padrões internacionais

## 2) Objetivo

Evoluir Sky-RPC para v0.2 com envelope estruturado:
- **Keyword padrão:** `detail` (en) em vez de `detalhe` (pt-BR)
- **Estrutura semântica:** `{ context, subject, action, payload }`
- **Compatibilidade:** legado (`detalhe` string) mantido via `oneOf`
- **Validação estrita:** `minProperties: 1` em payload

## 3) Escopo

### Inclui

- Novo schema `EnvelopeRequest` com `detail` (oneOf: string | object)
- Parser de envelope estruturado com campos semânticos
- Mapeamento reverso: legado `detalhe` → `detail`
- Validação de `minProperties: 1` para payload
- Novo erro `4221` para payload vazio
- Atualização do OpenAPI.yaml
- Testes de compatibilidade v0.1 → v0.2

### Não inclui

- Mudança na lógica de tickets (mantido de v0.1)
- Alteração de autenticação/autorização
- Mudança no modelo de resposta (`EnvelopeResponse`)

## 4) Requisitos Funcionais

### Core

| ID | Descrição |
|----|-----------|
| **RF1** | `POST /envelope` aceita `detail` como **string** (legado) |
| **RF2** | `POST /envelope` aceita `detail` como **objeto** `{ context, subject, action, payload }` |
| **RF3** | Parser reconhece `detalhe` (pt-BR) e mapeia para `detail` (compatibilidade reversa) |
| **RF4** | `payload` no formato estruturado é **obrigatório** |
| **RF5** | `payload` deve conter pelo menos 1 propriedade (`minProperties: 1`) |
| **RF6** | Payload vazio retorna erro `4221` |

### Validação

| ID | Descrição |
|----|-----------|
| **RF7** | `context` é obrigatório no envelope estruturado |
| **RF8** | `action` é obrigatório no envelope estruturado |
| **RF9** | `payload` é obrigatório no envelope estruturado |
| **RF10** | `subject` é opcional no envelope estruturado |

### Compatibilidade

| ID | Descrição |
|----|-----------|
| **RF11** | Clientes v0.1 com `detalhe: "valor"` continuam funcionando |
| **RF12** | Clientes v0.1 com `detalhe_1`, `detalhe_2` continuam funcionando |
| **RF13** | Novos clientes v0.2 recebem erro se usarem `detalhe` (depreciação) |

### Observabilidade

| ID | Descrição |
|----|-----------|
| **RF14** | Logs incluem `detail_type` (string | structured) |
| **RF15** | Logs incluem `context`, `action`, `subject` quando envelope estruturado |
| **RF16** | Métrica separada para requests legado vs estruturado |

## 5) Requisitos Não Funcionais

| ID | Descrição |
|----|-----------|
| **RNF1** | Latência de parsing < 5ms para envelope estruturado |
| **RNF2** | OpenAPI schema válido para `oneOf` |
| **RNF3** | Pydantic schemas sem warnings |
| **RNF4** | 100% de cobertura de testes para parser |
| **RNF5** | Documentação de migração clara |

## 6) DOD (Definition of Done)

### DOD1 — Implementação Core

- [ ] `EnvelopeRequest` Pydantic atualizado com `detail: Union[str, EnvelopeDetail]`
- [ ] `EnvelopeDetail` model com `context`, `subject`, `action`, `payload`
- [ ] `payload` com validação `minProperties: 1`
- [ ] Parser `_parse_detail()` implementa lógica `oneOf`
- [ ] Mapeamento reverso `detalhe` → `detail` implementado
- [ ] Erro `4221` implementado para payload vazio

### DOD2 — OpenAPI e Schema

- [ ] `openapi/v1/skybridge.yaml` atualizado com schema `oneOf`
- [ ] Exemplos de request v0.1 e v0.2 documentados
- [ ] Schema passa validação sem erros
- [ ] Campo `detalhe` marcado como `deprecated: true`
- [ ] `Version` incrementada de 0.2.1 para 0.2.2

### DOD3 — Testes

- [ ] Teste unitário: `detail` como string (legado)
- [ ] Teste unitário: `detail` como objeto estruturado
- [ ] Teste unitário: `detalhe` → `detail` mapeamento reverso
- [ ] Teste unitário: payload vazio → erro 4221
- [ ] Teste unitário: payload com 0 propriedade → erro 4221
- [ ] Teste unitário: payload com 1+ propriedades → ok
- [ ] Teste integração: fluxo completo v0.1 → v0.2
- [ ] Teste integração: `fileops.read` com envelope estruturado

### DOD4 — Observabilidade

- [ ] Logs incluem `detail_type`
- [ ] Logs incluem `context`, `action`, `subject` (quando aplicável)
- [ ] Métrica `sky_rpc_envelope_type{type="legacy|structured"}`

### DOD5 — Documentação

- [ ] SPEC002 v0.2 finalizada
- [ ] PRD008 finalizado
- [ ] Guia de migração v0.1 → v0.2 criado
- [ ] Changelog atualizado

## 7) Casos de Teste

### CT1 — Legado (Compatibilidade)

**Given:** ticket válido para `fileops.read`
**When:** POST `/envelope` com `{ "ticket_id": "abc", "detalhe": "README.md" }`
**Then:** status 200, arquivo lido com sucesso

### CT2 — Estruturado Completo

**Given:** ticket válido para `fileops.read`
**When:** POST `/envelope` com:
```json
{
  "ticket_id": "abc",
  "detail": {
    "context": "fileops.read",
    "subject": "README.md",
    "action": "read",
    "payload": { "encoding": "utf-8" }
  }
}
```
**Then:** status 200, arquivo lido com encoding utf-8

### CT3 — Payload Vazio

**Given:** ticket válido para `fileops.read`
**When:** POST `/envelope` com `detail.payload = {}`
**Then:** status 422, código `4221`, mensagem "Payload cannot be empty"

### CT4 — Sem Payload

**Given:** ticket válido para `fileops.read`
**When:** POST `/envelope` sem campo `detail.payload`
**Then:** status 422, código `4220`, mensagem "Missing required field: payload"

### CT5 — Mapeamento Reverso

**Given:** ticket válido para `health`
**When:** POST `/envelope` com `{ "ticket_id": "abc", "detalhe": "ping" }`
**Then:** status 200, tratado como `detail: "ping"` (mapeamento interno)

## 8) Plano de Implementação

### Fase 1 — Foundation (1-2 dias)
1. Criar models Pydantic: `EnvelopeDetail`, `EnvelopeRequestV2`
2. Implementar `_parse_detail()` com lógica `oneOf`
3. Adicionar validação `minProperties: 1`
4. Implementar erro `4221`

### Fase 2 — Compatibilidade (1 dia)
5. Implementar mapeamento reverso `detalhe` → `detail`
6. Adicionar deprecation warning para `detalhe`
7. Testar casos legado

### Fase 3 — OpenAPI e Testes (1 dia)
8. Atualizar `skybridge.yaml` com schema `oneOf`
9. Criar suíte de testes completa
10. Validar schema com OpenAPI validator

### Fase 4 — Observabilidade e Docs (0.5 dia)
11. Adicionar campos de log (`detail_type`, `context`, etc)
12. Criar métrica de envelope type
13. Finalizar SPEC002 v0.2 e guia de migração

### Fase 5 — Validação (0.5 dia)
14. Testes end-to-end com GPT Custom Actions
15. Testes de performance (latência < 5ms)
16. Code review e aprovação

## 9) Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Breaking change em clientes atuais | Alto | Mapeamento reverso `detalhe` → `detail` |
| Complexidade de `oneOf` no Pydantic | Médio | Testes extensivos + validação manual |
| Performance do parser | Baixo | Benchmark + cache se necessário |

## 10) Success Metrics

- [ ] 100% dos testes passando
- [ ] Zero regressões em clientes v0.1
- [ ] Latência de parsing < 5ms (p95)
- [ ] Cobertura de testes > 90%
- [ ] OpenAPI schema validado sem erros

---

> "Evolução com backbone: respeitar o passado, construir o futuro." – made by Sky 🔄
