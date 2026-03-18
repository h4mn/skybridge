# Guia de Versionamento - Skybridge

> **PL001 implementado (2026-01-25):** Git tags como fonte de verdade via `setuptools_scm`.

## Visão Geral

O Skybridge usa **git tags como fonte de verdade** para versionamento, eliminando conflitos de merge e permitindo versões dinâmicas que refletem o estado real de cada branch.

```
┌─────────────────────────────────────────────────────────────────────┐
│ MODELO ATUAL (PL001)                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  main:    tag v0.10.0 → versão 0.10.0                              │
│  dev:     3 commits após v0.10.0 → 0.10.0.dev3+gABC                 │
│  staging: 1 commit após v0.10.0 → 0.10.0.dev1+gXYZ                  │
│                                                                      │
│  Vantagens:                                                         │
│  ✅ Sem conflito de arquivos                                        │
│  ✅ Versão reflete estado real                                      │
│  ✅ Padrão Python (PEP 440)                                         │
│  ✅ Instalar qualquer commit historicamente                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Como Funciona

### 1. Cascade Fallback em `src/version.py`

```python
# 1. setuptools_scm auto-generated (preferred)
from ._version import version as __version__

# 2. Git describe (development fallback)
__version__ = f"{tag}.dev"  # ex: "0.10.0.dev"

# 3. Unknown (last resort)
__version__ = "0.0.0-unknown"
```

### 2. Formato de Versão

| Situação | Formato | Exemplo |
|----------|---------|---------|
| Commit com tag | `X.Y.Z` | `0.10.0` |
| N commits após tag | `X.Y.Z.devN+gHASH` | `0.10.0.dev3+gABC` |
| Sem tags | `0.0.0.postN+gHASH` | `0.0.0.post5+gXYZ` |

### 3. Arquivo Gerado (Não Versionado)

- **`src/_version.py`**: Gerado automaticamente por `setuptools_scm`
- Adicionado ao `.gitignore`
- Nunca edite manualmente

## Workflow de Release

### Automático (via GitHub Actions)

O workflow `.github/workflows/release.yml` é triggerado em **push para `main`**:

```yaml
1. Detect version bump (conventional commits)
   ├─ BREAKING CHANGE → MAJOR
   ├─ feat → MINOR
   └─ fix → PATCH

2. Calculate new version from latest tag
   Ex: v0.10.0 + feat → v0.11.0

3. Create and push git tag
   $ git tag -a "v0.11.0" -m "Release v0.11.0"
   $ git push origin "v0.11.0"

4. Update CHANGELOG.md

5. Create GitHub Release
```

### Manual (se necessário)

```bash
# 1. Fazer merge para main
git checkout main
git merge dev

# 2. Criar tag manualmente
git tag -a "v0.11.0" -m "Release v0.11.0"
git push origin "v0.11.0"

# 3. GitHub Actions vai gerar o release automaticamente
```

## Uso no Código

### Importar Versão

```python
from src.version import __version__

print(__version__)  # "0.10.0.dev3+gABC" (dev)
                   # "0.10.0" (main com tag)
```

### Versão Limpa (para display)

```python
import re
from src.version import __version__

# Remover sufixos de dev
clean_version = re.sub(r'\.dev\d+.*$', '', __version__)
clean_version = re.sub(r'\+.*$', '', clean_version)

print(clean_version)  # "0.10.0"
```

### Helper no `runtime/changelog.py`

```python
from runtime.changelog import get_project_version

version = get_project_version()  # "0.10.0" (já limpa)
```

## Conventional Commits

O versionamento automático depende de **conventional commits**:

```
<tipo>[escopo opcional]: <descrição>

[opcional corpo]

[opcional footer]
```

### Tipos que Geram Bump

| Tipo | Bump | Exemplo |
|------|------|---------|
| `feat` | MINOR | `feat(auth): implementar refresh token` |
| `fix` | PATCH | `fix(auth): corrigir leak de memória` |
| `BREAKING CHANGE` | MAJOR | `feat(protocol)!: mudar schema do envelope` |

### Tipos que NÃO Geram Bump

- `docs`: `docs: atualizar README`
- `chore`: `chore: atualizar dependências`
- `test`: `test(auth): adicionar testes`
- `refactor`: `refactor(kernel): simplificar código`

## Boas Práticas

### 1. Sempre Use Conventional Commits

```bash
# ✅ Bom
git commit -m "feat(auth): implementar refresh token"

# ❌ Ruim
git commit -m "implementando refresh token"
```

### 2. Para Breaking Changes, Use `!`

```bash
# ✅ Breaking change explícito
git commit -m "feat(api)!: mudar schema do envelope"

# ✅ Ou no footer
git commit -m "feat(api): novo endpoint de autenticação

BREAKING CHANGE: remove endpoint legado /auth/login"
```

### 3. Escopos Definidos

- `app`: aplicação Skybridge
- `kernel`: SDK interno
- `openapi`: contrato YAML
- `auth`: autenticação/autorização
- `fileops`: contexto de operações de arquivo
- `tasks`: contexto de tarefas
- `pl`: planos de implementação (PL***)

### 4. Nunca Edite `_version.py`

Este arquivo é gerado automaticamente. Edições manuais serão sobrescritas.

```bash
# ❌ NUNCA faça isso
vim src/_version.py

# ✅ Em vez disso, crie uma tag
git tag -a "v0.11.0" -m "Release v0.11.0"
```

## Troubleshooting

### Versão mostra "0.0.0-unknown"

**Causa:** Sem git tags disponíveis ou `.git` directory faltando.

**Solução:**
```bash
# Criar tag inicial
git tag -a "v0.1.0" -m "Initial release"
git push origin "v0.1.0"

# Ou verificar se está em um repo git
git status
```

### Versão mostra sufixo `.dev` em produção

**Causa:** Branch `main` sem tag no commit atual.

**Solução:**
```bash
# Criar tag no commit atual
git tag -a "v0.10.0" -m "Release v0.10.0"
git push origin "v0.10.0"
```

### `_version.py` não é gerado

**Causa:** `setuptools_scm` não instalado.

**Solução:**
```bash
pip install -e .
# ou
pip install "setuptools_scm[toml]>=8.0"
```

### Conflito de Merge em `_version.py`

**Causa:** Arquivo foi commitado acidentalmente.

**Solução:**
```bash
# Remover do versionamento
git rm --cached src/_version.py

# Adicionar ao .gitignore (se já não estiver)
echo "src/_version.py" >> .gitignore
```

## Referências

- **PL001**: `docs/plan/PL001-migrar-versionamento-git-tags.md`
- **ADR012**: `docs/adr/ADR012-estrategia-versionamento.md`
- **setuptools_scm**: https://setuptools-scm.readthedocs.io/
- **Conventional Commits**: https://www.conventionalcommits.org/
- **Semantic Versioning**: https://semver.org/

---

> "A melhor hora para plantar uma árvore foi há 20 anos. A segunda melhor hora é agora." – Provérbio Chinês

> "Versionamento sem caos é a base de confiança em evolução." – made by Sky 🚀
