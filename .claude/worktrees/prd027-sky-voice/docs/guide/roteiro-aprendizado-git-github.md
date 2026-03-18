# Roteiro de Aprendizado: Git & GitHub Avançado

Guia prático para evoluir suas habilidades de versionamento e colaboração.

---

## 🎯 Próximos Passos Sugeridos (em ordem de prioridade)

### 1. Git Rebase Interativo ⭐⭐⭐ (IMPORTANTE)

Você viu hoje que PRs tinham **17 commits** quando deveriam ter 1-2. Rebase resolve isso:

```bash
# Squash múltiplos commits em 1
git rebase -i main --autosquash

# O que cada opção significa:
# pick  = usa este commit como está
# reword = usa mas edita a mensagem
# edit = pausa para você fazer mudanças manuais
# squash = merge no commit anterior (1 mensagem)
# fixup = merge no commit anterior (descarta mensagem)
# drop = descarta o commit completamente
```

**Por que aprender**:
- PRs limpos = reviews mais rápidas
- Histórico organizado
- Fácil de entender o que foi feito

---

### 2. Git Worktree Management ⭐⭐⭐

Você usou worktrees hoje, mas pode gerenciar melhor:

```bash
# Listar worktrees
git worktree list

# Remover worktree após PR mergeado
git worktree remove ../path/to/worktree

# Criar worktree para issue específica
git worktree add ../skybridge-issue-66 issue-66

# Mover worktree (se mudou de lugar)
git worktree move ../old-path ../new-path
```

**Por que aprender**:
- Trabalhar em múltiplas issues ao mesmo tempo
- Isolar experimentos sem poluir branch principal
- Manter repositório limpo

---

### 3. GitHub Actions para Automação ⭐⭐

Automatizar tarefas repetitivas:

```yaml
# .github/workflows/auto-label-prs.yml
name: Auto-label PRs

on:
  pull_request:
    types: [opened]

jobs:
  auto-label:
    runs-on: ubuntu-latest
    steps:
      - name: Check if PR from Skybridge
        if: contains(github.event.pull_request.body, 'made with Sky')
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.addLabels({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              labels: ['skybridge-auto']
            })
```

**Por que aprender**:
- PR #69 é sobre isso (label automático)
- CI/CD é requisito em times modernos
- Economiza tempo manual

---

### 4. Semantic Versioning + Conventional Commits ⭐⭐

Você já usa Conventional Commits, mas pode refinar:

```bash
# Tipos semânticos
feat:     nova funcionalidade (MINOR version)
fix:      correção de bug (PATCH version)
BREAKING CHANGE: quebra compatibilidade (MAJOR version)

# Exemplo completo
feat(api)!: remove endpoint deprecated

Esta é uma BREAKING CHANGE porque remove
compatibilidade com versões anteriores.
```

**Ferramenta sugerida**: `commitizen` / `cz-cli`

```bash
# Instalar
npm install -g commitizen cz-conventional-changelog

# Usar ao invés de git commit
git cz
```

---

### 5. Git Hooks (pre-commit, pre-push) ⭐

Automatizar validações locais:

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Rodar testes antes de commitar
pytest tests/ -x

if [ $? -ne 0 ]; then
  echo "❌ Tests falharam. Commit abortado."
  exit 1
fi
```

**Ou usar pre-commit framework**:

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/ -x
        language: system
```

**Por que aprender**:
- Prevenir commits quebrados
- Padronizar código (black, pylint, etc)
- Economiza tempo de CI

---

### 6. Git Reflog para Recuperação ⭐⭐ (SALVA-VIDAS)

```bash
# Ver histórico de TODAS as operações
git reflog

# Recover branch deletada por engano
git reflog
# Encontra o commit: abc1234 HEAD@{5}: merge PR #70
git branch recover-branch abc1234

# Desfazer merge que deu conflito
git reset --hard HEAD@{1}
```

**Por que aprender**:
- Todo mundo comete erros
- Recuperar work perdido
- "Undo button" do Git

---

### 7. Git Bisect para Debug ⭐

Encontrar commit que quebrou algo:

```bash
# Iniciar bisect
git bisect start

# Marcar commit atual como "ruim"
git bisect bad

# Marcar commit antigo como "bom"
git bisect good HEAD~20

# Git vai pular para commit do meio
# Teste e marque:
git bisect bad   # se bug está aqui
git bisect good  # se bug não está aqui

# Repita até encontrar o commit culpado
git bisect reset
```

