# Fix: OpenAPI `patternProperties` e Custom GPT Actions

**Data:** 2025-12-27

**Status:** ✅ Resolvido

**Impacto:** Crítico - bloqueava uso de Custom GPT Actions

**Tempo de resolução:** ~24h+

---

## Problema

Custom GPT Actions não conseguiam enviar parâmetros posicionais (`detalhe_0`, `detalhe_1`, etc.) via envelope. O JIT (mecanismo interno do ChatGPT) rejeitava com:

```
UnrecognizedKwargsError: detalhe_0
```

### Sintomas

- Endpoint `/ticket` funcionava (retornava ticket ID)
- Endpoint `/envelope` recebia request mas o JIT rejeitava antes de chegar à API
- Mesmo mudando nomes de parâmetros, o problema persistia
- API logs mostravam que o envelope nem chegava a ser processado

---

## Causa Raiz

### Schema OpenAPI Incorreto

O arquivo `openapi/v1/skybridge.yaml` continha:

```yaml
EnvelopeRequest:
  type: object
  properties:
    ticket_id:
      type: string
    detalhe:
      description: Detalhe único da operação (quando aplicável).
  patternProperties:
    '^detalhe(_\\d+)?$':
      description: Detalhes posicionais (detalhe, detalhe_1, detalhe_2, etc.).
  additionalProperties: false  # ← BLOQUEIA TUDO QUE NAO ESTA EM "properties"
  required:
    - ticket_id
```

### Problemas

1. **`patternProperties` NAO EXISTE em OpenAPI 3.1.0**
   - Esta sintaxe é do **JSON Schema**, não do OpenAPI
   - O parser OpenAPI ignora silenciosamente
   - O JIT do ChatGPT também ignora

2. **`additionalProperties: false` é estrito demais**
   - Bloqueia qualquer propriedade não listada explicitamente em `properties`
   - Só permite `ticket_id` e `detalhe`
   - `detalhe_0`, `detalhe_1`, etc. são rejeitados

3. **YAML com pontos sem aspas**
   - Descrições com `ex.: fileops.read` causavam parse error
   - O YAML parser interpretava `:` como separador key-value

---

## Solução

### 1. Remover `patternProperties` (syntax inválida)

```yaml
# ANTES (INCORRETO)
patternProperties:
  '^detalhe(_\\d+)?$':
    description: Detalhes posicionais (detalhe, detalhe_1, detalhe_2, etc.).

# DEPOIS (REMOVIDO)
# Removido completamente - não é suportado pelo OpenAPI
```

### 2. Adicionar `type` ao `detalhe`

```yaml
# ANTES
detalhe:
  description: Detalhe único da operação (quando aplicável).

# DEPOIS
detalhe:
  type: string
  description: Detalhe único da operação (quando aplicável).
```

### 3. Mudar `additionalProperties` para `true`

```yaml
# ANTES
additionalProperties: false  # ← Bloqueia parâmetros não declarados

# DEPOIS
additionalProperties: true   # ← Permite parâmetros dinâmicos
```

### 4. Corrigir YAML com aspas

```yaml
# ANTES (QUEBRA YAML)
description: Nome da operação Sky-RPC (ex.: fileops.read). Não é verbo HTTP.

# DEPOIS (VÁLIDO)
description: "Nome da operação Sky-RPC (ex.: fileops.read). Não é verbo HTTP."
```

---

## Schema Final Corrigido

```yaml
EnvelopeRequest:
  type: object
  properties:
    ticket_id:
      type: string
    detalhe:
      type: string
      description: Detalhe único da operação (quando aplicável).
  additionalProperties: true  # ← Permite detalhe_0, detalhe_1, etc.
  required:
    - ticket_id
```

---

## Por que `additionalProperties: true` é a solução correta?

1. **OpenAPI 3.1 não suporta regex em propriedades**
   - Não existe `patternProperties` ou equivalentes
   - A única forma de permitir propriedades dinâmicas é `additionalProperties: true`

2. **Sky-RPC é introspectivo**
   - O servidor valida parâmetros em runtime
   - O schema OpenAPI não precisa ser estrito sobre propriedades
   - O protocolo envelope + ticket já fornece segurança

3. **Compatibilidade com Custom GPT Actions**
   - O JIT valida contra o schema OpenAPI
   - Com `additionalProperties: true`, ele aceita qualquer propriedade
   - A validação real acontece no servidor (não no JIT)

---

## Lições Aprendidas

1. **OpenAPI ≠ JSON Schema**
   - OpenAPI 3.1 usa JSON Schema para *subschemas*, mas não para todos os recursos
   - `patternProperties` não existe no contexto OpenAPI

2. **Custom GPT Actions usam JIT strict**
   - O JIT valida estritamente contra o schema OpenAPI
   - `additionalProperties: false` bloqueia TUDO que não está declarado

3. **Sempre validar YAML**
   - Descrições com `:` precisam de aspas
   - Usar `python -c "import yaml; yaml.safe_load(...)"` para validar

4. **Cache do Custom GPT**
   - Após mudar o schema, é preciso reconfigurar a Action
   - O JIT pode ter cache do schema antigo

---

## Validação

```bash
# Validar YAML
python -c "import yaml; yaml.safe_load(open(r'openapi\v1\skybridge.yaml'))"

# Testar schema
curl https://cunning-dear-primate.ngrok-free.app/openapi
```

---

## Referências

- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [JSON Schema - patternProperties](https://json-schema.org/understanding-json-schema/reference/object.html#pattern-properties)
- PRD007 - Sky-RPC Ticket Envelope

---

> "A solução mais simples é muitas vezes a mais difícil de encontrar, especialmente quando a sintaxe parece correta mas não é." – made by Sky 🔧
