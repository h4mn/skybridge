# Versionamento Profissional: Padrões, Estratégias e Recomendações

**Status:** Estudo
**Data:** 2026-01-11
**Autor:** Sky
**Contexto:** PR #6 - Bump 0.2.5 → 0.3.0

---

## 1. Contexto da Skybridge

**Situação atual:**
- Versão: `0.2.5`
- PR contém 3 funcionalidades novas (Snapshot Service, AI Agent Interface, Webhook Autonomous Agents)
- Commit manual: `chore(release): bump versão para 0.3.0`
- Workflow automatizado pode tentar bump novamente

**Decisão tomada:** Bump MINOR (0.2.5 → 0.3.0) ✅ CORRETA

---

## 2. Padrões Profissionais de Versionamento

### 2.1 Auto-Bump (Conventional Commits + CI/CD)

**Adotado por:** Angular, Angular CLI, Babel, ESLint, muitos projetos open-source

**Como funciona:**
```bash
# Developer faz commit com conventional commit
git commit -m "feat(auth): add OAuth2 support"

# CI detecta "feat" → bumps MINOR automaticamente
# Workflow cria tag, changelog, release
```

**Vantagens:**
- ✅ Zero atrito para desenvolvedores
- ✅ Versionamento consistente
- ✅ Changelog gerado automaticamente
- ✅ Releases previsíveis

**Desvantagens:**
- ❌ Dependência de padronização de commits
- ❌ Difícil corrigir versão errada
- ❌ Releases podem acontecer sem revisão humana

**Ferramentas:**
- `semantic-release` (Node.js)
- `conventional-changelog` (multi-language)
- `release-drafter` (GitHub Actions)
- `.github/workflows/release.yml` (custom, caso Skybridge)

---

### 2.2 Manual Bump (Release Manager)

**Adotado por:** Kubernetes, Docker, Redis, grandes projetos corporativos

**Como funciona:**
```bash
# Developer faz commits normais
git commit -m "Add OAuth2 support"

# Release Manager decide quando versionar
git checkout -b release-0.3.0
# Edita VERSION, CHANGELOG
git merge main
git tag v0.3.0
git push
```

**Vantagens:**
- ✅ Controle total sobre releases
- ✅ Pode agrupar features por release
- ✅ Flexibilidade para hotfixes
- ✅ Revisão humana antes de release

**Desvantagens:**
- ❌ Gatilho humano (esquecer, demorar)
- ❌ Pode criar gargalo (Release Manager ausente)
- ❌ Processo mais manual

---

### 2.3 Híbrido (Auto-Detect + Manual Approve)

**Adotado por:** Rust, .NET, muitos projetos corporativos maduros

**Como funciona:**
```bash
# CI detecta "feat" → sugere bump MINOR
# Cria PR de release: "Proposta: v0.3.0"
# Release Manager aprova PR → workflow completa
```

**Vantagens:**
- ✅ Melhor dos dois mundos
- ✅ Sugestão automática + aprovação humana
- ✅ Audit trail de decisões

**Desvantagens:**
- ❌ Mais complexo para configurar
- ❌ Requer processo de aprovação

---

## 3. Análise por Tipo de Projeto

| Tipo de Projeto | Padrão Recomendado | Justificativa |
|-----------------|---------------------|----------------|
| **Open-source pequeno** (<10 contribuidores) | Auto-Bump | Menor atrito, releases frequentes |
| **Open-source médio** (10-100 contribuidores) | Híbrido | Controle + escala |
| **Open-source grande** (100+ contribuidores) | Manual + Equipe | Release Manager, consistência |
| **Corporativo time pequeno** (<5 devs) | Auto-Bump | Velocidade |
| **Corporativo time médio** (5-20 devs) | Híbrido | Controle + velocidade |
| **Corporativo time grande** (20+ devs) | Manual + Equipe | Governança |

---

## 4. Caso Skybridge: Análise e Recomendação

### 4.1 Contexto Atual

**Características:**
- Repositório: 1 maintainers (h4mn)
- Contribuidores: 1 principal (h4mn/Sky)
- Tipo: Biblioteca + Plataforma (API + SDK)
- Estágio: Inicial (v0.2.x)
- Release cadence: Baseada em features (não time-based)

### 4.2 Problema: Versionamento por Componente

**Pergunta:** Cada componente (App, Kernel, OpenAPI) tem versão própria ou versão unificada?

| Opção | Vantagens | Desvantagens |
|-------|-----------|--------------|
| **Versão Unificada** (atual) | Simples, sync garantizado | Acoplamento de releases |
| **Versão Independente** | Desacoplado, flexível | Complexidade de gestão |
| **Versão por Contexto** | Melhor granularidade | Requer definição clara |

---

## 5. Proposta: Versionamento por Contexto (ADR019)

### 5.1 Princípios

1. **Cada Bounded Context tem sua própria versão**
2. **Integrações entre contexts usam contratos versionados**
3. **Breaking changes em um context NÃO forçam bump em outros**

