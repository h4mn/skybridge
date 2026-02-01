---
status: aceito
data: 2025-12-28
supersedes:
  - ADR013-adotar-yamllint-openapi-validator
  - ADR014-evoluir-sky-rpc (parcialmente - seção OpenAPI estático)
responsavel: arquitetura.skybridge
related:
  - PRD009-Sky-RPC-v0.3-RPC-first-Semantico
  - SPEC004-Sky-RPC-v0.3
  - ADR005-padronizar-naming-operacoes-auto-descoberta
---

# ADR016 — OpenAPI Híbrido: Operações Estáticas, Schemas Dinâmicos

## Contexto

As decisões anteriores sobre OpenAPI criaram ambiguidade:

- **ADR013**: Define OpenAPI como estático, validado com yamllint + openapi-spec-validator
- **ADR014**: Estabelece dois contratos: estático (`/openapi`) e dinâmico (`/discover`)
- **ADR005**: Diz que "operações passam a ser auto-documentadas via OpenAPI"
- **PRD009**: Especifica handlers com `input_schema` e `output_schema` no runtime

**Problema**: A interpretação de "OpenAPI estático" levou a acreditar que **tudo** seria estático (operações + schemas), criando um gap entre:
- O registro runtime (que tem schemas dinâmicos)
- O arquivo OpenAPI (que precisaria ser manualmente atualizado)

Isso resultou em:
1. Esforço manual para manter OpenAPI sincronizado com o código
2. Risco de drift entre documentação e runtime
3. Testes pulados (openapi-spec-validator não suporta `$ref` externos)
4. Workaround de mesclagem manual de YAML no Python

## Decisão

**Adotar OpenAPI híbrido:**

1. **Operações (rotas HTTP): ESTÁTICAS**
   - Definidas manualmente em `docs/spec/openapi/openapi.yaml`
   - Incluem: `/ticket`, `/envelope`, `/discover`, `/health`, `/privacy`
   - Versionadas e estáveis ao longo do tempo
   - Validadas com yamllint

2. **Schemas (componentes): DINÂMICOS**
   - Gerados automaticamente a partir do registry runtime
   - `input_schema` e `output_schema` vêm dos decorators `@query`/`@command`
   - Injetados no OpenAPI em tempo de resposta do endpoint `/openapi`
   - Sempre sincronizados com o código

3. **Adotar Redocly CLI**
   - Para validação de arquivos OpenAPI
   - Para bundle de `$ref` externos (se usado)
   - Substitui openapi-spec-validator (limitado)

## Arquitetura

### Estrutura do OpenAPI Híbrido

```yaml
# docs/spec/openapi/openapi.yaml (ESTÁTICO - operações)

openapi: 3.1.0
info:
  title: Skybridge Public API
  version: 0.3.0

# Rotas HTTP são definidas estaticamente
paths:
  /ticket:
    get:
      summary: Criar ticket de execução
      parameters: [...]
      # responsesschemas são PLACEHOLDERS, sobrescritos em runtime
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TicketResponse'

  /envelope:
    post:
      summary: Executar operação RPC
      # requestBody schema é PLACEHOLDER
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EnvelopeRequest'

# Schemas são GERADOS DINAMICAMENTE em runtime
components:
  schemas:
    # Placeholders - substituídos pelo registry em runtime
    TicketResponse: { type: object }
    EnvelopeRequest: { type: object }
    # ... outros schemas
```

### Fluxo de Geração

```python
# Em runtime, ao responder GET /openapi:

def get_openapi_document() -> dict:
    # 1. Carrega operações estáticas
    spec = load_yaml("docs/spec/openapi/openapi.yaml")

    # 2. Coleta schemas do registry
    discovery = get_skyrpc_registry().get_discovery()

    # 3. Injeta schemas dinâmicos no components.schemas
    for method_name, handler_metadata in discovery.discovery.items():
        spec["components"]["schemas"][f"{method_name}Request"] = handler_metadata.input_schema
        spec["components"]["schemas"][f"{method_name}Response"] = handler_metadata.output_schema

    # 4. Atualiza schemas reutilizáveis
    spec["components"]["schemas"]["TicketResponse"] = generate_ticket_response_schema()
    spec["components"]["schemas"]["EnvelopeRequest"] = generate_envelope_request_schema()
    spec["components"]["schemas"]["EnvelopeResponse"] = generate_envelope_response_schema()

    return spec
```

