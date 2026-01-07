# Crossfire: Sky-RPC vs JSON-RPC

**Data:** 2025-01-05

**Status:** Análise Comparativa

**Contexto:** Skybridge 2.0 - Avaliação da decisão de romper com JSON-RPC

---

## Resumo Executivo

**Pergunta Central:** JSON-RPC poderia ter sido adaptado para resolver os problemas da Skybridge 1.0, ou era necessário criar um protocolo próprio?

**Resposta:** **SIM, JSON-RPC poderia ter sido adaptado.**

A análise demonstra que os problemas atribuídos ao JSON-RPC eram, na verdade, problemas de **configuração** e **convenção**, não limitações do protocolo. Sky-RPC é uma escolha válida de identidade e controle, mas não era tecnicamente necessária.

---

## Contexto: Skybridge 1.0 → 2.0

### Problemas Reais da 1.0

| Problema | Descrição | Impacto |
|----------|-----------|---------|
| **OpenAPI limite** | 50+ endpoints, JIT lento, cache problemático | Bloqueio de crescimento |
| **Apenas GPT Custom** | Single point of failure | Falta de resiliência |
| **GPT-4o inconsistência** | Interpretação variada de comandos | Comportamento imprevisível |
| **JIT limitações** | Schema rígido rejeitava campos | Erros antes de chegar à API |

### Resposta Sky-RPC

- 3 endpoints fixos (/ticket, /envelope, /discover)
- Protocolo próprio com semântica explícita
- Introspecção runtime dinâmica

---

## Estrutura Comparativa

### JSON-RPC 2.0 (Padrão)

```json
POST /rpc
{
  "jsonrpc": "2.0",
  "method": "fileops.read",
  "params": {
    "path": "README.md",
    "encoding": "utf-8",
    "limit": 100
  },
  "id": "req-001"
}
```

**Características:**
- 1 round-trip (request/response)
- Correlação via `id`
- `params` flexível (qualquer JSON válido)
- Especificação madura (RFC-like)

### Sky-RPC v0.3 (Atual)

```json
// 1. Handshake
GET /ticket?method=fileops.read
→ { "ticket_id": "uuid", "meta": {...} }

// 2. Execução
POST /envelope
{
  "ticket_id": "uuid",
  "detail": {
    "context": "fileops",
    "subject": "README.md",
    "action": "read",
    "scope": "tenant:sky",
    "options": { "limit": 100 },
    "payload": {}
  }
}
```

**Características:**
- 2+ round-trips (ticket + envelope)
- Correlação via `ticket_id`
- Semântica explícita (context/subject/action)
- Introspecção via `/discover`

---

## Round-by-Round: Análise Detalhada

### Round 1: Escalabilidade

**Problema:** OpenAPI da 1.0 cresceu demais em endpoints

#### Solução Sky-RPC

```yaml
paths:
  /ticket: ...
  /envelope: ...
  /discover: ...
```

#### Solução JSON-RPC

```yaml
paths:
  /rpc: ...       # Endpoint único

/discovery:       # Descoberta dinâmica
  get:
    # Retorna todos os métodos disponíveis
```

**Veredito:** **EMPATE TÉCNICO**

Ambos resolvem o problema com endpoint único + descoberta dinâmica. Sky-RPC não tem vantagem técnica aqui.

---

### Round 2: Semântica

#### Sky-RPC

```json
{
  "detail": {
    "context": "fileops",    // Domínio
    "subject": "README.md",  // Entidade-alvo
    "action": "read",        // Operação
    "scope": "tenant:sky",   // Multi-tenant
    "options": {...},        // Opções específicas
    "payload": {...}         // Dados específicos
  }
}
```

#### JSON-RPC Adaptado

```json
{
  "method": "fileops.read",
  "params": {
    "context": "fileops",    // ✅ Pode ter
    "subject": "README.md",  // ✅ Pode ter
    "action": "read",        // ✅ Pode ter
    "scope": "tenant:sky",   // ✅ Pode ter
    "options": {...},        // ✅ Pode ter
    "payload": {...}         // ✅ Pode ter
  },
  "id": "req-001"
}
```

**Veredito:** **SKY-RPC VENCE**