### 5.2 Contexts da Skybridge

```
Skybridge
├── platform/            # Plataforma core
│   ├── observability/   # v0.3.0 (Snapshot Service)
│   ├── config/           # v0.3.0
│   └── delivery/         # v0.3.0 (FastAPI, routes)
├── core/                # Domínio core
│   ├── contexts/
│   │   ├── webhooks/     # v0.1.0 (novo contexto)
│   │   ├── fileops/      # v0.2.5
│   │   └── tasks/        # v0.2.0
└── infra/               # Infraestrutura
    └── contexts/
        └── webhooks/     # v0.1.0 (novo contexto)
```

### 5.3 Algoritmo de Bump por Contexto

**Regra 1: Contextos Novos**
```
Se o context não existe ainda → v1.0.0
```

**Regra 2: Breaking Change no Context**
```
Se breaking change no context X → bump MAJOR de X
Outros contexts mantêm versão
```

**Regra 3: Feature no Context**
```
Se feature no context X → bump MINOR de X
Outros contexts mantêm versão
```

**Regra 4: Fix no Context**
```
Se fix no context X → bump PATCH de X
Outros contexts mantêm versão
```

**Regra 5: Integração Entre Contexts**
```
Se Context A depende de Context B:
- B usa contrato versionado
- A especifica: "B >= 1.0.0, < 2.0.0"
- Breaking change em B requer revisão de A
```

---

## 6. Implementação Prática

### 6.1 Estrutura de Versionamento

```yaml
# VERSION (global - single source of truth para plataforma)
SKYBRIDGE_VERSION=0.3.0

# Contexts version (futuro)
PLATFORM_OBSERVABILITY_VERSION=0.3.0
PLATFORM_DELIVERY_VERSION=0.3.0
CORE_WEBHOOKS_VERSION=0.1.0
INFRA_WEBHOOKS_VERSION=0.1.0
```

### 6.2 Algoritmo de Bump Automático

```python
def calculate_version_bump(commits: List[Commit], context: str) -> VersionBump:
    """
    Calcula bump necessário para um context baseado nos commits.

    Args:
        commits: Lista de commits desde último release
        context: Nome do context (ex: 'webhooks', 'observability')

    Returns:
        VersionBump: MAJOR, MINOR, PATCH ou NONE
    """
    context_commits = [c for c in commits if c.context == context or c.context == 'global']

    # 1. Check for BREAKING CHANGE no context
    if any(c.has_breaking_change for c in context_commits):
        return VersionBump.MAJOR

    # 2. Check for feat no context
    if any(c.type == 'feat' for c in context_commits):
        return VersionBump.MINOR

    # 3. Check for fix no context
    if any(c.type == 'fix' for c in context_commits):
        return VersionBump.PATCH

    return VersionBump.NONE
```

### 6.3 Matriz de Impacto

| Context | Commits | Bump | Versão Anterior | Versão Nova |
|---------|---------|------|----------------|-------------|
| `webhooks` | 3 × `feat` | MINOR | - | `0.1.0` |
| `observability` | 2 × `feat` | MINOR | `0.2.5` | `0.3.0` |
| `platform` | 1 × `feat` | MINOR | `0.2.5` | `0.3.0` |
| `kernel` | 0 commits | - | `0.2.5` | `0.2.5` (sem mudança) |

---

## 7. Recomendação para Skybridge (Fase Atual)

### 7.1 Fase Inicial (v0.x) - NOW

**Estratégia:** **Versão Unificada + Auto-Bump com Revisão**

```
┌─────────────────────────────────────────────────────────────┐
│ PADRÃO ATUAL (v0.2.5 → v0.3.0) ✅ CORRETO                │
├─────────────────────────────────────────────────────────────┤
│ • Single source of truth: arquivo VERSION                  │
│ • Bump manual no PR com commit "chore(release): bump..."    │
│ • Workflow detecta, NÃO re-bumpa (valida antes de escrever) │
│ • Criar tag manual após merge se necessário                │
└─────────────────────────────────────────────────────────────┘
```

**Por que funciona para v0.x:**
- Projeto inicial, poucos contexts
- Mudanças frequentes
- Flexibilidade máxima

### 7.2 Fase Crescimento (v1.x) - FUTURO

**Estratégia:** **Versão por Contexto + Híbrido**

```
┌─────────────────────────────────────────────────────────────┐
│ EVOLUÇÃO (quando atingir v1.0)                             │
├─────────────────────────────────────────────────────────────┤
│ • Cada context tem VERSION próprio                         │
│ • Workflow detecta bumps por context                       │
│ • Cria PR de release para aprovação                         │
│ • Release Manager aprova/rejeita                            │
└─────────────────────────────────────────────────────────────┘
```

**Quando migrar:**
- Quando tiver 5+ contexts independentes
- Quando tiver 2+ maintainers
- Quando releases se tornarem frequentes (semanal/diário)