## Redocly CLI

**Playbook completo:** `docs/playbook/PB010-redocly-cli-openapi.md`

**Instalação rápida:**
```bash
npm install -g @redocly/cli
```

**Comandos essenciais:**
```bash
# Validar
redocly lint docs/spec/openapi/openapi.yaml

# Bundle (resolver $refs)
redocly bundle docs/spec/openapi/openapi.yaml -o dist/openapi-bundled.yaml

# Preview local
redocly preview-docs docs/spec/openapi/openapi.yaml
```

## Regras e Invariantes

1. **Operações HTTP** são imutáveis em runtime (só mudam via código)
2. **Schemas de componentes** são gerados do registry em tempo real
3. **Placeholders** no YAML estático são sobrescritos dinamicamente
4. **Valição estática** com Redocly CLI (não mais openapi-spec-validator)
5. **Versionamento** segue mudanças nas operações, não nos schemas

## Especificação Técnica

### Arquivos Modificados

```
src/skybridge/platform/
├── bootstrap/app.py
│   └── _custom_openapi()  # Agora injeta schemas dinâmicos
└── delivery/routes.py
    └── /openapi endpoint  # Retorna OpenAPI híbrido
```

### Arquivos Novos

```
tools/
└── redocly/
    ├── redocly.yaml       # Config do Redocly
    └── validate.sh        # Script de validação
```

## Alternativas Consideradas

| Opção | Descrição | Por que NÃO? |
|-------|-----------|--------------|
| **OpenAPI 100% estático** | Tudo manual, como ADR013 original | Drift com runtime, esforço manual |
| **OpenAPI 100% dinâmico** | Gerar tudo do registry | Perde estabilidade de contrato para clientes |
| **Schema Registry externo** | Usar ferramenta como Apicurio | Overhead, mais complexidade |
| **Geração em build-time** | Script pré-deploy | Não reflete runtime real |

## Consequências

### Positivas

- ✅ Contrato HTTP estável para clientes (`/ticket`, `/envelope`)
- ✅ Schemas sempre sincronizados com o código
- ✅ Validação com Redocly CLI (robusto, suporta refs)
- ✅ Melhor que ADR013/014 individuais (combina melhor dos dois)
- ✅ Zero esforço manual para manter schemas atualizados

### Negativas

- ❌ Mais complexidade no endpoint `/openapi`
- ❌ OpenAPI não é mais "arquivo puro" (modificado em runtime)
- ❌ Documentação visual precisa de runtime para ver schemas completos
- ❌ Cache pode ser necessário se performance for problema

## Referências

- [PRD010 — OpenAPI Híbrido](./prd/PRD010-OpenAPI-Hibrido.md)
- [PB010 — Redocly CLI para OpenAPI](./playbook/PB010-redocly-cli-openapi.md)
- [ADR005 — Padronizar naming e auto-descoberta](./ADR005-padronizar-naming-operaes-auto-descoberta.md)
- [ADR013 — yamllint + openapi-validator](./ADR013-adotar-yamllint-openapi-validator.md) (emendado)
- [ADR014 — Evoluir Sky-RPC](./ADR014-evoluir-sky-rpc.md) (emendado)
- [PRD009 — Sky-RPC v0.3](./prd/PRD009-Sky-RPC-v0.3-RPC-first-Semantico.md)
- [SPEC004 — Sky-RPC v0.3](./spec/SPEC004-Sky-RPC-v0.3.md)
- [Redocly CLI Docs](https://redocly.com/docs/cli)

---

> "O melhor de dois mundos: estável onde importa, dinâmico onde evolui."
> — made by Sky 🔄✨

## Documentos Relacionados

- [TASK003 — Implementação do OpenAPI Híbrido](../task/TASK003-2025-12-28-18-17.md)
- [openapi-modular-refs-research.md](../report/openapi-modular-refs-research.md)
