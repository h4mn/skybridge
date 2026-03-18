# Git Workflow com Múltiplos Agentes

**Problema:** Quando múltiplos agentes trabalham na mesma branch, operações de `git revert` podem causar perda de código não rastreada.

**Data:** 2026-02-05
**Contexto:** Revert 1bab198 perdeu o RequestLoggingMiddleware (91 linhas)

---

## 🚨 O Problema do Revert

```bash
# Cenário real:
53ac8d4 → feat(server): RequestLoggingMiddleware CRIADO
1bab198 → Revert "feat(server): ..." (remove 1.949 linhas!)
f911725 → chore(server): restaura apps/server/main.py (PARCIAL)
```

O `git revert` cria um commit que **inverte** as mudanças de outro commit. Isso pode:
- Remover arquivos inteiros
- Desfazer mudanças em múltiplos arquivos
- **Perder código que não estava em nenhum commit anterior**

---

## ✅ Prevenção - Regras para Operações Destrutivas

### 1. ANTES de qualquer operação destrutiva:

```bash
# Verifique o que será afetado
git revert --no-commit <commit>
git status

# Ou para resets:
git reset --soft <commit>  # safer, mantém mudanças staged
git status
```

### 2. Use `--no-commit` para reverts:

```bash
# Revert sem commit automático
git revert --no-commit <commit>

# Verifique manualmente
git status
git diff

# Se estiver ok, commit manualmente
git commit -m "Revert <mensagem>"
```

### 3. Para reverts grandes, prefira `git revert -n` (no-commit):

```bash
# Revert múltiplos commits sem auto-commit
git revert -n <commit1> <commit2> <commit3>

# Revise tudo junto
git status
git diff

# Commit manual após revisão
git commit -m "Revert: <descrição>"
```

### 4. Use worktrees para experimentos:

```bash
# Cria worktree para testar revert sem afetar branch principal
git worktree add ../test-revert revert-test

# Na worktree, teste o revert
cd ../test-revert
git revert <commit>

# Se der certo, merge de volta. Se não, delete worktree.
```

---

## 📋 Checklist para Múltiplos Agentes

### Ao trabalhar na mesma branch:

- [ ] **Antes de começar:** `git pull` para garantir que está atualizado
- [ ] **Sempre verifique:** `git status` antes e depois de cada operação
- [ ] **Nunca use:** `git reset --hard` ou `git clean -f` sem confirmação explícita
- [ ] **Preferência:** `git revert --no-commit` ao invés de `git revert`

### Para operações destrutivas:

- [ ] `git reset --soft` (mantém mudanças em staging)
- [ ] `git reset --mixed` (mantém mudanças em working tree)
- [ ] `git reset --hard` (PERIGO: perde tudo não commitado)

### Comunicação:

- [ ] **Avisar outros agentes** antes de operações destrutivas
- [ ] **Documentar** em COMMITS.md ou CHANGELOG.md quando fizer revert
- [ ] **Verificar** arquivos não rastreados com `git status` após revert

---

## 🔧 Recuperação - Quando algo é perdido

### 1. Encontre o commit onde o arquivo existia:

```bash
# Log com histórico de arquivo específico
git log --all --full-history -- <arquivo>

# Ou encontre o commit que deletou
git log --diff-filter=D --summary
```

### 2. Recupere o arquivo:

```bash
# Recupera arquivo de commit específico
git show <commit>:<caminho/arquivo> > <caminho/arquivo>

# Exemplo real:
git show 53ac8d4:src/runtime/delivery/middleware/request_log.py > src/runtime/delivery/middleware/request_log.py
```

### 3. Verifique o reflog se comitou acidentalmente:

```bash
# Mostra histórico de todas as operações
git reflog

# Recupera estado perdido
git reset --hard HEAD@{n}
```

---

## 🎯 Regra de Ouro

> "Em ambientes com múltiplos agentes, **nunca** use `git reset --hard` ou `git revert` sem `--no-commit` primeiro."

**Fluxo seguro:**
```
1. git revert --no-commit <commit>
2. git status (revise o que será alterado)
3. git diff (revise as mudanças)
4. Se OK: git commit
5. Se NÃO OK: git revert --abort
```

---

## 📚 Referências

- [Git Revert Documentation](https://git-scm.com/docs/git-revert)
- [Git Reset Documentation](https://git-scm.com/docs/git-reset)
- [Git Reflog](https://git-scm.com/docs/git-reflog)

---

> "Git é poderoso, mas com grande poder vem grande responsabilidade" – made by Sky 🛡️