Sky-RPC força semântica via estrutura. JSON-RPC depende de convenção em `params`.

**Porém:** A diferença é estrutural, não funcional. Ambos expressam a mesma informação.

---

### Round 3: GPT Custom (O Gatilho)

#### Problema Reportado

> "Schema rígido do GPT Custom rejeita campos fora do modelo esperado"

#### Análise Honestas

O problema era o **protocolo** ou a **configuração do schema**?

```yaml
# Schema que causou o problema
JSONRPCRequest:
  properties:
    method: string
    params:
      additionalProperties: false  # ← BLOQUEIA campos não declarados

# Schema que resolveria
JSONRPCRequest:
  properties:
    method: string
    params:
      additionalProperties: true   # ← PERMITE qualquer campo
```

**Veredito:** **JSON-RPC VENCE (POR KO)**

O problema era **configuração**, não protocolo. A solução usada por Sky-RPC (`additionalProperties: true`) também se aplica a JSON-RPC.

---

### Round 4: Payloads Grandes

#### Afirmação do Relatório de Evolução

> "`params` do JSON-RPC limitava envio de arquivos"

#### Verificação Fática

```json
// JSON-RPC 2.0 spec
{
  "params": {
    "file_content": "SGVsbG8gV29ybGQ..."  // base64, pode ser GIGANTES
  }
}
```

**Especificação JSON-RPC 2.0:** `params` é um valor JSON arbitrário. Não há limite de tamanho no protocolo.

**Veredito:** **EMPATE (ARGUMENTO INVÁLIDO)**

Ambos suportam payloads arbitrários. O argumento é tecnicamente incorreto.

---

### Round 5: Round-Trips

#### Sky-RPC

```
Cliente              Servidor
   │                    │
   ├─ GET /ticket ────→ │
   │←─ ticket_id ───────┤
   │                    │
   ├─ POST /envelope ──→│
   │←─ response ────────┤

Total: 2 chamadas HTTP
```

#### JSON-RPC

```
Cliente              Servidor
   │                    │
   ├─ POST /rpc ──────→│
   │←─ response ────────┤

Total: 1 chamada HTTP
```

**Argumento a favor do ticket:** Rate limiting, autenticação, rastreamento

**Contra-argumento:**
- Rate limiting: headers HTTP ou API key
- Autenticação: headers HTTP
- Rastreamento: campo `id` do JSON-RPC (serve exatamente para isso)

**Veredito:** **JSON-RPC VENCE**

O ticket handshake é overhead desnecessário. JSON-RPC resolve correlação com `id`.

---

### Round 6: Ecossistema e Ferramentas

#### Sky-RPC

```
Ferramentas disponíveis:
├─ Cliente customizado (próprio)
├─ Documentação própria
├─ Testes manuais
└─ Nenhuma ferramenta de terceiros
```

#### JSON-RPC

```
Ferramentas disponíveis:
├─ Clients em Python, JS, Go, Rust, Java, PHP, Ruby...
├─ OpenAPI/Swagger com suporte
├─ Postman Collections
├─ Insomnia
├─ Ferramentas de teste automatizadas
├─ OpenRPC compatibility
└─ Comunidade global
```

**Veredito:** **JSON-RPC VENCE (POR ESMAGAÇÃO)**

Diferença de ordens de magnitude em maturidade de ecossistema.

---

## Placar Final

