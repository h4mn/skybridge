# Relatório: Infraestrutura Claude Code CLI

**Data:** 2026-01-10
**Autor:** Sky
**Status:** Pesquisa Completa

---

## 1. Objetivo

Documentar todas as flags, permissões e configurações do Claude Code CLI necessárias para o spawnciamento de agentes no contexto Skybridge.

## 2. Flags CLI Relevantes

### 2.1) Flags Principais para Skybridge

| Flag | Uso | Obrigatório? | Valor Recomendado |
|------|-----|--------------|-------------------|
| `--print` | Modo não-interativo (headless) | ✅ Sim | Sempre |
| `-p` | Alias para `--print` | ✅ Sim | Sempre |
| `--cwd` | Diretório de trabalho (worktree) | ✅ Sim | `{worktree_path}` |
| `--system-prompt` | Contexto da tarefa | ✅ Sim | String com contexto |
| `--output-format` | Formato de saída | ✅ Sim | `json` |
| `--permission-mode` | Nível de permissão | ⚠️ Contexto | `bypass` (worktrees de confiança) |

### 2.2) Flags Úteis (Opcionais)

| Flag | Uso | Quando Usar |
|------|-----|-------------|
| `--model` | Override modelo | Para tasks específicas |
| `--agent` | Override agente | Para agentes customizados |
| `--allowedTools` | Restringir ferramentas | Para limitar ações |
| `--disallowedTools` | Bloquear ferramentas | Para segurança adicional |
| `--timeout` | Timeout da execução | Para prevenir hangs |
| `--max-budget-usd` | Limite de custo | Para controle financeiro |
| `--verbose` | Debug logging | Para desenvolvimento |

### 2.3) Flags NÃO Utilizados

| Flag | Por que não usar |
|------|------------------|
| `--dangerously-skip-permissions` | Worktrees já são isolados; usar `permission-mode: bypass` |
| `--continue` / `--resume` | Cada execução é única (não retomamos sessões) |
| `--teleport` | Integração web-cli (não necessário) |

## 3. Sistemas de Permissão

### 3.1) Níveis de `permission-mode`

| Nível | Descrição | Uso Skybridge |
|-------|-----------|----------------|
| `default` | Pede permissão para cada ação | ❌ Muito verboso |
| `acceptEdits` | Auto-aceita edits, permissão para resto | ❌ Ainda pede permissões |
| `bypass` | Auto-aceita TUDO | ✅ **Recomendado para worktrees** |

**Justificativa para `bypass`:**
Worktrees são **sandbox natural** - o agente só pode afetar o worktree isolado, não o repositório principal.

### 3.2) Permissões Granulares (se necessário)

```bash
# Em settings.json ou via flag
{
  "permissions": {
    "allowedTools": [
      "Edit",           # Criar/modificar arquivos
      "Bash(git:*)",    # Comandos git (apenas git)
      "Bash(git commit:*)",  # Commits específicos
      "Read",           # Leitura de arquivos
      "Search"          # Busca no código
    ],
    "disallowedTools": [
      "Bash(rm:*)",    # ❌ DELETES perigosos
      "Bash(sudo:*)",  # ❌ Privégios elevados
      "Bash(npm:publish)",  # ❌ Operações destrutivas
    ]
  }
}
```

### 3.3) Configuração Recomendada para Worktrees

```json
{
  "permissionMode": "bypass",
  "allowedTools": [
    "Edit",
    "Read",
    "Search",
    "Bash(git:*)"
  ],
  "disallowedTools": [
    "Bash(rm:-rf:*)",
    "Bash(sudo:*)",
    "Bash(dd:*)"
  ]
}
```

## 4. Timeout e Limits

### 4.1) Environment Variables Relevantes

| Variável | Default | Recomendação Skybridge |
|----------|---------|------------------------|
| `BASH_DEFAULT_TIMEOUT_MS` | 60000 (60s) | 300000 (5min) |
| `BASH_MAX_TIMEOUT_MS` | 600000 (10min) | 600000 (10min) |
| `CLAUDE_CODE_EXIT_AFTER_STOP_DELAY_MS` | - | 1000 (1s) para SDK |

### 4.2) Timeout por Tipo de Tarefa

| Tarefa | Timeout | Justificativa |
|--------|---------|----------------|
| Hello World | 60s | Simples |
| Bug fix simples | 300s (5min) | Análise + implementação |
| Bug fix complexo | 600s (10min) | Pode demandar pesquisa |
| Refatoração | 900s (15min) | Múltiplos arquivos |

## 5. Output Format

### 5.1) Formatos Disponíveis

| Formato | Uso | Skybridge |
|---------|-----|-----------|
| (default) | Terminal interativo | ❌ |
| `json` | JSON estruturado | ✅ **Padrão** |
| `stream-json` | Streaming JSON | 🔮 Futuro |

### 5.2) Estrutura JSON Esperada

