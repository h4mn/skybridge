# Evolution Analysis — Sky-RPC

**Contexto:** Análise da evolução do Sky-RPC desde sua concepção até a v0.3, identificando causas, motivações e padrões de decisão.

---

## Timeline de Evolução

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EVOLUÇÃO SKY-RPC                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  2025-12-25    2025-12-26        2025-12-27         2025-12-28              │
│  ADR004  ────►  ADR010  ──────►  SPEC002   ──────►  ADR014/SPEC004          │
│  JSON-RPC      Sky-RPC          v0.1/v0.2          v0.3 RPC-first           │
│  (canônico)    Ticket+Env       Envelope           Introspecção             │
│                (rompimento)     Estruturado        Dinâmica                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fase 1 — JSON-RPC como Contrato Canônico (ADR004)

### Data: 2025-12-25

### Contexto
- **Problema:** Divergências entre código, PRDs/SPECs/ADRs e OpenAPI
- **Sintoma:** Boilerplate de roteamento manual, drift entre rotas/registry/docs
- **Naming inconsistente:** `fileops_read` vs `fileops.read`

### Decisão
Adotar **JSON-RPC 2.0** via endpoint único `POST` como transporte canônico.

**Motivação:**
- Consolidar execução por `method`
- Reduzir boilerplate de roteamento
- Facilitar auto-descoberta
- Permitir políticas por operação (não por rota)

### Limitações Identificadas
```yaml
Trade-offs:
  Semântica HTTP por endpoint: ↓ (cache/idempotência/status codes por rota)
  OpenAPI por operação: ↓ (passa a documentar transporte, não cada operação)
  Interoperabilidade: ↑ (padrão JSON-RPC)
```

### Status: **SUBSTITUÍDA** pela ADR010

---

## Fase 2 — Rompimento com JSON-RPC (ADR010)

### Data: 2025-12-26

### Gatilho Crítico
**Problema real descoberto:** Schema rígido do GPT Custom Actions rejeita campos fora do modelo esperado.

### Diagrama de Causa (Ishikawa)

```
                            ┌───────────────────────────┐
                            │ Falha ao enviar `params`  │
                            └────────────┬──────────────┘
                                         │
 ┌───────────────────────┬────────────────┼────────────────────┬──────────────────────┐
 │ Ambiente Local        │ Binding Schema │ OpenRPC Mapping     │ API Remota           │
 ├───────────────────────┼────────────────┼────────────────────┼──────────────────────┤
 │ Schema rígido         │ additionalProperties:false    │ Campos não aninhados   │
 │ Validação antecipada  │ Falta de flatten reverso      │ Falta de suporte a meta│
 │ Anti-injection ativa  │ Erro antes do envio           │ Perda de semântica RPC │
 │ Erro no wrapper local │                               │ Rejeição de query      │
 └───────────────────────┴────────────────┴────────────────────┴──────────────────────┘
```

**Síntese:** A falha nasce no **cliente**, não no servidor. O binding local rejeita `params` por schema fechado e validação precoce.

### Decisão: Sky-RPC Ticket + Envelope

**Mudança radical:** Abandonar envelope JSON-RPC, criar formato próprio.

**Rotas canônicas:**
1. `GET /openapi` — Catálogo de contrato
2. `GET /ticket?method=dominio.caso` — Handshake
3. `POST /envelope` — Payload em detalhes flat

**Exemplo v0.1:**
```json
// Request
{
  "ticket_id": "a3f9b1e2",
  "detalhe": "README.md"
}

// Response
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

### Motivações Profundas

| Motivação | Descrição |
|-----------|-----------|
| **GPT Custom Actions** | Schema rígido rejeitava JSON-RPC; precisava de formato flat |
| **Payloads grandes** | `params` do JSON-RPC limitava envio de arquivos |
| **Simplicidade** | Remover camadas de schema redundantes |
| **Descoberta** | Facilitar via `GET /openapi` |

### Status: **SUBSTITUÍDA** pela ADR014, mas conceito base mantido

---

## Fase 3 — Envelope Estruturado (SPEC002 v0.1 → v0.2)

### Data: 2025-12-27

### Problemas da v0.1

| Problema | Impacto |
|----------|---------|
| `detalhe` e `detalhe_N` (flat) | Dificulta validação estrita de schemas complexos |
| Não expressa semântica | Intenção da operação não clara |
| Ambiguidade em múltiplos params | `detalhe_1`, `detalhe_2` não são auto-explicativos |
| Keyword em português | `detalhe` foge de padrões internacionais |

### Decisão: Envelope Estruturado

**Estrutura semântica:**
```json
{
  "ticket_id": "a3f9b1e2",
  "detail": {
    "context": "fileops.read",      // O contexto/domínio
    "subject": "README.md",          // A entidade-alvo
    "action": "read",                // A ação dentro do contexto
    "payload": {                     // Dados específicos
      "encoding": "utf-8",
      "line_limit": 100
    }
  }
}
```

### Compatibilidade via `oneOf`

**Decisão importante:** Manter compatibilidade legada através de `oneOf`.

```yaml
detail:
  oneOf:
    - type: string        # Legado v0.1
    - type: object        # Novo v0.2 estruturado
