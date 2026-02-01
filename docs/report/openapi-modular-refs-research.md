# Relatório: OpenAPI `$refs` Modulares por Arquivo

**Data:** 2025-12-27
**Contexto:** Pesquisa sobre organização modular de especificações OpenAPI usando `$refs` externos
**Relacionado:** Sky-RPC v0.2, skybridge architecture

---

## Resumo Executivo

**Pergunta:** O OpenAPI implementa bem `$refs` por arquivo para organização modular?

**Resposta:** **Sim**, com ressalvas importantes. O suporte existe na especificação, mas a qualidade de implementação varia muito entre ferramentas. Para skybridge (atualmente ~160 linhas), **manter monolítico é mais vantajoso**, mas estruturar para crescimento futuro é recomendado.

---

## 1. Como Funciona (`$ref` Syntax)

### 1.1 Tipos de Referência

```yaml
# Ref interna (mesmo arquivo)
$ref: '#/components/schemas/User'

# Ref externa relativa (arquivo local)
$ref: './schemas/user.yaml#/components/schemas/User'

# Ref externa absoluta (URL externa)
$ref: 'https://example.com/schemas/common.yaml#/components/schemas/Error'

# Ref para path item
$ref: './paths/users.yaml#/paths/~1users'  # ~1 = escape de /
```

### 1.2 JSON Pointer Syntax

O sufixo `#/components/...` é um **JSON Pointer** que navega dentro do arquivo referenciado:

| Sintaxe | Significado |
|---------|-------------|
| `#/components/schemas/User` | Componente `User` em `schemas` |
| `#/paths/~1users` | Path `/users` (tilde-bar = escape) |
| `#/components/responses/Error` | Componente `Error` em `responses` |

---

## 2. Estrutura de Diretório Recomendada

### 2.1 Estrutura Modular Típica

```
openapi/
├── openapi.yaml              # Root (paths apenas, com $refs)
├── paths/                    # Endpoints por contexto
│   ├── users.yaml
│   ├── orders.yaml
│   └── products.yaml
├── schemas/                  # Modelos de dados
│   ├── user.yaml
│   ├── order.yaml
│   └── product.yaml
├── parameters/               # Parâmetros reutilizáveis
│   ├── common.yaml
│   └── pagination.yaml
└── responses/                # Responses padrão
    ├── error.yaml
    └── success.yaml
```

### 2.2 Exemplo: openapi.yaml (Root)

```yaml
openapi: 3.1.0
info:
  title: Skybridge API
  version: 0.2.2

paths:
  /ticket:
    $ref: './paths/ticket.yaml#/paths/~1ticket'

  /envelope:
    $ref: './paths/envelope.yaml#/paths/~1envelope'

components:
  securitySchemes:
    BearerAuth:
      $ref: './common/security.yaml#/components/securitySchemes/BearerAuth'

  schemas:
    TicketResponse:
      $ref: './schemas/ticket.yaml#/components/schemas/TicketResponse'

    EnvelopeRequest:
      $ref: './schemas/envelope.yaml#/components/schemas/EnvelopeRequest'
```

---

## 3. Suporte de Ferramentas

### 3.1 Comparativo de Ferramentas

| Ferramenta | Suporte `$ref` Externo | Bundling | Status em 2025 | Recomendação |
|------------|------------------------|----------|-----------------|--------------|
| **Redocly CLI** | ✅ Excelente | ✅ `redocly bundle` | ✅ Ativo | **Melhor escolha** |
| **swagger-cli** | ⚠️ Limitado | ✅ `swagger-cli bundle` | ⚠️ Legado | Evitar |
| **Stoplight Elements** | ✅ Bom | ✅ Via CLI | ✅ Ativo | Boa alternativa |
| **ReDoc** | ⚠️ Requer bundle | ❌ Não | ✅ Ativo | Renderer apenas |
| **Swagger UI** | ⚠️ Requer bundle | ❌ Não | ✅ Ativo | Renderer apenas |
| **OpenAPI Generator** | ⚠️ Instável | ❌ Não | ✅ Ativo | Cuidado com refs |

### 3.2 Comandos de Bundle

```bash
# Redocly CLI (recomendado)
redocly bundle openapi.yaml -o openapi-bundled.yaml --remove-unused

# Swagger CLI (legado)
swagger-cli bundle openapi.yaml -o openapi-bundled.yaml
```

---

## 4. Limitações Conhecidas

### 4.1 Referências Circulares ⚠️

**Problema:** Muitas ferramentas não resolvem corretamente refs circulares.

```yaml
# CIRCULAR (evitar ou testar bem)
# A → B → A
components:
  schemas:
    A:
      type: object
      properties:
        b:
          $ref: '#/components/schemas/B'
    B:
      type: object
      properties:
        a:
          $ref: '#/components/schemas/A'
```

