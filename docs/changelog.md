# Changelog Generator

Documentação do gerador de changelog do Skybridge implementado em Python.

> "A disciplina dos changelogs é o respeito ao tempo de quem os lê" – made by Sky 📚

## Visão Geral

O `runtime/changelog.py` é um gerador de changelog completo em Python que substitui o `semantic-release` do Node.js, oferecendo:

- **Formato PT-BR** com emojis e categorização clara
- **Dois modos**: simples (padrão) e detalhado (com API GitHub)
- **Agrupamento por PR** com cabeçalhos clicáveis
- **Integração com GitHub Actions** para releases automatizados

## Uso Básico

### Modo Simples (Padrão)

Gera changelog sem usar a API do GitHub - apenas os commits do git local:

```bash
# Preview (dry-run)
python -m runtime.changelog

# Preview desde uma tag específica
python -m runtime.changelog 0.5.5 v0.5.4

# Aplicar e escrever no CHANGELOG.md
python -m runtime.changelog 0.5.5 v0.5.4 --apply
```

**Saída (simples):**
```markdown
### ✨ Novidades

* [`93468f5`](...) **ci:** implementar gerador de changelog Sky com Python [`@h4mn`](...)
* [`7534cd9`](...) **webhooks:** sincronização de labels ([#49](...)) [`@h4mn`](...)
```

### Modo Detalhado (`--detailed`)

Usa a API do GitHub para buscar commits internos das PRs e agrupa por PR:

```bash
# Preview detalhado
python -m runtime.changelog --detailed

# Preview detalhado desde uma tag
python -m runtime.changelog 0.5.5 v0.5.4 --detailed

# Aplicar modo detalhado
python -m runtime.changelog 0.5.5 v0.5.4 --detailed --apply
```

**Saída (detalhada):**
```markdown
### ✨ Novidades

[**#28**](https://github.com/h4mn/skybridge/pull/28) - implementar integração GitHub → Trello

* [`fb9ffe7`](...) **kanban:** implementar integração ([#28](...)) [`@h4mn`](...)
* [`48d3c9a`](...) **kanban:** contexto Kanban ([#28](...)) [`@h4mn`](...)

[**#33**](https://github.com/h4mn/skybridge/pull/33) - implementar FileBasedJobQueue

* [`c46da09`](...) **queue:** FileBasedJobQueue ([#33](...)) [`@h4mn`](...)
```

## Flags Disponíveis

| Flag | Descrição |
|------|-----------|
| `--apply` | Aplica as alterações e escreve no CHANGELOG.md |
| `--detailed` | Modo detalhado: usa API GitHub e agrupa commits por PR |
| `--from-git` | Gera changelog histórico completo do git (todas as tags) |
| `--from-gh` | Modo GitHub Actions: remove seção [Pendente] antes de processar |

## Modo Detalhado: API GitHub

### Funcionamento

No modo detalhado, o gerador:

1. **Busca commits internos das PRs** via GitHub REST API
2. **Agrupa commits por PR** mesmo com squash merge
3. **Mostra todos os commits** que fazem parte de uma PR, não apenas o commit de merge

### Requisitos

- `GITHUB_TOKEN` deve estar disponível (automático no GitHub Actions)
- Permissão `pull-requests: read` no workflow

### Exemplo de Enriquecimento

**Git log (squash merge):**
```
7534cd9 webhooks: sincronização de labels (#49)
```

**Modo detalhado (com API):**
```markdown
[**#49**](...) - sincronização de labels e correção de handlers

* [`93b8517`](...) **webhooks:** sincronização de labels ([#49](...))
* [`7534cd9`](...) **webhooks:** sincronização labels ([#49](...))
* [`3daab9f`](...) **runtime:** Demo Engine ([#49](...))
* [`33f47a0`](...) **webhooks:** branch base agentes ([#49](...))
* [`195412c`](...) **queue:** FileBasedJobQueue ([#49](...))
* [`93468f5`](...) **ci:** gerador changelog Python
* [`9260458`](...) **webhooks:** idempotência correlation ID ([#25](...))
```

