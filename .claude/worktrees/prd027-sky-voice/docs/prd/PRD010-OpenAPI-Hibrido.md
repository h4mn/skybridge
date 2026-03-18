---
status: proposta
data: 2025-12-28
relacionado:
  - ADR016-openapi-hibrido-estatico-dinamico.md
  - ADR013-adotar-yamllint-openapi-validator.md
  - ADR014-evoluir-sky-rpc.md
  - PRD009-Sky-RPC-v0.3-RPC-first-Semantico.md
  - SPEC004-Sky-RPC-v0.3.md
  - PB010-redocly-cli-openapi.md
---

# PRD010 — OpenAPI Híbrido (Operações Estáticas, Schemas Dinâmicos)

## 1) Problema

As decisões anteriores sobre OpenAPI (ADR013, ADR014) criaram ambiguidade:
- **ADR013** define OpenAPI como "estático", validado com openapi-spec-validator
- **ADR014** estabelece dois contratos: estático (`/openapi`) e dinâmico (`/discover`)
- **ADR005** diz que "operações passam a ser auto-documentadas via OpenAPI"
- **PRD009** especifica handlers com `input_schema` e `output_schema` no runtime

A interpretação literal de "OpenAPI estático" levou a:
- Esforço manual para manter sincronia entre código e documentação
- Workaround de mesclagem YAML no Python
- Testes pulados (openapi-spec-validator não suporta `$ref` externos)
- Gap crescente entre documentação e runtime
- Risco de drift: handlers novos não aparecem na documentação

## 2) Objetivo

Implementar **OpenAPI Híbrido** que combina:
- **Operações HTTP estáticas** — Definidas em `docs/spec/openapi/openapi.yaml`
- **Schemas dinâmicos** — Gerados automaticamente do registry runtime
- **Validação robusta** — Redocly CLI substituindo openapi-spec-validator

## 3) Escopo

### Inclui

- Modificação de `_custom_openapi()` para injetar schemas dinâmicos do registry
- Atualização do endpoint `/openapi` para retornar spec híbrido
- Simplificação de `docs/spec/openapi/openapi.yaml` (apenas operações, placeholders para schemas)
- Adoção de **Redocly CLI** para validação
- Criação de `redocly.yaml` com configuração recomendada
- Atualização de testes para usar Redocly CLI
- Emenda de ADR013 e ADR014 com referência a ADR016
- Criação de PB010 (playbook do Redocly CLI)

### Não inclui

- Mudança nas operações HTTP (`/ticket`, `/envelope`, `/discover`, `/health`)
- Alteração no comportamento do `/discover` (permanece dinâmico)
- Mudança no contrato Sky-RPC (mantém PRD009)
- Substituição do FastAPI ou mudança de framework

## 4) Requisitos Funcionais

### OpenAPI Híbrido

| ID | Descrição |
|----|-----------|
| **RF1** | `GET /openapi` retorna operações definidas no YAML estático |
| **RF2** | `GET /openapi` retorna schemas gerados do registry runtime |
| **RF3** | Schemas de handlers (`{method}Input`, `{method}Output`) são injetados dinamicamente |
| **RF4** | Schemas reutilizáveis (`TicketResponse`, `EnvelopeRequest`, etc.) são gerados via código |
| **RF5** | OpenAPI resultante é válido (OpenAPI 3.1.0) |
| **RF6** | Mudanças no registry (novos handlers) refletem imediatamente no `/openapi` |

### Operações Estáticas

| ID | Descrição |
|----|-----------|
| **RF7** | Operações HTTP são definidas em `docs/spec/openapi/openapi.yaml` |
| **RF8** | Operações canônicas: `/ticket`, `/envelope`, `/discover`, `/discover/reload`, `/health` |
| **RF9** | Cada operação tem `operationId`, `summary`, `tags` |
| **RF10** | Operações só mudam via edição do YAML (não em runtime) |

### Validação

| ID | Descrição |
|----|-----------|
| **RF11** | `redocly lint` valida `openapi.yaml` sem erros |
| **RF12** | Validação estática acontece em CI/CD |
| **RF13** | `openapi-spec-validator` é removido das dependências |
| **RF14** | Testes usam Redocly CLI via `subprocess` |

### Compatibilidade

| ID | Descrição |
|----|-----------|
| **RF15** | Clients existentes continuam funcionando |
| **RF16** | Versão do OpenAPI muda para refletir modelo híbrido |
| **RF17** | `/discover` permanece inalterado |

## 5) Requisitos Não Funcionais

| ID | Descrição |
|----|-----------|
| **RNF1** | `GET /openapi` responde em < 200ms |
| **RNF2** | Geração de schemas não impacta performance de handlers |
| **RNF3** | OpenAPI gerado é idêntico em todas as requisições (mesmo registry) |
| **RNF4** | Validação Redocly leva < 5s |
| **RNF5** | `redocly.yaml` é simples e manutenível |

## 6) DOD (Definition of Done)

### DOD1 — Redocly CLI

- [ ] Redocly CLI instalado (`redocly --version` funciona)
- [ ] `redocly.yaml` criado na raiz
- [ ] `redocly lint docs/spec/openapi/openapi.yaml` passa sem erros
- [ ] CI/CD atualizado com validação Redocly
- [ ] PB010 criado com playbook completo

### DOD2 — OpenAPI Híbrido

- [ ] `_custom_openapi()` em `app.py` injeta schemas do registry
- [ ] `/openapi` endpoint retorna YAML híbrido
- [ ] `docs/spec/openapi/openapi.yaml` simplificado (apenas operações)
- [ ] Placeholders de schemas são sobrescritos em runtime
- [ ] `curl /openapi` mostra schemas dinâmicos