```

### Breaking Changes
- `detalhe` (pt-BR) → `detail` (en)
- `payload` obrigatório no formato estruturado
- `payload` deve ter `minProperties: 1`

### Status: **Evoluído** para v0.3

---

## Fase 4 — RPC-First Semântico (ADR014/SPEC004 v0.3)

### Data: 2025-12-28

### Problemas da v0.2

| Problema | Impacto |
|----------|---------|
| Sem introspecção runtime | Descoberta dinâmica de handlers não existe |
| Sem reload dinâmico | Alterar registry requer restart |
| `/openapi` estático | Pode ficar desalinhado do código |
| Clients hardcoded | Métodos precisam ser conhecidos antecipadamente |

### Decisão: RPC-First com Introspecção

**Novos endpoints:**
- `GET /discover` — Catálogo dinâmico de handlers ativos
- `POST /discover/reload` — Reload do registry sem restart

**Envelope v0.3 — novos campos opcionais:**
```json
{
  "ticket_id": "uuid",
  "detail": {
    "context": "fileops",
    "action": "read",
    "subject": "docs/adr/ADR005.md",
    "scope": "tenant:sky",        // NOVO: Escopo multi-tenant
    "options": { "limit": 100 },  // NOVO: Opções específicas
    "payload": { ... }            // AGORA OPCIONAL (era obrigatório)
  }
}
```

### Emendment 1: OpenAPI Híbrido (ADR016)

**Ambiguidade criada:** "/openapi estático" foi interpretado como 100% estático.

**Correção:**
- **Operações HTTP:** Estáticas (definidas em YAML)
- **Schemas:** Dinâmicos (injetados do registry em runtime)

```python
def _custom_openapi() -> dict:
    # 1. Carrega operações estáticas do YAML
    spec = yaml.safe_load("docs/spec/openapi/openapi.yaml")

    # 2. Coleta schemas do registry
    discovery = get_skyrpc_registry().get_discovery()

    # 3. Injeta schemas dinâmicos
    for method_name, handler_meta in discovery.discovery.items():
        spec["components"]["schemas"][f"{method_name}Input"] = handler_meta.input_schema
        spec["components"]["schemas"][f"{method_name}Output"] = handler_meta.output_schema

    return spec
```

### Status: **ESTÁVEL** — versão atual

---

## Críticas Construtivas ao Sky-RPC

### 1. Volatilidade de Decisões

**Observação:**
- ADR004 → ADR010: **1 dia** (rompimento com JSON-RPC)
- v0.1 → v0.2: **1 dia** (envelope estruturado)
- v0.2 → v0.3: **1 dia** (introspecção)

**Crítica:** Evolução muito rápida pode indicar falta de prototipagem adequada antes de documentar ADRs.

**Sugestão:** Para futuras mudanças arquiteturais:
1. Criar PoC sem ADR
2. Validar em runtime
3. Só então documentar ADR definitivo

### 2. Complexidade Crescente

```
v0.1 (flat):      { ticket_id, detalhe }
v0.2 (estrut):    { ticket_id, detail: {context, subject, action, payload} }
v0.3 (introspec): { ticket_id, detail: {context, subject, action, scope, options, payload} }
```

**Crítica:** Envelope cresce em complexidade. v0.1 era simples para GPT Custom; v0.3 requer mais configuração.

**Risco:** Barreira de entrada para integrações simples.

**Sugestão:**
- Manter v0.1 como "Sky-RPC Lite" para casos simples
- v0.3 como "Sky-RPC Pro" para casos avançados

### 3. Ambiguidade de "Estático" vs "Dinâmico"

**Observação:** ADR014 teve que ser emendada por ADR016 devido a ambiguidade.

**Crítica:** Terminologia imprecisa gerou retrabalho.

**Sugestão:** Usar termos mais específicos:
- "Operações HTTP declarativas" (não "estáticas")
- "Schemas derivados de runtime" (não "dinâmicos")

### 4. Inglês vs Português

**Observação:**
- v0.1: `detalhe` (pt-BR)
- v0.2+: `detail` (en)

**Crítica:** Inconsistência inicial criou technical debt.

**Sugestão:** Definir desde o início:
- Keywords técnicas: inglês (`detail`, `context`, `action`)
- Domínio de negócio: flexível

### 5. Ticket como Obrigatório

**Observação:** Fluxo sempre requer 2 chamadas:
1. `GET /ticket`
2. `POST /envelope`

**Crítica:** Para operações simples (ex: health check), 2 round-trips é overhead.

**Sugestão:** Implementar "one-shot RPC" opcional:
```yaml
# Alternativa para operações idempotentes simples
POST /envelope?method=health
{ "detail": { "context": "health", "action": "check" } }
```

### 6. Compatibilidade via `oneOf`

**Observação:** v0.2 mantém compatibilidade com v0.1 via `oneOf`.

**Crítica:** Isso cria complexidade de validação e manutenção de código paralelo.

**Risco:** Acúmulo de debt de compatibilidade.

**Sugestão:**
- Definir política de depreciação explícita
- v0.1 descontinuada após X meses
- Forçar migração com warnings

### 7. Falta de Validação de Schema

**Observação:** v0.2 define `input_schema` e `output_schema` em metadados, mas não há validação automática em runtime.

**Crítica:** Schema é documentação, não contrato executável.

**Sugestão:** Implementar validação de schema em runtime:
```python
def validate_input(method: str, payload: dict):
    schema = registry.get_input_schema(method)
    jsonschema.validate(payload, schema)