```json
{
  "success": true,
  "changes_made": true,
  "files_created": ["path/to/file1.py"],
  "files_modified": ["path/to/file2.py"],
  "commit_hash": "abc123def456",
  "pr_url": "https://github.com/org/repo/pull/123",
  "message": "Issue resolved: fixed version alignment",
  "thinkings": [
    {
      "step": 1,
      "thought": "Analisando issue...",
      "timestamp": "2026-01-10T10:30:00Z"
    }
  ]
}
```

## 6. Comando de Spawn Recomendado

```bash
claude \
  --print \
  --cwd "${WORKTREE_PATH}" \
  --system-prompt "${SYSTEM_PROMPT}" \
  --output-format json \
  --permission-mode bypass \
  --allowedTools "Edit,Read,Search,Bash(git:*)" \
  --disallowedTools "Bash(rm:-rf:*),Bash(sudo:*)" \
  --timeout 600 \
  "${PROMPT_PRINCIPAL}"
```

### 6.1) Variáveis de Substituição

| Variável | Conteúdo |
|----------|----------|
| `${WORKTREE_PATH}` | `/tmp/worktrees/skybridge-github-225-abc123` |
| `${SYSTEM_PROMPT}` | Conteúdo completo do system prompt (ver SPEC008) |
| `${PROMPT_PRINCIPAL}` | "Resolve issue #225: Fix version alignment" |

## 7. Exemplos Práticos

### 7.1) Exemplo Mínimo (Hello World)

```bash
claude -p \
  --cwd /tmp/worktree \
  --system-prompt "Create hello world script" \
  --output-format json \
  --permission-mode bypass \
  "Create hello_world.py"
```

### 7.2) Exemplo Completo (Resolução de Issue)

```bash
SYSTEM_PROMPT=$(cat <<'EOF'
You are in ISOLATED GIT WORKTREE for issue #225.
Worktree: /tmp/skybridge-github-225-abc123
Branch: webhook/github/issue/225/abc123

Issue:
Title: Fix version alignment between CLI and API
Description: The versions are not centralized...

CRITICAL RULES:
1. All work in this worktree
2. Follow existing patterns
3. Test before committing
4. Create proper commit messages
5. Push branch
6. Create PR with gh pr create

Output MUST be JSON with success, changes_made, files_created, etc.
EOF
)

claude --print \
  --cwd "/tmp/skybridge-github-225-abc123" \
  --system-prompt "${SYSTEM_PROMPT}" \
  --output-format json \
  --permission-mode bypass \
  --timeout 600 \
  "Fix the version alignment issue described in the GitHub issue"
```

## 8. Validações Pós-Execução

### 8.1) Verificações Obrigatórias

| Verificação | Como | Falha se |
|-------------|-----|-----------|
| Arquivos criados no worktree | `ls -la ${WORKTREE_PATH}` | ❌ |
| Nenhum arquivo fora do worktree | `git status --porcelain` (main) | ❌ |
| Commit hash válido | `git rev-parse HEAD` (worktree) | ❌ (se declarado) |
| PR URL válida | `gh pr view ${URL}` | ❌ (se declarada) |

### 8.2) Validação via Snapshot (SPEC007)

```python
# Snapshot antes
before = git_extractor.capture(worktree_path)

# Executa agente
result = spawner.spawn_agent(job)

# Snapshot depois
after = git_extractor.capture(worktree_path)

# Diff
diff = snapshot_diff(before, after)

# Valida
assert diff.files_created == result.files_created
assert diff.files_modified == result.files_modified
```

## 9. Segurança

### 9.1) Sandbox Natural de Worktree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Repositório Principal                                                  [PROTEGIDO]           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Worktree Isolado                                              [TRABALHO] │   │
│  │                                                                     │   │
│  │  Agente operando com --permission-mode bypass                      │   │
│  │  ✓ Pode criar arquivos                                            │   │
│  │  ✓ Pode modificar arquivos                                         │   │
│  │  ✓ Pode commitar                                                 │   │
│  │  ✗ NÃO pode afetar repositório principal                         │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2) Proteções Adicionais

| Proteção | Implementação |
|----------|---------------|
| Isolamento de worktree | Git worktree nativo |
| Validação pré-cleanup | GitExtractor.validate_worktree() |
| Timeout máximo | `--timeout 600` (10min) |
| Comandos bloqueados | `--disallowedTools "Bash(rm:-rf:*)"` |
| Snapshot antes/depois | Sistema de observabilidade |

## 10. Conclusão

O Claude Code CLI oferece **todas as flags necessárias** para spawnciamento seguro de agentes em worktrees isolados.

**Comando padrão para Skybridge:**
```bash
claude --print \
  --cwd "${WORKTREE_PATH}" \
  --system-prompt "${SYSTEM_PROMPT}" \
  --output-format json \
  --permission-mode bypass \
  --timeout 600 \
  "${PROMPT_PRINCIPAL}"
```

---

## Fontes

- [Claude Code Changelog](https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Official Documentation](https://code.claude.com/docs/en/overview)
- [SPEC008 — AI Agent Interface](../spec/SPEC008-AI-Agent-Interface.md)

> "Conheça bem suas ferramentas antes de confiá-las com trabalho autônomo." – made by Sky 🔧