### DOD3 — Testes

- [ ] `test_openapi_schema.py` atualizado para usar Redocly CLI
- [ ] `test_openapi_spec_valid` antigo removido/alterado
- [ ] `test_openapi_hybrid.py` criado (novos testes)
- [ ] Teste verifica sincronização entre `/openapi` e `/discover`
- [ ] Teste verifica operações estáticas presentes
- [ ] 100% dos testes passam

### DOD4 — Documentação

- [ ] ADR013 emendada com referência a ADR016
- [ ] ADR014 emendada com referência a ADR016
- [ ] SPEC004 atualizada com seção "OpenAPI Híbrido"
- [ ] PRD009 atualizado se necessário
- [ ] Changelog atualizado

### DOD5 — Limpeza

- [ ] Mesclagem manual de YAML removida (`_load_openapi_text()` simplificado)
- [ ] `openapi-spec-validator` removido das dependências
- [ ] Workarounds de `$ref` externos removidos
- [ ] `common.yaml` removido ou arquivado se não usado

## 7) Exemplos

### 7.1 OpenAPI Final

```yaml
# Retornado por GET /openapi (híbrido)

openapi: 3.1.0
info:
  title: Skybridge Public API
  version: 0.3.0

paths:
  # === ESTÁTICO (do YAML) ===
  /ticket:
    get:
      operationId: createTicket
      summary: Criar ticket de execução
      parameters: [...]
      responses:
        '200':
          schema:
            $ref: '#/components/schemas/TicketResponse'

  /envelope:
    post:
      operationId: executeEnvelope
      summary: Executar operação RPC
      requestBody:
        schema:
          $ref: '#/components/schemas/EnvelopeRequest'

  /discover:
    get:
      operationId: listHandlers
      summary: Listar handlers ativos
      responses:
        '200':
          schema:
            $ref: '#/components/schemas/SkyRpcDiscovery'

components:
  schemas:
    # === DINÂMICO (do registry) ===
    fileops.readInput:
      type: object
      properties:
        path: { type: string }
      required: [path]

    fileops.readOutput:
      type: object
      properties:
        content: { type: string }

    healthInput:
      type: object

    healthOutput:
      type: object
      properties:
        status: { type: string }

    # === GERADOS (reutilizáveis) ===
    TicketResponse:
      type: object
      properties:
        ok: { type: boolean }
        ticket: { type: object }

    EnvelopeRequest:
      type: object
      additionalProperties: true
      properties:
        ticket_id: { type: string, format: uuid }
        detail: { type: object }
```

### 7.2 Fluxo de Geração

```python
# Pseudocódigo de _custom_openapi()

def _custom_openapi():
    # 1. Carrega YAML estático
    spec = yaml.load("docs/spec/openapi/openapi.yaml")

    # 2. Coleta schemas do registry
    discovery = registry.get_discovery()

    # 3. Injeta schemas dinâmicos
    for method, meta in discovery.discovery.items():
        spec["components"]["schemas"][f"{method}Input"] = meta.input_schema
        spec["components"]["schemas"][f"{method}Output"] = meta.output_schema

    # 4. Gera schemas reutilizáveis
    spec["components"]["schemas"]["TicketResponse"] = _gen_ticket_schema()
    spec["components"]["schemas"]["EnvelopeRequest"] = _gen_envelope_schema()

    return spec
```

## 8) Cronograma

| Fase | Atividades | Dependências |
|-------|------------|---------------|
| **Fase 1** | Instalar Redocly CLI, criar config | - |
| **Fase 2** | Modificar `_custom_openapi()`, atualizar `/openapi` | Fase 1 |
| **Fase 3** | Simplificar `openapi.yaml`, remover workarounds | Fase 2 |
| **Fase 4** | Atualizar testes, criar testes híbridos | Fase 3 |
| **Fase 5** | Emendar ADRs, atualizar SPEC | Fase 4 |
| **Fase 6** | CI/CD com Redocly, documentação final | Fase 5 |

## 9) Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Performance degrade com geração dinâmica | Baixa | Médio | Cache de spec, lazy loading |
| OpenAPI gerado fica inválido | Baixa | Alto | Testes automatizados, validação |
| Redocly CLI tem bugs | Baixa | Médio | Testar antes de adotar |
| Confusão sobre o que é estático/dinâmico | Média | Baixo | Documentação clara, exemplos |
| Clients quebram com mudança | Baixa | Alto | Testes de compatibilidade |

## 10) Critérios de Sucesso

- ✅ Redocly CLI valida `openapi.yaml` sem erros
- ✅ `GET /openapi` retorna schemas do registry
- ✅ Schemas estão sincronizados com `/discover`
- ✅ Operações HTTP permanecem estáveis
- ✅ Zero esforço manual para manter schemas atualizados
- ✅ 100% dos testes passam
- ✅ CI/CD valida OpenAPI em cada PR

## 11) Próximos Passos

1. Revisar e aprovar ADR016
2. Revisar e aprovar PRD010
3. Seguir PB010 para instalação do Redocly CLI
4. Implementar seguindo Fases 1-6
5. Testar e validar

---

## Referências

- [ADR016 — OpenAPI Híbrido](../adr/ADR016-openapi-hibrido-estatico-dinamico.md)
- [PB010 — Redocly CLI](../playbook/PB010-redocly-cli-openapi.md)
- [PRD009 — Sky-RPC v0.3](./PRD009-Sky-RPC-v0.3-RPC-first-Semantico.md)
- [SPEC004 — Sky-RPC v0.3](../spec/SPEC004-Sky-RPC-v0.3.md)

---

> "O melhor de dois mundos: estável onde importa, dinâmico onde evolui."
> — made by Sky 🔄✨