```

---

## Pontos Positivos do Sky-RPC

### 1. ROMPIMENTO COM JSON-RPC

**Decisão corajosa:** Abandonar padrão estabelecido quando não atende às necessidades.

**Resultado:** Formato próprio que atende melhor o caso de uso (GPT Custom).

### 2. SEMÂNTICA EXPLÍCITA

`context`, `subject`, `action` expressam intenção melhor que `params` genérico.

### 3. INTROSPECÇÃO RUNTIME

`/discover` é feature poderosa para ferramentas de desenvolvimento.

### 4. OPENAPI HÍBRIDO

Correção inteligente: operações estáticas + schemas dinâmicos = melhor dos dois mundos.

### 5. COMPATIBILIDADE REVERSA

`oneOf` permitiu migração sem breaking change abrupto.

---

## Lições Aprendidas

### 1. Prototipar Antes de Documentar ADR

```
❌ Errado:  ADR → Implementação → Descobrir problema → Novo ADR
✅ Certo:   PoC → Validação → ADR Definitivo → Implementação
```

### 2. Terminologia Precisa Evita Retrabalho

"Estático" e "dinâmico" são termos sobrecarregados. Seja específico.

### 3. Evolução Incremental vs Mudança Radical

| Abordagem | Quando Usar |
|-----------|-------------|
| **Incremental** | Melhorias de UX, novas features |
| **Radical** | Contrato base não atinge objetivos |

Sky-RPC usou radical quando JSON-RPC provou ser insuficiente (correto).

### 4. Compatibilidade Tem Custo

`oneOf` simplifica migração, mas cria complexidade permanente. Políticas de depreciação são essenciais.

---

## Tabela de Comparação de Versões

| Aspecto | v0.1 (ADR010) | v0.2 (SPEC002) | v0.3 (SPEC004) |
|---------|---------------|----------------|----------------|
| **Envelope** | `detalhe` flat | `detail` estruturado | + `scope`, `options` |
| **Payload** | Opcional | Obrigatório (`minProperties: 1`) | Opcional |
| **Keyword** | pt-BR (`detalhe`) | en (`detail`) | en (`detail`) |
| **Introspecção** | ❌ | ❌ | ✅ `/discover` |
| **Reload** | ❌ | ❌ | ✅ `/discover/reload` |
| **OpenAPI** | Estático | Estático | Híbrido |
| **Compatibilidade** | — | `oneOf` com v0.1 | ✅ com v0.2 |
| **Complexidade** | Baixa | Média | Alta |
| **Flexibilidade** | Baixa | Média | Alta |

---

## Próximos Passos Sugeridos

### Curto Prazo
1. **Validação de schema em runtime** — Tornar schemas executáveis, não só documentação
2. **Política de depreciação** — Definir timeline para remover v0.1/v0.2
3. **Sky-RPC Lite** — Manter versão simplificada para casos simples

### Médio Prazo
4. **Client generation** — Gerar clientes TypeScript/Python a partir de `/discover`
5. **Rate limiting por ticket** — Prevenir abuso do handshake
6. **Assinatura de envelope** — Garantir integridade payload-to-tick

### Longo Prazo
7. **WebSocket RPC** — Para operações longas (streaming)
8. **Batch RPC** — Executar múltiplas operações em um envelope
9. **RPC versioning** — Suportar múltiplas versões simultâneas

---

## Conclusão

O Sky-RPC passou por uma evolução rápida e significativa em poucos dias, motivada principalmente por:

1. **Limitações do GPT Custom Actions** — Gatilho principal do rompimento com JSON-RPC
2. **Necessidade de semântica** — Evolução de flat para estruturado
3. **Introspecção runtime** — Necessidade de discovery dinâmico

**Decisões acertadas:**
- Abandonar JSON-RPC quando não atendia às necessidades
- Adotar envelope estruturado semântico
- Implementar introspecção runtime
- Corrigir ambiguidade de OpenAPI estático/dinâmico

**Áreas de melhoria:**
- Prototipagem antes de ADR
- Terminologia mais precisa
- Política de depreciação explícita
- Validação de schema em runtime

---

> "Evoluir é preciso; romper quando necessário, corrigir sempre." – made by Sky 🔄