### 7.3 Fase Maduro (v2.x+) - FUTURO

**Estratégia:** **Versionamento Semântico por Contexto + API Contracts**

```
┌─────────────────────────────────────────────────────────────┐
│ MATURIDADE (quando estável)                                │
├─────────────────────────────────────────────────────────────┤
│ • API versionada por header (v1, v2)                        │
│ • Contratos entre contexts versionados                      │
│ • Release cadence definida (ex: quinzenal)                  │
│ • Breaking changes requerem RFC/ADR                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Padrões Profissionais: Casos Reais

### 8.1 Kubernetes (Manual + Equipe)

**Estratégia:**
- Release Managers: @kubernetes/release-managers
- PR de release: `kubernetes/kubernetes/pull/XXXXX`
- Processo: Proposta → Discussão → Aprovação → Release

**Por que funciona:**
- Projeto massivo (1000+ contribuidores)
- Muitos sub-projetos (kubectl, kube-proxy, etc.)
- Requer consistência absoluta

### 8.2 Rust (Híbrido + Auto-Bump)

**Estratégia:**
- `cargo publish` detecta versão via `Cargo.toml`
- `bors` (bot) aprova merge → auto-publica crates.io
- Release criado automaticamente

**Por que funciona:**
- Ecossistema de crates versionados independentemente
- Ferramenta (`cargo`) padroniza processo

### 8.3 Angular (Auto-Bump Puro)

**Estratégia:**
- `semantic-release` gera versão automaticamente
- Commit `feat` → MINOR bump
- Commit `fix:` → PATCH bump
- Breaking change → MAJOR bump

**Por que funciona:**
- Ferramenta padronizada (`angular-cli`)
- Time relativamente pequeno (~20 maintainers)
- Comunidade segue Conventional Commits

---

## 9. Solução Imediata para PR #6

### 9.1 Validar Workflow Atual

**Problema:** Workflow pode tentar re-bumpar

**Solução:** Atualizar workflow para detectar VERSION já bumpada

```yaml
# Adicionar step de validação
- name: Check if VERSION already bumped
  run: |
    source VERSION
    CURRENT_VERSION=$SKYBRIDGE_VERSION

    # Calcula versão alvo
    if [ "$BUMP_TYPE" == "major" ]; then
      # ... calcula MAJOR bump
    elif [ "$BUMP_TYPE" == "minor" ]; then
      # ... calcula MINOR bump
    fi

    # Se VERSION já está na versão alvo, skip
    if [ "$CURRENT_VERSION" == "$NEW_VERSION" ]; then
      echo "VERSION já está em $NEW_VERSION, skip bump"
      echo "skip_bump=true" >> $GITHUB_OUTPUT
    fi
```

### 9.2 Ação Imediata

**Opção A: Manter como está** ✅ RECOMENDADO

- Commit manual no PR: `chore(release): bump versão para 0.3.0`
- Workflow vai detectar VERSION=0.3.0
- Workflow NÃO vai re-bumpar (vai apenas criar tag e release)

**Opção B: Remover commit manual**

- Remover commit `chore(release): bump versão para 0.3.0`
- Workflow vai criar commit automaticamente
- Tag e release criados pelo workflow

**Opção C: Criar tag manualmente**

```bash
git tag -a "v0.3.0" -m "Release v0.3.0"
git push origin v0.3.0
```

---

## 10. Conclusão e Próximos Passos

### 10.1 Para PR #6 (Imediato)

**Decisão:** ✅ **Bump manual está CORRETO**

**Justificativa:**
- 3 funcionalidades novas (MINOR bump)
- Versão unificada faz sentido para v0.x
- Commit documentado: `chore(release): bump versão para 0.3.0`

**Próximo passo:**
- Manter PR como está
- Atualizar workflow para detectar VERSION já bumpada (se necessário)
- Observar comportamento após merge

### 10.2 Para Futuro (ADR019)

**Criar ADR:** "Versionamento por Contexto"

**Conteúdo:**
1. Definir bounded contexts da Skybridge
2. Especificar algoritmo de bump por context
3. Definir quando migrar para versionamento por context
4. Documentar contratos entre contexts

**Trigger para ADR019:**
- Quando atingir v1.0.0
- Quando tiver 5+ contexts independentes
- Quando surgir necessidade de releases independentes

---

## 11. Referências

- **ADR012:** Estratégia de Versionamento (atual)
- **Semver.org:** Semantic Versioning 2.0.0
- **Conventional Commits:** conventionalcommits.org
- **semantic-release:** github.com/semantic-release/semantic-release
- **Kubernetes Release:** kubernetes.io/docs/setup/release/
- **Rust Publishing:** doc.rust-lang.org/cargo/reference/publishing.html
- **release-drafter:** medium.com/@daniel.soaress/automatizando-a-gest%C3%A3o-de-releases-com-release-drafter-github-actions-b69bb266c85b

---

> "Versionamento é sobre comunicação, não apenas números" – made by Sky 📊