```
┌────────────────────────────────────────────────────────────┐
│                    PLACAR FINAL                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   Round 1: Escalabilidade      EMPATE TÉCNICO              │
│   Round 2: Semântica           SKY-RPC VENCE               │
│   Round 3: GPT Custom          JSON-RPC VENCE (KO)         │
│   Round 4: Payloads            EMPATE (argumento inválido)  │
│   Round 5: Round-trips         JSON-RPC VENCE              │
│   Round 6: Ecossistema         JSON-RPC VENCE (esmagadora)  │
│                                                            │
│   ┌────────────────────────────────────────────────────┐  │
│   │  SKY-RPC:     1 vitória                             │  │
│   │  JSON-RPC:    3 vitórias                            │  │
│   │  Empates:     2                                     │  │
│   └────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Prova Técnica: JSON-RPC Adaptado

### Especificação Proposta

```yaml
# OpenAPI para JSON-RPC adaptado
paths:
  /rpc:
    post:
      summary: Sky-RPC via JSON-RPC 2.0
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [jsonrpc, method, params, id]
              properties:
                jsonrpc:
                  type: string
                  enum: ["2.0"]
                method:
                  type: string
                  description: |
                    Operação no formato contexto.ação ou método completo
                  examples: ["fileops.read", "health.check"]
                params:
                  type: object
                  additionalProperties: true  # ← Chave para flexibilidade
                  properties:
                    # Estrutura semântica recomendada
                    context:
                      type: string
                      description: Domínio da operação
                    subject:
                      type: string
                      description: Entidade-alvo
                    action:
                      type: string
                      description: Ação específica
                    scope:
                      type: string
                      description: Escopo multi-tenant
                    options:
                      type: object
                      description: Opções específicas da operação
                    payload:
                      type: object
                      description: Dados específicos da operação
                id:
                  type: string
                  description: UUID para correlação request-response

  /discovery:
    get:
      summary: Descoberta dinâmica de métodos
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  methods:
                    type: array
                    items:
                      type: object
                      properties:
                        name:
                          type: string
                        description:
                          type: string
                        params_schema:
                          type: object
                        result_schema:
                          type: object
```

### Exemplo de Uso

```json
// Request
POST /rpc
{
  "jsonrpc": "2.0",
  "method": "fileops.read",
  "params": {
    "context": "fileops",
    "subject": "README.md",
    "action": "read",
    "scope": "tenant:sky",
    "options": { "limit": 100, "encoding": "utf-8" },
    "payload": {}
  },
  "id": "req-001"
}

// Response
{
  "jsonrpc": "2.0",
  "result": {
    "path": "README.md",
    "content": "...",
    "size": 1234
  },
  "id": "req-001"
}
```

**Resolve TODOS os problemas da 1.0:**
- ✅ Limite de operações: 1 endpoint + /discovery
- ✅ Semântica rica: `params` estruturado
- ✅ GPT Custom: `additionalProperties: true`
- ✅ Payloads grandes: sem limite
- ✅ Multi-tenant: `scope` em `params`
- ✅ Multi-protocolo: agnóstico

---

## Por Que Sky-RPC Então?

### Motivos Válidos (Não Técnicos)

| Motivo | Descrição | Justificável? |
|--------|-----------|---------------|
| **Terminologia própria** | `detail/context/subject/action` vs `params` | ✅ Sim |
| **Controle total** | Evolução independente de spec externa | ✅ Sim |
| **Identidade de produto** | "Sky-RPC" vs "JSON-RPC" | ✅ Sim |
| **Desacoplamento de decisões passadas** | Romper com ADR004 | ⚠️ Depende |

### Motivos Questionáveis

| Argumento | Realidade |
|-----------|-----------|
| "JSON-RPC limita payloads" | ❌ Falso - especificação não impõe limite |
| "JSON-RPC não escala" | ❌ Falso - 1 endpoint + discovery resolve |
| "GPT Custom rejeita JSON-RPC" | ❌ Era configuração (`additionalProperties`) |
| "Semântica pobre" | ⚠️ Convenção vs estrutura - funcionalmente igual |

---

## Análise de Custo-Benefício

### Mantendo Sky-RPC

| Benefício | Custo |
|-----------|-------|
| Controle total da evolução | Ecossistema isolado |
| Terminologia própria | Manutenção de clientes customizados |
| Identidade de produto | Curva de aprendizado externa |
| Semântica forçada | 2+ round-trips por operação |

### Se Tivesse Usado JSON-RPC Adaptado

| Benefício | Custo |
|-----------|-------|
| Ecossistema maduro | Terminologia menos "própria" |
| Clientes prontos em 10+ linguagens | Convenção vs estrutura forçada |
| Ferramentas de teste padronizadas | Menor controle de branding |
| Interoperabilidade imediata | Depende de spec externa |

---

## Lições Aprendidas

### 1. Prototipagem Antes de Romper

```
❌ O que aconteceu:
   ADR004 (adotar JSON-RPC) → Problema com GPT Custom → ADR010 (romper)