---

### 8. GitHub CLI Avançado ⭐⭐

Você usou `gh` hoje, mas tem muito mais:

```bash
# Ver PRs com filtros complexos
gh pr list --search "label:skybridge-auto" --state closed

# Editar múltiplas issues de uma vez
gh issue list --search "label:bug" --json number | \
  jq '.[].number' | \
  xargs -I {} gh issue edit {} --add-label "triaged"

# Criar template de issue
gh issue create --body-file .github/ISSUE_TEMPLATE/bug.md

# Ver métricas de PR
gh pr view 70 --json additions,deletions,changedFiles,commits

# Merge PR com delete automático de branch
gh pr merge 70 --merge --delete-branch
```

---

### 9. Branching Strategies ⭐⭐

Diferentes modelos de trabalho:

#### GitHub Flow (Simples)
```
main → branch → PR → merge → main
```

#### Git Flow (Complexo)
```
main (produção)
  ↓
develop (desenvolvimento)
  ↓
feature/*, release/*, hotfix/*
```

#### Trunk-Based Development (Avançado)
```
main sempre deployável
feature flags em vez de branches
```

---

## 📚 Roteiro de Aprendizado Sugerido

### Semana 1: Fundamentos Solidificar

- [ ] **Git Rebase Interativo** (praticar com branches de teste)
- [ ] **Git Worktree Management** (limpar worktrees antigos)
- [ ] **Git Reflog** (saber recuperar se der merda)

### Semana 2: Automação

- [ ] **Pre-commit hooks** (instalar e configurar)
- [ ] **GitHub Actions básico** (criar workflow simples)
- [ ] **Commitizen** (padronizar mensagens)

### Semana 3: GitHub Avançado

