---
status: proposto
data: 2026-02-07
implementado: pendente
---

# ADR-025 — Estratégia de CHANGELOG e Release Notes

## Contexto

O projeto Skybridge adota o **PL001** (git tags como fonte de verdade para versionamento) e possui um **CHANGELOG.md** que é:

1. **Gerado automaticamente** pelo workflow `release.yml` via `runtime/changelog.py`
2. **Versionado no Git** (commitado pelo bot a cada release)
3. **Editado manualmente** com seções `[Unreleased]` que não correspondem a versões numeradas

Esta abordagem híbrida cria contradições:

```markdown
## [Unreleased] - 2026-02-04  ← Entrada manual, sem versão
### 📝 Documentação
* PRD026 criado...

## [Unreleased] - 2026-02-03  ← Entrada manual, sem versão
### ✨ Novidades
* Tasks 5 e 6 do PRD024...

## [0.13.0] - 2026-02-01  ← Gerado automaticamente
### ✨ Novidades
* feat: implementar visualização Kanban...
```

**Problemas identificados:**

| Problema | Impacto |
|----------|---------|
| CHANGELOG gerado + versionado | Conflitos ao fazer merge dev → main |
| Entradas `[Unreleased]` | Mistura manual + automático, conceitualmente confuso |
| Fonte da verdade? | Git log tem a mesma info que CHANGELOG |
| Dev não tem releases | Mudanças em dev só viram release quando mergeiam |

Além disso, atualmente **só a branch `main` recebe releases**, o que significa:

- Mudanças em `dev` só são "lançadas" quando mergeadas para `main`
- Não é possível testar uma versão em `dev` antes de ir para produção
- O ciclo de release é rígido: dev → main → release

---

## Decisão

**Adotar estratégia híbrida com duas camadas de documentação de releases:**

