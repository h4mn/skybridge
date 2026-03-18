# SPEC006 — Estrutura de Specs (Contratos e Esquemas)

---

status: estável
version: 1.0.0
---

## 1) Visão Geral

Este documento define a estrutura canônica do diretório `docs/spec/`, que contém contratos, esquemas e especificações técnicas da Skybridge.

**Objetivo:** Padronizar a organização de especificações para facilitar descoberta, manutenção e geração de código/tooling.

---

## 2) Estrutura Canônica

```
docs/spec/
├─ openapi/                 # Contrato público HTTP (rotas, parâmetros, responses)
│  ├─ openapi.yaml         # OpenAPI principal com refs para contexts
│  └─ v1/                  # Versionamento de contrato (futuro)
│     └─ skybridge.yaml
│
├─ discover/                # Contrato de introspecção runtime
│  └─ discover-spec.yaml   # Schema de SkyRpcDiscovery
│
├─ contexts/                # Schemas por domínio/contexto (reutilizáveis)
│  ├─ common.yaml          # Schemas compartilhados (Envelope, Error, Result)
│  ├─ fileops.yaml         # Schemas específicos de FileOps
│  ├─ tasks.yaml           # Schemas específicos de Tasks
│  ├─ auth.yaml            # Schemas de autenticação/autorização
│  └─ health.yaml          # Schemas de health checks
│
└─ *.md                     # SPECs narrativas (SPEC001-SPEC005+)
   ├─ SPEC001-baseline-seguranca-llm.md
   ├─ SPEC002-Sky-RPC-v0.1.md
   ├─ SPEC003-Sky-RPC-v0.2.md
   ├─ SPEC004-Sky-RPC-v0.3.md
   └─ SPEC005-documentacao-metadados.md
```

---

## 3) Diretórios e Arquivos

### 3.1) `specs/openapi/`

**Propósito:** Contrato público HTTP exposto via `GET /openapi`

**Conteúdo:**
- Definição de rotas (`/ticket`, `/envelope`, `/discover`, etc.)
- Referências para schemas em `specs/contexts/`
- Metadados de versão, segurança, servidores

**Exemplo de estrutura:**

```yaml
# specs/openapi/openapi.yaml
openapi: 3.1.0
info:
  title: Skybridge Public API
  version: 0.3.0

paths:
  /ticket:
    get:
      summary: Cria ticket de execução
      # ...

  /envelope:
    post:
      summary: Executa operação RPC
      requestBody:
        content:
          application/json:
            schema:
              $ref: '../contexts/common.yaml#/components/schemas/EnvelopeRequest'
```

**Naming:** `openapi.yaml` (ou `skybridge.yaml`)

---

### 3.2) `specs/discover/`

**Propósito:** Contrato de introspecção runtime (descoberta dinâmica de handlers)

**Conteúdo:**
- Schema `SkyRpcDiscovery`
- Metadados de handler: `method`, `kind`, `module`, `input_schema`, `output_schema`

**Exemplo de estrutura:**

```yaml
# specs/discover/discover-spec.yaml
openapi: 3.1.0
info:
  title: Skybridge Runtime Discovery API
  version: 0.3.0

components:
  schemas:
    SkyRpcDiscovery:
      type: object
      properties:
        version: { type: string }
        discovery:
          type: object
          additionalProperties:
            $ref: '../contexts/common.yaml#/components/schemas/SkyRpcHandler'
```

**Naming:** `discover-spec.yaml`

---

### 3.3) `specs/contexts/`

**Propósito:** Schemas por domínio/contexto (reutilizáveis via `$ref`)

**Conteúdo:** Schemas JSON/YAML organizados por bounded context

| Arquivo | Conteúdo |
|---------|----------|
| `common.yaml` | EnvelopeRequest, EnvelopeResponse, Error, Result, Ticket |
| `fileops.yaml` | FileOpsRequest, FileOpsResponse, FileMetadata |
| `tasks.yaml` | Task, Note, Group, List, TaskEvent |
| `auth.yaml` | AuthRequest, AuthResponse, TokenInfo |
| `health.yaml` | HealthResponse, HealthStatus |

**Exemplo de estrutura:**

```yaml
# specs/contexts/common.yaml
components:
  schemas:
    EnvelopeRequest:
      type: object
      properties:
        ticket_id: { type: string, format: uuid }
        detail:
          type: object
          properties:
            context: { type: string }
            action: { type: string }
            subject: { type: string }
            scope: { type: string }
            options: { type: object, additionalProperties: true }
            payload: { type: object, additionalProperties: true }
          required: [context, action]

    EnvelopeResponse:
      type: object
      properties:
        ok: { type: boolean }
        id: { type: string, format: uuid }
        result: { type: object, additionalProperties: true }
        error:
          $ref: '#/components/schemas/Error'

    Error:
      type: object
      properties:
        code: { type: integer }
        message: { type: string }
        details: { type: object }
      required: [code, message]
```

**Naming:** `<context>.yaml` (snake_case, singular)

**Regras:**
- Schemas reutilizáveis vão em `common.yaml`
- Schemas específicos de um contexto vão no arquivo do contexto
- Use `$ref` para referenciar schemas entre arquivos