- [ ] **GitHub CLI avançado** (scripts com gh)
- [ ] **Labels automáticas** (resolver Issue #69)
- [ ] **Templates de issue/PR**

### Semana 4: Debug e Recuperação

- [ ] **Git Bisect** (encontrar bug)
- [ ] **Git Blame** (histórico de linha)
- [ ] **Git Log avançado** (filtros e formatação)

---

## 🎯 Prática Sugerida para Hoje

### Exercício 1: Limpeza de Worktrees

```bash
# 1. Listar worktrees
git worktree list

# 2. Identificar worktrees de PRs já mergeados
# 3. Remover worktrees não usados
git worktree remove ../path/to/old-worktree

# 4. Prune worktrees deletados
git worktree prune
```

### Exercício 2: Criar Template de Issue

```bash
# Criar .github/ISSUE_TEMPLATE/feature.md
gh issue create --title "Teste de template" --body-file -
```

### Exercício 3: Rebase Simulado

```bash
# 1. Criar branch de teste
git checkout -b test-rebase

# 2. Fazer 3 commits pequenos
echo "a" > a.txt && git add . && git commit -m "feat: add a"
echo "b" > b.txt && git add . && git commit -m "feat: add b"
echo "c" > c.txt && git add . && git commit -m "feat: add c"

# 3. Squash em 1 commit
git rebase -i main
# Mudar para: pick, fixup, fixup

# 4. Ver resultado
git log --oneline
```

---

## 📖 Recursos Recomendados

### Livros/Documentação

- [Pro Git Book](https://git-scm.com/book) - Gratuito, completo
- [GitHub Skills](https://skills.github.com/) - Interativo, prático
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

### Canais YouTube

- **Git & GitHub Bootcamp** (freeCodeCamp)
- **GitHub Actions** (官方频道)
- **Advanced Git Techniques** (Git minutos)

### Ferramentas para Praticar

- [Learn Git Branching](https://learngitbranching.js.org/) - **JOGO INTERATIVO** ⭐
- [Oh Shit, Git!?!](https://ohshitgit.com/) - Quando dá merda
- [GitHub Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Git Visual Simulator](https://git-school.github.io/visualization/)

### Ferramentas CLI

```bash
# Pre-commit framework
pip install pre-commit

# Commitizen (mensagens padronizadas)
npm install -g commitizen cz-conventional-changelog

# GitHub CLI (você já tem)
gh --version

# Git-flow (se quiser usar Git Flow)
# (não recomendado para projetos pequenos)
```

---

## 🔧 Comandos Rápidos de Referência

### Rebase

```bash
# Rebase interativo
git rebase -i main

# Rebase com autosquash (usa mensagens como "fixup!")
git rebase -i main --autosquash

# Continuar rebase após conflito
git rebase --continue

# Abortar rebase (voltar ao estado original)
git rebase --abort

# Skip commit atual
git rebase --skip
```

### Worktree

```bash
# Criar worktree
git worktree add ../path branch-name

# Listar worktrees
git worktree list

# Remover worktree
git worktree remove ../path

# Prune worktrees deletados
git worktree prune

# Mover worktree
git worktree move ../old ../new
```

### Reflog

```bash
# Ver reflog
git reflog

# Ver reflog com detalhes
git reflog show --all

# Recommit perdido no reflog
git log --walk-reflogs

# Reset para ponto no reflog
git reset --hard HEAD@{5}
```

### Bisect

```bash
# Iniciar bisect
git bisect start

# Marcar commits
git bisect good abc123
git bisect bad def456

# Pular para next commit
git bisect next

# Reset após terminar
git bisect reset
```

---

## 🎓 Dicas de Boas Práticas

### Commits

- ✅ Um commit = uma ideia lógica
- ✅ Mensagem no imperativo ("Add feature" não "Added feature")
- ✅ Corpo do commit explica "por que", não "o quê"
- ❌ Nunca commite código quebrado
- ❌ Nunca commite segredos (senhas, tokens)

### Branches

- ✅ Branches curtos (merge em 1-2 dias)
- ✅ Nomes descritivos: `feature/nome-funcionalidade`
- ✅ Deletar branch após merge
- ❌ Nunca commite diretamente em main/produção

### PRs

- ✅ Título claro e conciso
- ✅ Descrição explica "o que" e "por que"
- ✅ Screenshots para mudanças visuais
- ✅ Link para issues relacionadas
- ❌ PRs gigantes (>500 linhas)
- ❌ PRs sem descrição

---

## 🚀 Checklist Antes de Push/PR

### Antes de Pushar

- [ ] Código está formatado (black, pylint)
- [ ] Tests passando localmente
- [ ] Commits estão squashed (se necessário)
- [ ] Mensagens seguem Conventional Commits
- [ ] Nada em `.gitignore` foi commitado
- [ ] Segredos removidos (grep -r "sk-" / "token")

### Antes de Abrir PR

- [ ] Branch está atualizada com main
- [ ] CI passou (se houver)
- [ ] Descrição completa do que foi feito
- [ ] Issues relacionadas linkadas
- [ ] Co-autores adicionados (se aplicável)
- [ ] Labels apropriadas adicionadas

---

## 🐛 Solução de Problemas Comuns

### "Commitei algo errado"

```bash
# Se ainda não fez push
git reset --soft HEAD~1  # mantém mudanças
# ou
git reset --hard HEAD~1   # descarta mudanças

# Se já fez push
git revert HEAD
git push
```

### "Merge deu conflito"

```bash
# Abortar merge
git merge --abort

# Continuar após resolver conflitos
git add .
git commit  # sem argumentos
```

### "Deleti branch por engano"

```bash
# Se ainda tem o worktree
git worktree list
git checkout branch-name

# Se deletou worktree também
git reflog  # encontrar o commit
git branch branch-name abc1234
```

### "Quero mudar mensagem do último commit"

```bash
git commit --amend  # abre editor
# ou
git commit --amend -m "Nova mensagem"
```

---

## 📝 Glossário

| Termo | Significado |
|-------|-------------|
| **HEAD** | Ponteiro para o commit atual |
| **Branch** | Ponteiro móvel para commit |
| **Merge** | Unir histórico de dois branches |
| **Rebase** | Reaplicar commits em outra base |
| **Fast-forward** | Merge quando não há divergência |
| **Upstream** | Branch remoto (origin/main) |
| **Detached HEAD** | Estado sem apontar para branch |
| **Squash** | Comprimir múltiplos commits em um |
| **Cherry-pick** | Aplicar commit específico |
| **Reflog** | Log de todas as operações locais |

---

## 🎯 Próximos Passos

1. **Praticar** os exercícios sugeridos
2. **Escolher** uma ferramenta nova por semana
3. **Criar** um repositório de teste
4. **Quebrar** coisas propositalmente e recuperar
5. **Ensinar** alguém else (melhor forma de aprender)

> "A melhor forma de aprender Git é usando Git diariamente" – made by Sky 🚀

---

**Última atualização**: 2026-01-24
**Versão**: 1.0
**Autoria**: Sky (assistant)
**Repositório**: skybridge/docs/guide/
