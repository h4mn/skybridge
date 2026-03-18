# PL001: Migrar Versionamento para Git Tags

> **Status**: Proposto
> **Data**: 2026-01-25
> **Autor**: Sky
> **Aprovado por**: Pendente
> **Relacionado**: ADR012 (Single Source of Truth)

---

## 📋 Resumo Executivo

Migrar o sistema de versionamento do Skybridge de arquivo `VERSION` hardcoded para **git tags como fonte de verdade** usando `setuptools_scm`, eliminando conflitos de sincronização entre branches e seguindo melhores práticas do ecossistema Python.

### Problema Atual

```bash
# PROBLEMA: VERSION desincronizado entre branches
main:    VERSION=0.10.0  (release)
dev:     VERSION=0.9.0   (ficou para trás)
staging: VERSION=0.8.0   (mais atrás ainda)

# CAUSA RAIZ
src/version.py está HARDCODED "0.5.4-dev"
Workflow atualiza VERSION mas não propaga para dev
```

### Solução Proposta

```bash
# SOLUÇÃO: Git tags como source of truth
main:    tag v0.10.0 → versão 0.10.0
dev:     3 commits após v0.10.0 → versão 0.10.0.dev3+gABC
staging: 1 commit após v0.10.0 → versão 0.10.0.dev1+gXYZ

# VANTAGENS
✅ Sem conflito de arquivos
✅ Versão sempre reflete estado real
✅ Padrão Python (PEP 440)
✅ Instalar qualquer commit historicamente
```

---

## 🎯 Objetivos

### Primário
- Eliminar desincronização de `VERSION` entre branches
- Adotar `setuptools_scm` como gerador de versão dinâmico
- Usar git tags como única fonte de verdade

### Secundários
- Simplificar workflow de release
- Melhorar rastreabilidade de releases
- Alinhar com padrões do ecossistema Python

---

## 📊 Análise de Impacto

### Afetados

| Componente | Impacto | Esforço |
|------------|---------|---------|
| `src/version.py` | 🔴 Alto | 2h |
| `VERSION` file | 🟡 Médio | 1h |
| `pyproject.toml` | 🟡 Médio | 1h |
| `.github/workflows/release.yml` | 🔴 Alto | 3h |
| `runtime/changelog.py` | 🟡 Médio | 1h |
| Testes de versão | 🟡 Médio | 2h |
| Documentação | 🟢 Baixo | 1h |

### Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Break em produção | Média | Alto | Fases de rollout + rollback plan |
| Incompatibilidade com dependências | Baixa | Médio | Testes exhaustivos em staging |
| Time de deploy > janela | Baixa | Médio | Planejamento antecipado |
| Perda de histórico de versões | Baixa | Alto | Manter tags antigas |

---

## 📅 Fases de Migração

### FASE 0: Preparação (1 dia)

**Objetivo**: Entender estado atual e preparar ambiente

#### Tarefas

- [ ] **0.1** Documentar fluxo atual de versionamento
- [ ] **0.2** Identificar todos os pontos que usam `VERSION`
- [ ] **0.3** Criar branch `feature/git-versioning`
- [ ] **0.4** Setup de ambiente de testes isolado

**Critério de Sucesso**: Branch criada e inventário completo

---

### FASE 1: Implementação Base (2 dias)

**Objetivo**: Implementar `setuptools_scm` mantendo compatibilidade

#### 1.1 Configurar `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0", "setuptools_scm[toml]>=8.0"]
build-backend = "setuptools.build_meta"

[project]
name = "skybridge"
dynamic = ["version"]

[tool.setuptools_scm]
write_to = "src/_version.py"
version_scheme = "release-branch-semver"
tag_prefix = "v"
fallback_version = "0.0.0"
```

#### 1.2 Reescrever `src/version.py`

```python
# src/version.py
"""
Version module for Skybridge.

Single Source of Truth: Git Tags via setuptools_scm
Priority:
  1. Auto-generated _version.py (from git tags)
  2. VERSION file (legacy, fallback)
  3. Git describe (development fallback)
  4. Unknown (last resort)
"""

import os
from pathlib import Path

# Tenta 1: setuptools_scm auto-generated
try:
    from ._version import version as __version__
except ImportError:
    # Tenta 2: VERSION file (compatibilidade)
    version_file = Path(__file__).parent.parent / "VERSION"
    if version_file.exists():
        for line in version_file.read_text().split("\n"):
            if line.startswith("SKYBRIDGE_VERSION="):
                __version__ = line.split("=")[1].strip()
                break
    else:
        # Tenta 3: Git describe
        import subprocess
        try:
            tag = subprocess.check_output(
                ["git", "describe", "--tags", "--abbrev=0"],
                stderr=subprocess.DEVNULL
            ).decode().strip().lstrip("v")
            __version__ = f"{tag}.dev"
        except:
            # Tenta 4: Fallback final
            __version__ = "0.0.0-unknown"