✅ O que deveria:
   PoC com `additionalProperties: true` → Validar → Decisão final
```

### 2. Diagnóstico Correto de Problemas

| Sintoma | Diagnóstico Inicial | Diagnóstico Correto |
|---------|---------------------|---------------------|
| GPT Custom rejeita | "JSON-RPC incompatível" | "Schema fechado em `params`" |
| Escala limitada | "OpenAPI/REST inadequado" | "Faltava discovery dinâmico" |
| Payloads limitados | "`params` do JSON-RPC" | "Configuração, não protocolo" |

### 3. Trade-off Explícito

A decisão pelo Sky-RPC é um trade-off **VÁLIDO** se reconhecido como:

> "Preferimos controle e identidade própria em detrimento de interoperabilidade e ecossistema."

O problema é justificá-lo com **argumentos técnicos incorretos**.

---

## Recomendações

### Para Skybridge 2.0 (Sky-RPC)

1. **Documentar trade-off explicitamente**
   - Reconhecer que JSON-RPC adaptado seria tecnicamente viável
   - Justificar Sky-RPC por identidade/controle, não limitação técnica

2. **Considerar ponte de compatibilidade**
   ```python
   # Adaptador JSON-RPC → Sky-RPC
   @app.post("/rpc")
   async def jsonrpc_to_skyrpc(request: JSONRPCRequest):
       # Converte para envelope Sky-RPC
       ticket = await create_ticket(request.method)
       envelope = {
           "ticket_id": ticket.id,
           "detail": request.params  # context/subject/action
       }
       return await execute_envelope(envelope)
   ```

3. **Política de evolução**
   - Sky-RPC v0.3 é estável? Evitar v0.4, v0.5...
   - Se for evoluir, considerar alinhar mais com JSON-RPC

### Para Futuras Decisões Arquiteturais

1. **PoC antes de ADR**
   - Testar soluções com configurações diferentes
   - Validar limitações reais vs percebidas

2. **Segunda opinião técnica**
   - Revisão crítica de diagnósticos
   - Challenge de argumentos por alguém externo ao projeto

3. **Registro de trade-offs**
   - ADRs devem listar "alternativas consideradas e por que rejeitadas"
   - Incluir custo de manutenção de decisões não-padronizadas

---

## Conclusão

### Veredito Final

**Sky-RPC é uma escolha VÁLIDA para Skybridge 2.0, mas não era uma escolha NECESSÁRIA.**

A análise demonstra que:

1. **Tecnicamente:** JSON-RPC adaptado resolveria todos os problemas da 1.0
2. **Conceitualmente:** Sky-RPC oferece melhor semântica estruturada
3. **Praticamente:** JSON-RPC tem ecossistema muito superior
4. **Estrategicamente:** Sky-RPC é uma decisão de identidade, não técnica

### Posição Final

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Sky-RPC foi uma decisão de CONTROLE e IDENTIDADE         │
│   Não uma resposta a limitações técnicas do JSON-RPC        │
│                                                             │
│   Reconhecer isso é crucial para:                           │
│   - Documentação honesta                                    │
│   - Decisões futuras                                       │
│   - Avaliação de custo-benefício                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Próximos Passos Sugeridos

1. Atualizar ADR010 com esta análise
2. Considerar adaptador JSON-RPC para interoperabilidade
3. Documentar trade-off explicitamente na SPEC004
4. Estabelecer política de evolução de protocolo

---

## Referências

- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [OpenRPC Specification](https://spec.openrpc.org/)
- ADR004 - Adotar JSON-RPC como Contrato Canônico
- ADR010 - Adotar Sky-RPC
- ADR014 - Evoluir Sky-RPC
- SPEC002 - Sky-RPC v0.2
- SPEC004 - Sky-RPC v0.3
- `sky-rpc-evolution-analysis.md`
- `openapi-patternproperties-fix.md`

---

> "A melhor arquitetura é a que funciona. A arquitetura sustentável é a que não te isola do mundo. A arquitetura honesta é a que reconhece suas escolhas como escolhas, não como necessidades." – made by Sky ⚖️