## GitHub Actions Integration

### Workflow Release

O workflow `.github/workflows/release.yml` usa o changelog generator:

```yaml
- name: Generate changelog (Sky format)
  run: |
    NEW_VERSION="${{ steps.bump_version.outputs.new_version }}"
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    python -m runtime.changelog "${NEW_VERSION}" "${LATEST_TAG}" --from-gh --detailed --apply
```

### Flags no CI

- `--from-gh`: Remove a seção `[Pendente]` antes de gerar o changelog da versão
- `--detailed`: Usa API GitHub para mostrar commits internos das PRs
- `--apply`: Escreve no CHANGELOG.md

## Formato do Changelog

### Estrutura

O changelog segue o formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/):

```markdown
# Changelog

## [Pendente]

### ✨ Novidades
* Commits de novos recursos

### 🐛 Correções
* Commits de correções de bugs

## [0.5.4] - 2026-01-19

### 📚 Documentação
* Commits de documentação
```

### Categorias

| Tipo | Categoria | Emoji |
|------|-----------|-------|
| `feat` | Novidades | ✨ |
| `fix` | Correções | 🐛 |
| `refactor` | Refatoração | ♻️ |
| `docs` | Documentação | 📚 |
| `style` | Estilos | 💅 |
| `perf` | Performance | ⚡ |
| `test` | Testes | ✅ |
| `build` | Build | 📦 |
| `ci` | CI | 👷 |
| `chore` | Tarefas | 🧹 |
| `revert` | Reverter | ⏪ |

## Conventional Commits

O gerador reconhece commits no formato Conventional Commits:

```
tipo(scope): descrição

# Exemplos:
feat(webhooks): adicionar integração com Trello
fix(queue): corrigir race condition em job processing
docs(changelog): documentar novo formato
```

### Escopos (scope)

O escopo é opcional, mas quando presente, aparece em **negrito** no changelog:

```
**webhooks:** adicionar integração com Trello
```

## Referências de PR

O gerador detecta automaticamente números de PR nos commits:

- No subject: `feat(webhooks): adicionar feature (#49)`
- No footer: `#49`

Os links são gerados automaticamente para o repositório configurado.

## Desenvolvimento

### Executar Localmente

```bash
# Instalar dependências (se necessário)
pip install requests

# Testar changelog simples
python -m runtime.changelog

# Testar changelog detalhado
python -m runtime.changelog --detailed

# Regenerar changelog histórico completo (simples)
python -m runtime.changelog --from-git --apply

# Regenerar changelog histórico completo (detalhado)
python -m runtime.changelog --from-git --detailed --apply
```

### Testes

```bash
# Ver commits que seriam incluídos
git log v0.5.4..HEAD --pretty=format:"%H|%s|%an|%ae"

# Testar parsing de commits
python -c "
from runtime.changelog import get_commits_since, generate_changelog_simple
commits = get_commits_since('v0.5.4')
print(generate_changelog_simple(commits))
"
```

## Troubleshooting

### GITHUB_TOKEN não encontrado

**Problema:**
```
⚠️  GITHUB_TOKEN não encontrado. Pulando busca de commits da PR #49
```

**Solução:**
- No GitHub Actions, o token é automático
- Localmente, exporte a variável: `export GITHUB_TOKEN=seu_token`

### Nenhum commit novo para adicionar

**Problema:**
```
⚠️  Nenhum commit novo para adicionar ao CHANGELOG.md
```

**Solução:**
- Os commits já estão no CHANGELOG.md
- Use `--from-git` para regenerar tudo do zero
- Ou faça novos commits desde a última tag

### Commits duplicados

**Problema:** Commits aparecem duplicados no changelog

**Solução:** O gerador usa `filter_new_commits()` para ignorar commits já presentes no CHANGELOG.md baseado no hash curto (7 caracteres).

## ADR Relacionado

Ver `ADR012` para decisões sobre versionamento e gerenciamento de changelog.

---

> "Simplicidade é o último grau de sofisticação" – made by Sky 🚀