1. **CHANGELOG.md** - Histórico oficial de releases (gerado automaticamente)
2. **docs/release-notes/** - Notas de release planejadas (edição manual)

E **permitir releases em branches** (dev, main, ou qualquer branch com proteção).

---

## Análise de Opções

### Opção 1: Manter como está (Status Quo)

**Descrição:** CHANGELOG.md gerado automaticamente + versionado, com `[Unreleased]` manuais.

```yaml
# Como está:
CHANGELOG.md:
  ## [Unreleased] - 2026-02-04  ← Manual
  ## [Unreleased] - 2026-02-03  ← Manual
  ## [0.13.0] - 2026-02-01       ← Auto gerado
```

**Vantagens:**
- ✅ Já funciona
- ✅ Workflow automatizado

**Desvantagens:**
- ❌ Conceitualmente confuso (manual + automático misturados)
- ❌ Conflitos no merge dev → main
- ❌ `[Unreleased]` em arquivo de histórico é contraditório
- ❌ Fonte de verdade ambígua (git log vs CHANGELOG)

---

### Opção 2: Modelo auto-claude (CHANGELOG Manual + Workflow Valida)

**Descrição:** CHANGELOG.md é editado manualmente antes do release, workflow valida que existe.

```yaml
# Fluxo auto-claude:
1. Desenvolvedor roda: npm version bump (ou script similar)
2. Desenvolvedor edita CHANGELOG.md manualmente
3. Cria PR develop → main
4. Workflow valida: CHANGELOG tem entrada para versão?
5. Se SIM: cria tag, builda, release
6. Se NÃO: falha com erro
```

**Vantagens:**
- ✅ CHANGELOG tem valor humano (resumos, contexto, não só lista de commits)
- ✅ Workflow garante que changelog existe
- ✅ Sem conflitos (CHANGELOG editado antes do merge)

**Desvantagens:**
- ❌ Requer passo manual obrigatório
- ❌ Pode esquecer de editar CHANGELOG
- ❌ Changelog pode ficar desincronizado do git log
- ❌ Mais trabalho para o desenvolvedor

**Fonte:** [auto-claude/RELEASE.md](https://github.com/AndyMik90/Auto-Claude/blob/main/RELEASE.md)

---

### Opção 3: CHANGELOG Apenas Releases + Release Notes por Versão

**Descrição:** CHANGELOG.md só contém versões lançadas. Notas manuais vão para arquivos separados.

```yaml
# Estrutura:
CHANGELOG.md:              # Apenas releases concretizados
  ## [0.13.0] - 2026-02-01
  ## [0.12.0] - 2026-01-26

docs/release-notes/:
  unreleased.md             # Coisas sem data definida
  0.14.0-rc1.md            # Planejamento da release candidata
  0.14.0.md                # Planejamento da release final
```

**Vantagens:**
- ✅ Separação clara: histórico (CHANGELOG) vs planejamento (release-notes)
- ✅ CHANGELOG conceitualmente correto (só versões lançadas)
- ✅ Sem `[Unreleased]` no CHANGELOG
- ✅ Release notes podem ser colaborativos

**Desvantagens:**
- ❌ Mais arquivos para gerenciar
- ❌ Precisa mover/copy conteúdo de release-notes para CHANGELOG
- ❌ Complexidade adicional

---

### Opção 4: Releases em Branches (dev também recebe releases)

**Descrição:** Permitir criar releases a partir de qualquer branch protegido (dev, main).

```yaml
# Fluxo proposto:
dev branch:
  1. Features implementadas
  2. Merge commit dev → dev (workflow_DISPATCH)
  3. Workflow detecta commits desde última tag
  4. Cria release dev-v0.14.0-rc.1
  5. Gera CHANGELOG (só dev)

main branch:
  1. Merge dev → main
  2. Workflow detecta commits desde última tag
  3. Cria release v0.14.0
  4. Gera CHANGELOG (oficial)
```

**Vantagens:**
- ✅ Possível testar releases em dev
- ✅ RC (release candidates) antes de produção
- ✅ Maior flexibilidade no ciclo de release
- ✅ Dev pode ter seu próprio changelog

**Desvantagens:**
- ❌ Mais complexidade no workflow
- ❌ Múltiplas tags para mesma versão (rc1, rc2, final)
- ❌ Precisa decidir qual changelog é "oficial"

---

## Decisão Final

**Adotar Opção 3 (CHANGELOG + Release Notes separados) + Variação da Opção 4 (releases em branches)**

### Estrutura de Arquivos

```
projeto/
├── CHANGELOG.md                    # Apenas releases OFICIAIS (main)
│   ## [0.13.0] - 2026-02-01
│   ## [0.12.0] - 2026-01-26
│
├── docs/
│   ├── release-notes/             # Notas planejadas
│   │   ├── unreleased.md          # Backlog de mudanças
│   │   ├── 0.14.0.md              # Planejamento próxima versão
│   │   └── dev/                   # Releases de dev
│   │       ├── 0.14.0-rc.1.md     # RC 1 em dev
│   │       └── 0.14.0-rc.2.md     # RC 2 em dev
│   │
│   └── guide/
│       └── release.md             # Guia de releases (já existe)
│
└── .github/
    └── workflows/
        ├── release.yml            # Releases OFICIAIS (main)
        └── release-dev.yml        # Releases de DEV (opcional)
```

### Regras

| Arquivo | Conteúdo | Gerado por | Editado manualmente? |
|---------|----------|------------|---------------------|
| **CHANGELOG.md** | Apenas versões oficiais (main) | `release.yml` | ❌ Não |
| **docs/release-notes/unreleased.md** | Coisas sem versão definida | - | ✅ Sim |
| **docs/release-notes/0.14.0.md** | Planejamento da versão | - | ✅ Sim |
| **docs/release-notes/dev/*.md** | RCs de dev | `release-dev.yml` | ✅ Sim |

### Fluxo de Release

#### 1. Desenvolvimento (dev)

```
dev branch:
1. Implementa features
2. Atualiza docs/release-notes/unreleased.md
3. Quando pronto, move para 0.14.0.md
```

#### 2. Release Candidate (dev)

```bash
# Opção 1: Manual
gh workflow run release-dev.yml -f version=0.14.0-rc.1

# Opção 2: Automático quando houver commit específico
git commit --allow-empty -m "chore: release 0.14.0-rc.1"
git push
```

**Resultado:**
- Tag `dev-v0.14.0-rc.1` criada
- Release `dev-v0.14.0-rc.1` no GitHub
- CHANGELOG.md NÃO é alterado

#### 3. Release Oficial (main)

```
main branch:
1. Merge dev → main
2. Workflow detecta commits desde v0.13.0
3. Calcula nova versão (0.14.0)
4. Gera CHANGELOG.md (adiciona ## [0.14.0])
5. Cria tag v0.14.0
6. Cria Release oficial no GitHub
```

---

## Implicações

### Positivas

| Aspecto | Benefício |
|---------|-----------|
| ** Clareza conceitual** | CHANGELOG = histórico, release-notes = planejamento |
| ** Sem conflitos** | CHANGELOG só é alterado em main, não há merge |
| ** Flexibilidade** | Dev pode ter RCs, testes, experimentos |
| ** Colaboração** | release-notes podem ser editados por múltiplas pessoas |
| ** Histórico preservado** | CHANGELOG só cresce, versões são imutáveis |

### Negativas

| Aspecto | Custo |
|---------|-------|
| ** Complexidade** | Mais arquivos para gerenciar |
| ** Workflow adicional** | Precisa criar/mover conteúdo entre arquivos |
| ** Aprendizado** | Time precisa entender nova estrutura |

### Migração

```bash
# Passo 1: Mover [Unreleased] para release-notes
mkdir -p docs/release-notes
# Mover conteúdo dos [Unreleased] para docs/release-notes/unreleased.md

# Passo 2: Limpar CHANGELOG.md
# Remover todas seções [Unreleased], deixar só versões numeradas

# Passo 3: Criar template de 0.14.0.md
touch docs/release-notes/0.14.0.md

# Passo 4: Atualizar workflow
# Modificar release.yml para NÃO adicionar [Unreleased]
```

---

## Alternativas Consideradas

1. **CHANGELOG não versionado (gerado apenas)**
   - Rejeitado porque: usuários offline não conseguem ver histórico

2. **CHANGELOG puramente manual**
   - Rejeitado porque: fácil esquecer, trabaloso, propenso a erros

3. **Usar GitHub Releases como único changelog**
   - Rejeitado porque: não funciona offline, API do GitHub necessária

---

## Referências

### Projetos Referência

- **[auto-claude](https://github.com/AndyMik90/Auto-Claude)** - CHANGELOG manual + workflow valida
- **[Keep a Changelog](https://keepachangelog.com/)** - Formato padrão de changelog
- **[Common Changelog](https://github.com/vweevers/common-changelog)** - Style guide para changelogs

### Artigos

- **[11 Best Practices for Changelogs](https://www.getbeamber.com/blog/11-best-practices-for-changelogs)** (Jan 2024)
- **[Five changelog principles from best-in-class developer brands](https://www.mintlify.com/blog/five-changelog-principles-from-best-developer-brands)** (Dec 2024)

### Documentação Interna

- **PL001** - Migrar Versionamento para Git Tags
- **ADR012** - Estratégia de Versionamento
- **docs/guide/release.md** - Guia de Release Automatizado

---

## Status

**Proposto** - Aguardando aprovação

---

> "A verdadeira fonte da verdade é o git log. O resto é documentação." – made by Sky 🚀
