# ADR 012: Adotar yamllint + openapi-validator

**Data:** 2025-12-27
**Status:** ✅ Aceito
**Contexto:** PRD007 - Sky-RPC Ticket Envelope

---

## Contexto

Durante troubleshooting de 24h+ (ver `docs/report/openapi-patternproperties-fix.md`), descobrimos que:
- Sintaxe inválida de OpenAPI (`patternProperties`) passou despercebida
- Erro de YAML (dois pontos sem aspas) quebrou o parser
- Validação manual não é suficiente para prevenir esses erros

O problema custou horas de debug porque o erro só aparecia em runtime, no JIT do ChatGPT.

---

## Decisão

Adotar **yamllint** + **openapi-validator** como ferramentas de validação obrigatórias para:
- Todo arquivo YAML no projeto
- Todo schema OpenAPI (skybridge.yaml)

### Ferramentas Escolhidas

| Ferramenta | Uso | Por quê? |
|------------|-----|----------|
| **yamllint** | Sintaxe YAML | Leve, Python (mesmo stack), detecta indentação, aspas, syntax |
| **openapi-spec-validator** | Validação OpenAPI | Python (mesmo stack), valida contra spec 3.x, integra com CI |

---

## Especificação

### yamllint

**Instalação:**
```bash
pip install yamllint
```

**Config:** `.yamllint` na raiz do projeto
```yaml
extends: default
rules:
  line-length:
    max: 120
  quotes:
    required: true
  trailing-spaces:
    level: warning
```

**Uso:**
```bash
# Validar arquivo específico
yamllint openapi/v1/skybridge.yaml

# Validar todos YAML
yamllint openapi/ .github/workflows/
```

### openapi-spec-validator

**Instalação:**
```bash
pip install openapi-spec-validator
```

**Uso:**
```bash
# Validar schema OpenAPI
openapi-spec-validator openapi/v1/skybridge.yaml
```

**Resultado:**
```
openapi/v1/skybridge.yaml: OK
```

---

## Integração com CI/CD

Adicionar ao workflow de testes:

```yaml
- name: Validate YAML
  run: yamllint openapi/ .github/workflows/

- name: Validate OpenAPI
  run: openapi-validator openapi/v1/skybridge.yaml
```

---

## Exemplos de Erros Detectados

### yamllint
```yaml
# ERRO: dois pontos sem aspas
description: Nome da operação Sky-RPC (ex.: fileops.read). Não é verbo HTTP.
#                                  ↑
#                             yamllint detecta
```

### openapi-validator
```yaml
# ERRO: patternProperties não existe em OpenAPI 3.1
patternProperties:
  '^detalhe(_\\d+)?$':
    description: Detalhes posicionais
# ↑
# openapi-validator detecta
```

---

## Alternativas Consideradas

| Ferramenta | Stack | Por que NAO? |
|------------|-------|--------------|
| **Spectral** | Node.js | Stack diferente (Python), mais pesado |
| **swagger-validator** | Node.js | Stack diferente, dependência npm |
| **prism** | Node.js | Servidor de mock, não validador puro |

---

## Consequências

### Positivas
- ✅ Erros de sintaxe detectados antes do commit
- ✅ Validação contra spec OpenAPI 3.1
- ✅ Previne problemas como o de 24h+ de debug
- ✅ Integra com CI/CD

### Negativas
- ⚠️ Mais uma dependência no projeto (mas leve)
- ⚠️ Arquivo de config adicional (`.yamllint`)

---

## Status de Implementação

- [x] Instalar yamllint ✅
- [x] Instalar openapi-spec-validator ✅
- [x] Criar `.yamllint` config ✅
- [x] Rodar validação inicial em `openapi/v1/skybridge.yaml` ✅
- [ ] Adicionar ao CI/CD (se houver)

---

## Emendments (Emendas)

### Emendment 1 (2025-12-28): Adoção de Redocly CLI

**Contexto:** A validação com `openapi-spec-validator` mostrou limitações:
- Não suporta `$ref` externos
- Performance lenta em specs grandes
- Pouco mantido pela comunidade

**Decisão:** Conforme **[ADR016](./ADR016-openapi-hibrido-estatico-dinamico.md)**:
- `openapi-spec-validator` é substituído por **Redocly CLI**
- `yamllint` é mantido para validação de sintaxe YAML
- Redocly CLI oferece suporte superior para `$ref` externos e bundle

**Mudanças:**
```bash
# Antigo (depreciado)
openapi-spec-validator docs/spec/openapi/openapi.yaml

# Novo (ADR016)
redocly lint docs/spec/openapi/openapi.yaml
redocly bundle docs/spec/openapi/openapi.yaml -o dist/openapi-bundled.yaml
```

**Ver também:** [PB010 — Redocly CLI para OpenAPI](../playbook/PB010-redocly-cli-openapi.md)

---

## Referências

### Resultado dos Testes (2025-12-27)

```bash
$ yamllint openapi/v1/skybridge.yaml
YAML VALIDADO

$ openapi-spec-validator openapi/v1/skybridge.yaml
openapi/v1/skybridge.yaml: OK
```

---

## Referências

- [yamllint docs](https://yamllint.readthedocs.io/)
- [openapi-validator](https://github.com/p1c2u/openapi-validator)
- ADR012 relacionado: PRD007 - Sky-RPC Ticket Envelope
- Incidente: `docs/report/openapi-patternproperties-fix.md`

---

> "Prevenir é mais barato que debugar." – made by Sky 🛡️