__all__ = ["__version__"]
```

#### 1.3 Atualizar `.gitignore`

```gitignore
# Arquivos gerados pelo setuptools_scm
src/_version.py
```

#### 1.4 Testes Locais

```bash
# Teste 1: Versão em branch sem tag
python -c "from src.version import __version__; print(__version__)"
# Esperado: 0.10.0.dev ou similar

# Teste 2: Versão em tagged commit
git tag v0.10.0-test
python -c "from src.version import __version__; print(__version__)"
# Esperado: 0.10.0-test

# Teste 3: Compatibilidade com VERSION file
echo "SKYBRIDGE_VERSION=0.9.0" > VERSION
python -c "from src.version import __version__; print(__version__)"
# Esperado: 0.9.0 (fallback funciona)
```

**Critério de Sucesso**: Todos os testes passam

---

### FASE 2: Atualizar Workflow de Release (2 dias)

**Objetivo**: Simplificar workflow para criar apenas tags

#### 2.1 Simplificar `.github/workflows/release.yml`

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Detect version bump
        id: bump
        run: |
          LATEST_TAG=$(git describe --tags --abbrev=0)
          COMMITS=$(git log ${LATEST_TAG}..HEAD --pretty=format:"%s")

          if echo "$COMMITS" | grep -qE "BREAKING|feat.*!"; then
            echo "bump=major" >> $GITHUB_OUTPUT
          elif echo "$COMMITS" | grep -qE " feat"; then
            echo "bump=minor" >> $GITHUB_OUTPUT
          elif echo "$COMMITS" | grep -qE " fix"; then
            echo "bump=patch" >> $GITHUB_OUTPUT
          else
            echo "bump=none" >> $GITHUB_OUTPUT
          fi

      - name: Calculate new version
        if: steps.bump.outputs.bump != 'none'
        id: version
        run: |
          LATEST_TAG=$(git describe --tags --abbrev=0)
          CURRENT=${LATEST_TAG#v}

          IFS='.' read -ra PARTS <<< "$CURRENT"
          case "${{ steps.bump.outputs.bump }}" in
            major)
              PARTS[0]=$((${PARTS[0]} + 1))
              PARTS[1]=0; PARTS[2]=0
              ;;
            minor)
              PARTS[1]=$((${PARTS[1]} + 1))
              PARTS[2]=0
              ;;
            patch)
              PARTS[2]=$((${PARTS[2]} + 1))
              ;;
          esac

          NEW_VERSION="${PARTS[0]}.${PARTS[1]}.${PARTS[2]}"
          echo "version=${NEW_VERSION}" >> $GITHUB_OUTPUT

      - name: Create and push tag
        if: steps.bump.outputs.bump != 'none'
        run: |
          NEW_VERSION=${{ steps.version.outputs.version }}

          # Criar tag anotada
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}"
          git push origin "v${NEW_VERSION}"

      - name: Update CHANGELOG
        if: steps.bump.outputs.bump != 'none'
        run: |
          NEW_VERSION=${{ steps.version.outputs.version }}
          python -m runtime.changelog "${NEW_VERSION}" --from-gh --apply

          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add CHANGELOG.md
          git commit -m "docs(release): update changelog for ${NEW_VERSION}"
          git push

      - name: Create GitHub Release
        if: steps.bump.outputs.bump != 'none'
        uses: softprops/action-gh-release@v1
        with:
          tag_name: "v${{ steps.version.outputs.version }}"
          name: "Release v${{ steps.version.outputs.version }}"
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

#### 2.2 Testar Workflow em Branch de Teste

```bash
# Criar branch de teste
git checkout -b test/release-workflow

# Fazer commit fictício
echo "# test" >> README.md
git commit -am "feat: test release workflow"

# Push e observar workflow
git push origin test/release-workflow

# Verificar se tag foi criada corretamente
```

**Critério de Sucesso**: Workflow cria tags e não modifica VERSION

---

### FASE 3: Remover Dependências do VERSION (1 dia)

**Objetivo**: Eliminar uso do arquivo VERSION progressivamente

#### 3.1 Remover VERSION do versionamento ativo

```bash
# Renomear VERSION para VERSION.legacy
mv VERSION VERSION.legacy

# Adicionar ao .gitignore se já não estiver
echo "VERSION.legacy" >> .gitignore
```

#### 3.2 Atualizar runtime/changelog.py

```python
# runtime/changelog.py - linha ~32
def get_project_version() -> str:
    """Retorna a versão do projeto a partir de git tags."""
    # Tenta obter versão de src/version.py (que lê de git)
    from src.version import __version__
    return __version__.replace("-dev", "")
```

#### 3.3 Testes de Regressão

```bash
# Teste 1: Aplicação inicia corretamente
python -m apps.server.main &
# Verificar console: deve mostrar versão correta

# Teste 2: Testes passam
pytest tests/ -v

