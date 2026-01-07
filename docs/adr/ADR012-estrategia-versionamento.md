---
status: aceito
data: 2025-12-27
implementado: 2026-01-06
---

# ADR-012 — Estratégia de Versionamento

## Contexto

O projeto Skybridge possui múltiplas fontes de versionamento que evoluem de forma independente:

| Componente | Localização | Versão Atual | Descrição |
|------------|-------------|--------------|-----------|
| **App Skybridge** | `src/skybridge/__init__.py` | 0.1.0 | Versão da aplicação |
| **Kernel API** | `src/skybridge/__init__.py` | 1.0.0 | Contrato do SDK interno |
| **OpenAPI Contract** | `openapi/v1/skybridge.yaml` | 0.2.0 | Contrato HTTP exposto |
| **Documentação** | `docs/` | - | PRDs, SPECS, ADRs, Playbooks |

Sem uma estratégia unificada, temos:
- Versões duplicadas em múltiplos arquivos
- Dificuldade de rastrear mudanças que afetam múltiplos componentes
- Changelogs manuais propensos a erros
- Falha de comunicação sobre breaking changes

## Decisão

Adotar **Semver** + **Conventional Commits** + **GitHub Workflows** para automatizar o versionamento e geração de documentação.

### 1. Semver para Versionamento

```
MAJOR.MINOR.PATCH

MAJOR: mudanças incompatíveis na API pública
MINOR: funcionalidades backward-compatible
PATCH: bug fixes backward-compatible
```

**Regras por componente:**

| Componente | Escopo de MAJOR | Exemplos |
|------------|-----------------|----------|
| **App** | Contrato `/ticket`, `/envelope` | Remover endpoint, mudar schema de resposta |
| **Kernel API** | Assinaturas públicas do SDK | Remover função, mudar tipo de parâmetro |
| **OpenAPI** | Schema exposto via `/openapi` | Remover propriedade, mudar tipo de campo |

**Independência de versões:**
- Cada componente tem seu próprio número de versão
- Mudanças em um componente não forçam bump em outros
- Ex: App 1.2.0 pode usar OpenAPI 1.0.0

### 2. Conventional Commits

```
<tipo>[escopo opcional]: <descrição>

[opcional corpo]

[opcional footer]
```

**Tipos suportados:**

| Tipo | Bump | Exemplo |
|------|------|---------|
| `feat` | MINOR | `feat(auth): adicionar lógica de retry para auth falhadas` |
| `fix` | PATCH | `fix(auth): corrigir caso de borda na expiração de token` |
| `BREAKING CHANGE` | MAJOR | `feat(protocol)!: mudar schema do envelope` |
| `docs` | - | `docs: atualizar ADR012 com exemplos de versionamento` |
| `chore` | - | `chore: atualizar dependências do pyproject.toml` |
| `test` | - | `test(auth): adicionar testes de validação de expiração` |
| `refactor` | - | `refactor(kernel): simplificar registro de queries` |

**Escopos definidos:**

- `app`: aplicação Skybridge
- `kernel`: SDK interno
- `openapi`: contrato YAML
- `auth`: autenticação/autorização
- `fileops`: contexto de operações de arquivo
- `tasks`: contexto de tarefas

**Exemplos válidos:**

```
feat(auth): implementar refresh token

- Adicionar endpoint /auth/refresh
- Implementar rotação de tokens
- Adicionar validação de expiração

BREAKING CHANGE: remover endpoint legado

fix(auth): resolver race condition em requisições concorrentes

docs(adr): criar ADR012 para estratégia de versionamento

refactor(openapi): simplificar definições de schema
```

### 3. Single Source of Truth

**Versão centralizada em `VERSION`:**

```
skybridge/
├── VERSION              # única fonte de verdade
├── src/skybridge/__init__.py    # lê VERSION
├── openapi/v1/skybridge.yaml    # lê VERSION via script
└── .github/workflows/           # usa VERSION para tags
```

**Formato do arquivo VERSION:**

```
SKYBRIDGE_VERSION=0.1.0
KERNEL_API_VERSION=0.1.0
OPENAPI_CONTRACT_VERSION=0.1.0
```

### 3.1. Decisão de Versões Iniciais (2026-01-06)

**Decisão:** Rebaixar todos os componentes para **0.1.0**

**Justificativa:**
- ✅ **Fresh start** — Antes não havia versionamento oficial rastreando
- ✅ **Sincronia total** — Todos os componentes começam alinhados
- ✅ **Sem confusão** — Evita discrepâncias entre versões anteriores não oficiais

