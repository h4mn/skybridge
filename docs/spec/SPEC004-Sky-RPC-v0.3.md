# SPEC004 — Sky-RPC v0.3

---

status: estável
version: 0.3.0
supersedes:

* ADR010-adotar-sky-rpc
* SPEC002-Sky-RPC-v0.2

---

## 1) Visão geral

O Sky-RPC v0.3 é uma evolução incremental do v0.2, que consolida o envelope
estruturado e adiciona **introspecção de runtime** via `/discover`.

A estrutura de envelope definida em v0.2 é mantida, com novos campos opcionais
(`scope`, `options`) e a formalização do contrato dinâmico.

---

## 2) Estrutura de arquivos YAML

> **Estrutura completa de `docs/spec/` definida em [SPEC006](./SPEC006-Estrutura-de-Specs.md)**

```
specs/
├─ openapi/                 # Contrato público (rotas, parâmetros e responses)
│  └─ openapi.yaml
├─ discover/                # Introspecção runtime (descoberta de handlers)
│  └─ discover-spec.yaml
└─ contexts/                # Domínios e schemas reutilizáveis
   ├─ fileops.yaml
   ├─ tasks.yaml
   ├─ auth.yaml
   └─ common.yaml
```

### Exemplos:

#### `specs/openapi/openapi.yaml`

```yaml
openapi: 3.1.0
info:
  title: Skybridge Public API
  version: 0.3.0

paths:
  /ticket:
    get:
      summary: Cria ticket de execução
      parameters:
        - name: method
          in: query
          schema: { type: string }
      responses:
        '200': { description: OK }

  /envelope:
    post:
      summary: Executa operação RPC
      requestBody:
        content:
          application/json:
            schema:
              $ref: '../contexts/common.yaml#/components/schemas/EnvelopeRequest'
      responses:
        '200': { description: Resultado RPC }

  /discover:
    get:
      summary: Lista handlers ativos (introspecção)
      responses:
        '200':
          description: Lista de handlers
          content:
            application/json:
              schema:
                $ref: '../discover/discover-spec.yaml#/components/schemas/SkyRpcDiscovery'
```

#### `specs/discover/discover-spec.yaml`

```yaml
openapi: 3.1.0
info:
  title: Skybridge Runtime Discovery API
  version: 0.3.0

paths:
  /discover:
    get:
      summary: Lista handlers ativos
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SkyRpcDiscovery'

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

#### `specs/contexts/common.yaml`

```yaml
components:
  schemas:
    EnvelopeRequest:
      type: object
      properties:
        ticket_id: { type: string, format: uuid }
        detail:
          oneOf:
            - $ref: '#/components/schemas/EnvelopeDetailStruct'
            - $ref: '#/components/schemas/EnvelopeDetailString'

    EnvelopeDetailStruct:
      type: object
      properties:
        context: { type: string }
        action: { type: string }
        subject: { type: string }
        scope: { type: string }
        options: { type: object, additionalProperties: true }
        payload: { type: object, additionalProperties: true }
      required: [context, action]

    EnvelopeDetailString:
      type: string  # compatibilidade v0.2
```

---

## 2.1) Envelope v0.3 - Campos Novos

### Campos opcionais adicionados

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `scope` | string | Escopo da operação (multi-tenant) | `"tenant:sky"` |
| `options` | object | Opções específicas da operação | `{ limit: 100 }` |
| `payload` | object | **Agora opcional** em v0.3 | `{ encoding: "utf-8" }` |

### Compatibilidade

- **v0.2 exigia:** `payload` obrigatório com `minProperties: 1`
- **v0.3 permite:** `payload` opcional (operações simples sem parâmetros)

### Exemplo completo v0.3

```json
{
  "ticket_id": "a3f9b1e2-4c8d-4e5f-9a1b-2c3d4e5f6a7b",
  "detail": {
    "context": "fileops",
    "action": "read",
    "subject": "README.md",
    "scope": "tenant:sky",
    "options": { "limit": 100 },
    "payload": { "encoding": "utf-8" }
  }
}
```

### Exemplo mínimo v0.3 (sem payload)

```json
{
  "ticket_id": "b4f2c1e3-5d9e-5f6g-0b2c-3d4e5f6a7b8c",
  "detail": {
    "context": "health",
    "action": "check"
  }
}
```

---

## 3) Compatibilidade

| Versão         | Status       | Compatibilidade |
| -------------- | ------------ | --------------- |
| v0.1 (ADR010)  | Deprecada    | ❌               |
| v0.2 (SPEC002) | Experimental | ⚠️              |
| v0.3 (SPEC003) | Estável      | ✅               |

---

## 4) OpenAPI Híbrido (ADR016)

Conforme **[ADR016](../adr/ADR016-openapi-hibrido-estatico-dinamico.md)**, o Sky-RPC v0.3 adota o modelo de **OpenAPI Híbrido**:

### 4.1) Definição

| Componente      | Tipo       | Fonte                      |
|----------------|------------|----------------------------|
| **Operações HTTP** | Estáticas  | `docs/spec/openapi/openapi.yaml` |
| **Schemas**       | Dinâmicos | Registry runtime (`get_skyrpc_registry()`) |

### 4.2) Funcionamento

```python
# Em runtime (app.py), ao responder GET /openapi:

def _custom_openapi() -> dict:
    # 1. Carrega operações estáticas do YAML
    spec = yaml.safe_load("docs/spec/openapi/openapi.yaml")

    # 2. Coleta schemas do registry
    discovery = get_skyrpc_registry().get_discovery()

    # 3. Injeta schemas dinâmicos
    for method_name, handler_meta in discovery.discovery.items():
        spec["components"]["schemas"][f"{method_name}Input"] = handler_meta.input_schema
        spec["components"]["schemas"][f"{method_name}Output"] = handler_meta.output_schema

    # 4. Gera schemas reutilizáveis
    spec["components"]["schemas"]["TicketResponse"] = generate_ticket_response_schema()
    # ...

    return spec
```

### 4.3) Contratos

| Endpoint | Tipo      | Descrição |
|----------|-----------|-----------|
| `GET /openapi` | Híbrido | Operações estáticas + Schemas dinâmicos |
| `GET /discover` | Dinâmico | 100% gerado do registry runtime |

### 4.4) Validação

- **Estático:** `redocly lint docs/spec/openapi/openapi.yaml`
- **Dinâmico:** `curl -s http://localhost:8000/openapi | redocly lint -`

**Ver também:**
- [ADR016 — OpenAPI Híbrido](../adr/ADR016-openapi-hibrido-estatico-dinamico.md)
- [PRD010 — OpenAPI Híbrido](../prd/PRD010-OpenAPI-Hibrido.md)
- [PB010 — Redocly CLI](../playbook/PB010-redocly-cli-openapi.md)

---

## Referências

- [SPEC006 — Estrutura de Specs](./SPEC006-Estrutura-de-Specs.md)
- [ADR014 — Evoluir Sky-RPC para arquitetura RPC-first semântica](../adr/ADR014-evoluir-sky-rpc.md)
- [ADR016 — OpenAPI Híbrido: Operações Estáticas, Schemas Dinâmicos](../adr/ADR016-openapi-hibrido-estatico-dinamico.md)
- [PRD009 — Sky-RPC v0.3 (RPC-first Semântico)](../prd/PRD009-Sky-RPC-v0.3-RPC-first-Semantico.md)
- [PRD010 — OpenAPI Híbrido](../prd/PRD010-OpenAPI-Hibrido.md)

---

> "Evoluir sem quebrar é a arte da engenharia." – made by Sky 🧩