---

## 4) Referências entre Arquivos

### 4.1) Path relativo para `$ref`

```yaml
# De openapi.yaml para contexts/
$ref: '../contexts/common.yaml#/components/schemas/EnvelopeRequest'

# De discover-spec.yaml para contexts/
$ref: '../contexts/common.yaml#/components/schemas/SkyRpcHandler'

# De fileops.yaml para common.yaml
$ref: './common.yaml#/components/schemas/Error'
```

### 4.2) Hierarquia de dependências

```
openapi.yaml
  └─ contexts/common.yaml
  └─ contexts/fileops.yaml
     └─ contexts/common.yaml

discover-spec.yaml
  └─ contexts/common.yaml
```

---

## 5) Versionamento

### 5.1) Versionamento de Specs

| Versão | Arquivo | Status |
|--------|---------|--------|
| 1.0.0 | SPEC006 | Estável (este documento) |

### 5.2) Versionamento de Contratos

- **OpenAPI:** Versionado em `info.version` (ex: `0.3.0`)
- **Sky-RPC:** Versionado via SPEC (SPEC002, SPEC003, SPEC004)
- **Schemas de contexto:** Versionado via git, sem numeração explícita

### 5.3) Compatibilidade

- Mudanças **backward-compatible**: incrementar `MINOR` (ex: `0.3.0` → `0.4.0`)
- Mudanças **breaking**: incrementar `MAJOR` (ex: `0.3.0` → `1.0.0`)

---

## 6) Convenções de Nomenclatura

### 6.1) Arquivos YAML

| Tipo | Padrão | Exemplo |
|------|--------|---------|
| OpenAPI principal | `openapi.yaml` ou `<service>.yaml` | `openapi.yaml`, `skybridge.yaml` |
| Contrato específico | `<feature>-spec.yaml` | `discover-spec.yaml` |
| Contexto | `<context>.yaml` | `fileops.yaml`, `tasks.yaml` |

### 6.2) Schemas

| Tipo | Padrão | Exemplo |
|------|--------|---------|
| Request | `<Context>Request` | `FileOpsRequest` |
| Response | `<Context>Response` | `FileOpsResponse` |
| Entidade | `<Nome>` | `Task`, `FileMetadata` |
| Enum | `<Nome>Enum` | `TaskStatusEnum` |

---

## 7) Validação

### 7.1) Ferramentas

| Ferramenta | Uso |
|------------|-----|
| **yamllint** | Valida sintaxe YAML |
| **openapi-spec-validator** | Valida contra spec OpenAPI 3.1 |
| **spectral** (opcional) | Lint de regras customizadas |

### 7.2) CI/CD

```yaml
# .github/workflows/validate-specs.yml
name: Validate Specs

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Validate YAML
        run: |
          yamllint docs/spec/**/*.yaml

      - name: Validate OpenAPI
        run: |
          openapi-spec-validator docs/spec/openapi/openapi.yaml
```

---

## 8) Integração com Código

### 8.1) Geração de código

Schemas em `specs/contexts/` podem ser usados para gerar:

- **TypeScript types** (via quicktype ou similar)
- **Python dataclasses** (via datamodel-code-generator)
- **Validação em runtime** (via pydantic, jsonschema)

### 8.2) Documentação

- `GET /openapi` expõe o contrato público
- `GET /discover` expõe handlers dinâmicos (v0.3+)

---

## 9) Exemplo Completo de Fluxo

```
1. Cliente chama GET /openapi
   → Retorna specs/openapi/openapi.yaml

2. Cliente descobre operação fileops.read
   → openapi.yaml referencia contexts/fileops.yaml

3. Cliente chama GET /ticket?method=fileops.read
   → Server valida contra schemas/contexts/fileops.yaml

4. Cliente chama POST /envelope
   → Payload validado contra EnvelopeRequest (common.yaml)
```

---

## 10) Migração

### Estado Atual
- `docs/spec/` contém apenas arquivos `.md` (SPEC001-SPEC005)
- Subdiretórios `openapi/`, `discover/`, `contexts/` **não existem ainda**

### Passos para Implementação

1. Criar estrutura de diretórios
   ```bash
   mkdir -p docs/spec/{openapi,discover,contexts}
   ```

2. Mover/conteúdo dos contratos existentes para `specs/openapi/`

3. Criar `specs/contexts/common.yaml` com schemas base

4. Criar `specs/contexts/fileops.yaml` com schemas específicos

5. Atualizar referências em SPEC004, PRD009 e ADR014

6. Adicionar validação no CI/CD

---

## Referências

- [ADR014 — Evoluir Sky-RPC para arquitetura RPC-first semântica](../adr/ADR014-evoluir-sky-rpc.md)
- [SPEC004 — Sky-RPC v0.3](./SPEC004-Sky-RPC-v0.3.md)
- [PRD009 — Sky-RPC v0.3 (RPC-first Semântico)](../prd/PRD009-Sky-RPC-v0.3-RPC-first-Semantico.md)
- [OpenAPI Specification 3.1.0](https://spec.openapis.org/oas/v3.1.0)

---

> "Estrutura bem definida é metade da documentação." – made by Sky 📐