# Teste 3: Pip install local funciona
pip install -e .
python -c "import skybridge; print(skybridge.__version__)"
```

**Critério de Sucesso**: Sistema funciona sem VERSION.legacy

---

### FASE 4: Rollout Gradual (3 dias)

**Objetivo**: Deploy em produção com monitoramento

#### 4.1 Dia 1: Merge para dev

```bash
# Dia 1 - Manhã
git checkout dev
git merge feature/git-versioning
git push origin dev

# Monitorar:
- Logs da aplicação em dev
- Versão reportada no console
- Testes automatizados
```

**Métricas de Sucesso:**
- ✅ Sem erros de import de versão
- ✅ Versão no console tem formato X.Y.Z.devN
- ✅ Todos os testes passam

#### 4.2 Dia 2: Merge para staging (se existe)

```bash
# Dia 2
git checkout staging
git merge dev
git push origin staging

# Monitorar:
- Performance
- Logs de erro
- Comportamento de agentes
```

#### 4.3 Dia 3: Merge para main

```bash
# Dia 3
git checkout main
git merge dev

# Criar tag de release manualmente (primeira vez)
git tag v0.11.0
git push origin main --tags

# Verificar workflow de release
```

**Critério de Sucesso**: Produção estável por 24h

---

### FASE 5: Limpeza (1 dia)

**Objetivo**: Remover código legacy e documentar

#### Tarefas

- [ ] **5.1** Deletar `VERSION.legacy`
- [ ] **5.2** Remover fallback de VERSION em `src/version.py`
- [ ] **5.3** Atualizar ADR012 com novo sistema
- [ ] **5.4** Criar guia de versionamento em docs/
- [ ] **5.5** Deletar branch `feature/git-versioning`

**Critério de Sucesso**: Sistema limpo e documentado

---

## 🔄 Rollback Plan

### Gatilhos de Rollback

- Erros críticos em produção
- Versões inconsistentes entre ambientes
- Performance degradation > 20%

### Procedimento

```bash
# ROLLBACK RÁPIDO (< 5 min)
git checkout main
git revert <merge-commit>
git push origin main

# ROLLBACK COMPLETO
git checkout main
git reset --hard origin/main~1  # Antes do merge
git push origin main --force

# Restaurar VERSION manualmente se necessário
echo "SKYBRIDGE_VERSION=0.10.0" > VERSION
git commit -am "rollback: restore VERSION file"
git push
```

### Pontos de Restauração

| Fase | Rollback Complexity | Tempo Estimado |
|------|---------------------|----------------|
| Fase 1 | Baixo | < 5 min |
| Fase 2 | Médio | 15 min |
| Fase 3 | Médio | 15 min |
| Fase 4 | Alto | 30 min |
| Fase 5 | Baixo | 5 min |

---

## 📈 Métricas de Sucesso

### Técnicas

| Métrica | Antes | Depois | Target |
|---------|-------|--------|--------|
| Tempo de release | 15 min | 5 min | -67% |
| Conflitos de VERSION | 5/semana | 0 | -100% |
| Passos manuais | 3 | 0 | -100% |
| Erros de versão | 2/mês | 0 | -100% |

### Qualitativas

- ✅ Time dev não precisa mais manter VERSION
- ✅ Release consiste apenas em criar tag
- ✅ Pode instalar qualquer commit historicamente
- ✅ Alinhado com padrões Python

---

## 📚 Referências

- [PEP 440 - Version Identification](https://peps.python.org/pep-0440/)
- [setuptools_scm Documentation](https://setuptools-scm.readthedocs.io/)
- [Versioning Python packages on GitHub](https://medium.com/@thomas.vidori/versioning-python-packages-on-github-dc7c82a9a5ff)
- [GitOps Best Practices](https://akuity.io/blog/gitops-best-practices-whitepaper)

---

## 🗓️ Cronograma

| Fase | Duração | Data Início | Data Fim | Responsável |
|------|---------|-------------|----------|-------------|
| Fase 0 | 1 dia | 2026-01-27 | 2026-01-27 | Sky |
| Fase 1 | 2 dias | 2026-01-28 | 2026-01-29 | Sky |
| Fase 2 | 2 dias | 2026-01-30 | 2026-01-31 | Sky |
| Fase 3 | 1 dia | 2026-02-01 | 2026-02-01 | Sky |
| Fase 4 | 3 dias | 2026-02-02 | 2026-02-04 | Sky + Aprovação |
| Fase 5 | 1 dia | 2026-02-05 | 2026-02-05 | Sky |

**Total**: 10 dias úteis

---

## ✅ Checklist de Aprovação

- [ ] Plano revisado por time técnico
- [ ] Riscos avaliados e mitigados
- [ ] Rollback testado
- [ ] Documentação atualizada
- [ ] Stakeholders informados
- [ ] Janela de manutenção agendada

---

> "A melhor hora para plantar uma árvore foi há 20 anos. A segunda melhor hora é agora." – Provérbio Chinês

> "Migração bem-sucedida é aquela que ninguém nota, exceto pela ausência de problemas" – made by Sky 🚀