**Mudanças aplicadas:**
- Core: 0.1.0 → 0.1.0 (mantém)
- Kernel API: 1.0.0 → 0.1.0 (rebaixa)
- CLI: 0.3.0 → 0.1.0 (rebaixa)
- OpenAPI: 0.2.2 → 0.1.0 (rebaixa)

**Relatório completo:** `docs/inventory/PRD012-version-inventory.md`

### 4. GitHub Workflows

**Workflow `.github/workflows/release.yml`:**

```yaml
name: Release

on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Parse commits with conventional commits
        # Determina tipo de bump (MAJOR/MINOR/PATCH)

      - name: Update VERSION files
        # Atualiza versões baseado no escopo do commit

      - name: Generate changelog
        # Gera CHANGELOG.md do histórico de commits

      - name: Create Git tag
        # Cria tag v{version} e push

      - name: Create GitHub Release
        # Cria release com changelog
```

**Workflow `.github/workflows/docs.yml`:**

```yaml
name: Docs

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'VERSION'

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - name: Generate OpenAPI with version
        # Injeta versão do VERSION no YAML

      - name: Update SPEC versions
        # Atualiza referências de versão nos specs

      - name: Build documentation site
        # Gera site estático da documentação

      - name: Deploy to GitHub Pages
        # Publica em skybridge.dev/docs
```

### 5. Matriz de Impacto de Mudanças

| Mudança em... | Afeta... | Bump necessário? |
|---------------|----------|-----------------|
| `App` | App VERSION | Sim |
| `Kernel API` | Kernel VERSION | Sim |
| `OpenAPI` | Contract VERSION + YAML | Sim |
| `feat` no App | App VERSION (MINOR) | Sim |
| `fix` no App | App VERSION (PATCH) | Sim |
| `docs` | - | Não |
| `chore` | - | Não |

**Regra geral:** apenas commits `feat`, `fix` e `BREAKING CHANGE` geram bumps.

### 6. Geração de Documentação

**CHANGELOG.md gerado automaticamente:**

```markdown
# Changelog

## [0.2.0] - 2025-12-27

### Adicionado
- feat(auth): implementar refresh token ([abc123])
- feat(auth): adicionar rotação de tokens ([def456])

### Alterado
- BREAKING CHANGE: remover endpoint legado ([ghi789])

### Corrigido
- fix(auth): resolver race condition em requisições concorrentes ([jkl012])
```

**Docs indexadas por versão:**

```
https://skybridge.dev/docs/v0.2/spec/protocol
https://skybridge.dev/docs/v0.1/spec/protocol
```

## Consequências

### Positivas

* **Single source of truth:** versões centralizadas, sem duplicação
* **Changelog automático:** histórico gerado dos commits
* **Release automatizado:** zero manual na criação de versões
* **Rastreabilidade clara:** cada mudança linkada ao commit
* **Documentação versionada:** specs indexados por versão
* **Semver padronizado:** comunicação clara de breaking changes

### Negativas / Riscos

* Requer disciplina nos commits (conventional commits obrigatórios)
* Primeira configuração dos workflows demanda esforço
* Migração de versões manuais para automatizadas

## Status de Implementação

### ✅ Concluído (2026-01-06)
- [x] Inventário de versões completo (`docs/inventory/PRD012-version-inventory.md`)
- [x] Decisão de versões iniciais (todos em 0.1.0)
- [x] Criação do arquivo VERSION
- [x] Atualização de todos os componentes para 0.1.0

### 🔄 Pendente
- [ ] Criar workflow `.github/workflows/release.yml`
- [ ] Criar workflow `.github/workflows/docs.yml`
- [ ] Configurar commitlint para enforce conventional commits
- [ ] Implementar geração automática de CHANGELOG.md

## Dependências

- **ADR011** (Snapshot/Diff): Snapshots são vinculados a versões via Git hooks

## Referências

- [ADR011 - Snapshot/Diff para Visão do Estado Atual](B:\_repositorios\skybridge\docs\adr\ADR011-snapshot-diff-estado-atual.md)
- [Conventional Commits v1.0.0](https://www.conventionalcommits.org/)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [A successful Git branching model](https://nvie.com/posts/a-successful-git-branching-model/)

---

> "Versionamento sem caos é a base de confiança em evolução." – made by Sky ✨
