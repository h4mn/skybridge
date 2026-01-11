# Exemplo: Worktree Validation com Snapshot

## Fluxo Completo de Resolução de Issue com Worktree Validation

```python
# No skill /resolve-issue ou agent orchestator

from skybridge.core.contexts.agents.worktree_validator import safe_worktree_cleanup

def resolve_issue_workflow(issue_number: int):
    """Fluxo completo com validação de worktree."""

    # 1. Criar worktree
    worktree_path = f"../skybridge-fix-{issue_number}"
    git_worktree_add(worktree_path, branch=f"fix/issue-{issue_number}")

    # 2. Capturar snapshot inicial
    validator = WorktreeValidator()
    initial_snapshot = validator.capture_initial_state(worktree_path)

    # 3. Agente trabalha no worktree
    try:
        # ... agente implementa solução ...
        # ... git commit, push, etc ...
        pass

    finally:
        # 4. Validar ANTES de remover (sempre executa, mesmo com erro)
        result = safe_worktree_cleanup(
            worktree_path,
            require_clean=False,  # Permite artefatos de build
            dry_run=True,         # Primeiro valida
        )

        if result["can_remove"]:
            # Worktree limpo, pode remover
            safe_worktree_cleanup(worktree_path, require_clean=False, dry_run=False)
            print(f"✅ Worktree {worktree_path} removido com sucesso")
        else:
            # Worktree sujo, alertar
            print(f"⚠️  {result['message']}")
            print(f"Status: {result['status']}")

            # Opcional: forçar cleanup após confirmação
            if user_confirms_force_cleanup():
                git_worktree_remove_force(worktree_path)
```

## Exemplo de Saída da Validação

### Worktree Limpo (pode remover)
```json
{
  "worktree": "../skybridge-fix-225",
  "can_remove": true,
  "message": "Worktree limpo (com 3 arquivos untracked)",
  "status": {
    "branch": "fix/issue-225",
    "clean": true,
    "staged": 0,
    "unstaged": 0,
    "untracked": 3,
    "conflicts": 0,
    "can_remove": true,
    "files": {
      "staged": [],
      "unstaged": [],
      "conflicts": []
    }
  },
  "dry_run": true,
  "cleanup_message": "DRY RUN: Worktree pode ser removido"
}
```

### Worktree Sujo (NÃO pode remover)
```json
{
  "worktree": "../skybridge-fix-225",
  "can_remove": false,
  "message": "Worktree tem 2 arquivos modificados não commitados",
  "status": {
    "branch": "fix/issue-225",
    "clean": false,
    "staged": 0,
    "unstaged": 2,
    "untracked": 1,
    "conflicts": 0,
    "can_remove": false,
    "files": {
      "staged": [],
      "unstaged": [
        "apps/cli/main.py",
        "apps/api/main.py"
      ],
      "conflicts": []
    }
  },
  "dry_run": true,
  "cleanup_message": "DRY RUN: Worktree NÃO pode ser removido"
}
```

## Integração com Agent Skill

```bash
# No skill /resolve-issue
claude
> /resolve-issue #225

# Skill executa:
1. git worktree add ../skybridge-fix-225 -b fix/225
2. [Trabalho do agente]
3. git commit -m "fix: resolve issue #225"
4. git push
5. gh pr create
6. safe_worktree_cleanup("../skybridge-fix-225", dry_run=True)
   ✅ Validação passou
7. safe_worktree_cleanup("../skybridge-fix-225", dry_run=False)
   ✅ Worktree removido
```

## Vantagens

1. **Segurança**: Nunca remove worktree sujo acidentalmente
2. **Observabilidade**: Snapshot antes/depois para debugging
3. **Flexibilidade**: Modo estrito vs relaxado
4. **Recuperação**: Se falhar, worktree ainda existe para investigação

## Próximos Passos

1. Integrar com Agent Orchestrator
2. Adicionar métricas de cleanup (taxa de sucesso)
3. Dashboard de worktrees ativos
4. Auto-cleanup de worktrees velhos (X dias)

---

> "Validação antes de cleanup é melhor que descoberta depois" – made by Sky 🧹