**Quando quebra:**
- Quando `required: true` está em um schema que participa de um loop
- Ferramentas de geração de código/SDK
- Validadores menos robustos
- Leitores de OpenAPI que não implementam full-spec

**Workarounds:**
- Usar `oneOf` em vez de ref direta circular
- Testar com ferramenta específica antes de adotar
- Manter specs acíclicas quando possível

### 4.2 Validação de Sub-arquivos ⚠️

**Requisito:** Cada sub-arquivo deve ser um documento OpenAPI válido.

```yaml
# ❌ ERRADO - schemas/user.yaml
User:
  type: object
  properties:
    name: string

# ✅ CORRETO - schemas/user.yaml
openapi: 3.1.0
info:
  title: User Schemas
  version: 1.0.0
components:
  schemas:
    User:
      type: object
      properties:
        name:
          type: string
```

### 4.3 Path Items e Merge de Campos

**Problema:** Quando Path Item Object fields aparecem tanto no arquivo principal quanto no referenciado.

```yaml
# Potencialmente problemático
paths:
  /users:
    summary: "Users endpoint"           # Campo no principal
    $ref: './paths/users.yaml'          # Ref que também pode ter summary
```

**Recomendação:** Manter todos os campos do Path Item no arquivo referenciado.

---

## 5. Boas Práticas

### 5.1 Quando Usar `$ref` Externo

| Situação | Recomendação | Justificativa |
|----------|--------------|---------------|
| API pequena (<100 endpoints) | ❌ Evitar | Overhead desnecessário |
| API média (100-300 endpoints) | ⚠️ Considerar | Depende da taxa de mudança |
| API grande (>300 endpoints) | ✅ Recomendado | Manutenibilidade crítica |
| Múltiplas versões simultâneas | ✅ Recomendado | Reuso de schemas |
| Múltiplos times contribuindo | ✅ Recomendado | Menos conflitos de merge |
| Bounded contexts distintos | ✅ Recomendado | Separação natural |

### 5.2 Padrões de Nomenclatura

```
./<tipo>/<entidade>.yaml#/components/<tipo>/<Entidade>

Exemplos:
./schemas/user.yaml#/components/schemas/User
./paths/ticket.yaml#/paths/~1ticket
./parameters/pagination.yaml#/components/parameters/Page
./responses/error.yaml#/components/responses/Error
```

### 5.3 Evoluir de Monolítico para Modular

**Fase 1: Internal Structure** (atual)
```yaml
# Monolítico mas bem organizado
openapi:
  components:
    schemas:
      # === Schemas do FileOps ===
      TicketResponse: {...}
      EnvelopeRequest: {...}

      # === Schemas compartilhados ===
      ErrorObject: {...}
```

**Fase 2: Externalizar Schemas** (~300 linhas)
```yaml
openapi:
  components:
    schemas:
      TicketResponse:
        $ref: './schemas/ticket.yaml#/components/schemas/TicketResponse'
      EnvelopeRequest:
        $ref: './schemas/envelope.yaml#/components/schemas/EnvelopeRequest'
```

**Fase 3: Externalizar Paths** (~500 linhas)
```yaml
paths:
  /ticket:
    $ref: './paths/ticket.yaml#/paths/~1ticket'
  /envelope:
    $ref: './paths/envelope.yaml#/paths/~1envelope'
```

**Fase 4: Organizar por Context** (bounded contexts)
```
paths/
  fileops/
    ticket.yaml
    envelope.yaml
  tasks/
    create.yaml
    update.yaml
```

---

## 6. Veredito para Skybridge

### 6.1 Estado Atual

```yaml
# openapi/v1/skybridge.yaml
- Versão: 0.2.2
- Linhas: ~160
- Estrutura: Monolítico
- Organização: Boa (seções claras)
```

### 6.2 Análise

| Aspecto | Avaliação | Ação |
|---------|-----------|------|
| Tamanho atual | **Pequeno** | ✅ Manter monolítico |
| Taxa de crescimento | **Moderada** | ⚠️ Monitorar |
| Complexidade | **Baixa** | ✅ Monolítico OK |
| Bounded contexts | **2 (fileops, tasks)** | ⚠️ Preparar para split |
| Ferramenta escolhida | N/A | 🔄 Escolher Redocly CLI |

### 6.3 Recomendações

**Curto prazo (0-3 meses):**
1. ✅ Manter `openapi/v1/skybridge.yaml` monolítico
2. ✅ Adicionar comentários delimitando contexts (FileOps, Tasks)
3. 🔄 Instalar `redocly-cli` para validação

**Médio prazo (3-6 meses):**
- Considerar split de schemas quando atingir ~300 linhas
- Migrar para estrutura modular se bounded contexts aumentarem

**Longo prazo (6-12 meses):**
- Estrutura completa modular se skybridge crescer significativamente
- CI/CD com `redocly lint` e `redocly bundle`

### 6.4 Ações Imediatas

```bash
# 1. Instalar Redocly CLI
npm install -g @redocly/cli

# 2. Adicionar script de validação
# package.json
{
  "scripts": {
    "openapi:lint": "redocly lint openapi/v1/skybridge.yaml",
    "openapi:bundle": "redocly bundle openapi/v1/skybridge.yaml -o openapi/v1/skybridge-bundled.yaml"
  }
}

# 3. Validar spec atual
npm run openapi:lint
```

---

## 7. Referências

### 7.1 Especificações Oficiais

| Fonte | URL |
|-------|-----|
| OpenAPI Specification v3.2.0 (Latest) | https://spec.openapis.org/oas/v3.2.0.html |
| OpenAPI Specification v3.1.0 | https://swagger.io/specification/ |

### 7.2 Guias e Best Practices

| Fonte | URL |
|-------|-----|
| Speakeasy - References ($ref) Best Practices | https://www.speakeasy.com/openapi/references |
| Gravitee - OpenAPI Structure Best Practices | https://www.gravitee.io/blog/openapi-specification-structure-best-practices |
| Learn OpenAPI - Best Practices | https://learn.openapis.org/best-practices.html |
| APIIMatic - 14 Best Practices for OpenAPI | https://www.apimatic.io/blog/2022/11/14-best-practices-to-write-openapi-for-better-api-consumption |

### 7.3 Tutoriais de Split

| Fonte | URL |
|-------|-----|
| Medium - Split OpenAPI into Multiple Files | https://medium.com/@gant0in/how-to-split-your-openapi-specification-file-into-multiple-files-33147cdd64e6 |
| Blog - How to split a large OpenAPI document | https://blog.techdocs.studio/p/how-to-split-a-large-openapi-document |
| Medium - Including external OpenAPI models | https://medium.com/xmglobal/including-external-openapi-models-in-your-openapi-definition-6c4c6507fe84 |

### 7.4 Ferramentas

| Fonte | URL |
|-------|-----|
| Redocly CLI - Migration from swagger-cli | https://redocly.com/docs/cli/guides/migrate-from-swagger-cli |
| OpenAPI Tools Directory | https://tools.openapis.org/categories/all.html |
| OpenAPI Tools (comprehensive list) | https://openapi.tools/ |

### 7.5 Limitações e Issues

| Fonte | URL |
|-------|-----|
| pb33f.io - Circular References in OpenAPI | https://pb33f.io/libopenapi/circular-references/ |
| GitHub Issue - Circular reference not resolved | https://github.com/readmeio/rdme/issues/1052 |
| ReadMe - Compatibility Chart | https://docs.readme.com/main/docs/openapi-compatibility-chart |
| OpenAI Community - Circular Schema Reference | https://community.openai.com/t/openapi-circular-schema-reference-function-calling/1086002 |

### 7.6 Discussões Técnicas

| Fonte | URL |
|-------|-----|
| Stack Overflow - Referencing path from external file | https://stackoverflow.com/questions/78863760/openapi-referencing-a-path-from-external-file |
| Stack Overflow - Split paths into multiple files | https://stackoverflow.com/questions/61340890/split-openapi-paths-into-multiple-path-definition-files |
| GitHub Issue - Multi-file OpenAPI definitions | https://github.com/42Crunch/vscode-openapi/issues/82 |
| Blog - Working with OpenAPI contract in multiple files | https://blog.pchudzik.com/202004/open-api-and-external-ref/ |

---

## 8. Conclusão

O suporte a `$refs` externos no OpenAPI é **maduro e bem definido** na especificação, mas a qualidade de implementação varia entre ferramentas. Para skybridge:

- **Manter monolítico** é a decisão correta para o momento atual
- **Estruturar internamente** com seções claras prepara o terreno para split futuro
- **Adotar Redocly CLI** para validação e futura modularização
- **Monitorar crescimento** e revisar decisão ao atingir ~300 linhas

---

> "Arquitetura é a arte de adiar decisões, mas estruturar para o crescimento." – made by Sky 🏗️

**Documentos relacionados:**
- [SPEC002-Sky-RPC-v0.2.md](../spec/SPEC002-Sky-RPC-v0.2.md)
- [PRD008-Sky-RPC-v0.2-envelope-estruturado.md](../prd/PRD008-Sky-RPC-v0.2-envelope-estruturado.md)
- [ADR010-adotar-sky-rpc.md](../adr/ADR010-adotar-sky-rpc.md)
