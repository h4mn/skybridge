# Hook Session Isolation - Guia de Solução

## Problema

Hooks no Claude Code são configurados por **projeto**, não por **sessão**. Isso causa "vazamento" de hooks entre sessões do mesmo projeto.

### Exemplo do Problema

```
Sessão A (discord) registra stop-hook
    ↓
Hook registrado globalmente para o projeto
    ↓
Sessão B (autotrack) tenta fechar
    ↓
Hook da sessão A executa na sessão B (ERRADO!)
```

## Solução: Session-Aware Hook Wrapper

Use o wrapper `.claude/hooks/session-aware-hook-wrapper.sh` para garantir que hooks executem apenas na sessão correta.

### Como Usar

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/session-aware-hook-wrapper.sh <SESSION_ID> <COMANDO>",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Exemplo Prático

```bash
# Hook que deve executar apenas na sessão "discord"
SESSION_ID="135c02a7-c03c-4420-8200-c2ed168a0bdb"

# Sem wrapper (ERRADO - executa em todas as sessões)
command: "bash ${CLAUDE_PROJECT_DIR}/script.sh"

# Com wrapper (CORRETO - executa apenas na sessão certa)
command: "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/session-aware-hook-wrapper.sh ${SESSION_ID} bash ${CLAUDE_PROJECT_DIR}/script.sh"
```

## Como Obter o Session_ID

### Método 1: Do Hook Input

```bash
# Em qualquer hook, ler stdin e extrair session_id
HOOK_INPUT=$(cat)
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id')
```

### Método 2: Do Cache do Ralph Loop

```bash
# O Ralph Loop mantém o session_id atual em cache
CACHE_FILE="${CLAUDE_PROJECT_DIR}/.claude/cache/ralph-session-id.txt"
SESSION_ID=$(cat "$CACHE_FILE")
```

### Método 3: Variável de Ambiente

```bash
# Em alguns casos, o session_id está disponível como variável
SESSION_ID="${CLAUDE_CODE_SESSION_ID:-}"
```

## Padrões de Hook com Isolamento

### Padrão 1: Stop Hook Específico de Sessão

```bash
# Crie um script que recebe o session_id como argumento
# .claude/hooks/my-session-hook.sh

EXPECTED_SESSION_ID="$1"
HOOK_INPUT=$(cat)
CURRENT_SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // ""')

if [[ "$CURRENT_SESSION_ID" == "$EXPECTED_SESSION_ID" ]]; then
  # Executar lógica do hook
  echo "Hook executando na sessão correta"
else
  # Sessão errada - sair sem fazer nada
  exit 0
fi
```

### Padrão 2: Hook com Multiplas Sessões

```bash
# Hook que aceita múltiplos session_ids válidos
ALLOWED_SESSIONS=(
  "135c02a7-c03c-4420-8200-c2ed168a0bdb"
  "7d19f4e4-19c1-4c3a-9d71-96482125d13b"
)

HOOK_INPUT=$(cat)
CURRENT_SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // ""')

for allowed in "${ALLOWED_SESSIONS[@]}"; do
  if [[ "$CURRENT_SESSION_ID" == "$allowed" ]]; then
    # Session_id permitido - executar
    exec bash "$@"
  fi
done

# Session_id não permitido - sair
exit 0
```

## Debugging

### Verificar quais hooks estão ativos

```bash
# Listar hooks do projeto
cat .claude/hooks/hooks.json | jq .

# Verificar hooks globais
cat ~/.claude/settings.json | jq '.hooks'
```

### Verificar session_id atual

```bash
# Do cache do Ralph Loop
cat .claude/cache/ralph-session-id.txt

# Do log de debug
tail -1 .claude/cache/ralph-hook-debug.log | grep SESSION_ID
```

### Simular hook com session_id específico

```bash
# Criar input de hook simulado
HOOK_INPUT=$(cat <<EOF
{
  "session_id": "135c02a7-c03c-4420-8200-c2ed168a0bdb",
  "cwd": "$(pwd)",
  "transcript_path": "/path/to/transcript"
}
EOF
)

# Testar wrapper
echo "$HOOK_INPUT" | bash .claude/hooks/session-aware-hook-wrapper.sh "135c02a7-c03c-4420-8200-c2ed168a0bdb" echo "Teste"
```

## Casos de Uso

### Caso 1: Ralph Loop com Plano Específico

```bash
# Ralph Loop está executando um plano na sessão discord
# O plano tem um stop-hook que deve executar apenas nessa sessão

# No hooks.json ou configuração dinâmica:
{
  "command": "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/session-aware-hook-wrapper.sh 135c02a7-c03c-4420-8200-c2ed168a0bdb bash ${CLAUDE_PROJECT_DIR}/scripts/pyropaws-plan.sh",
  "timeout": 60
}
```

### Caso 2: Hook de Notificação

```bash
# Notificar apenas quando a sessão específica fechar
{
  "command": "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/session-aware-hook-wrapper.sh ${SESSION_ID} bash ${CLAUDE_PROJECT_DIR}/scripts/notify-session-end.sh",
  "timeout": 10
}
```

## Referências

- Ralph Loop Multi-Sessão: Implementação completa em `openspec/changes/ralph-loop-multi-sessao/`
- Hook API: Documentação interna do Claude Code
- Session Capture: `.claude/hooks/ralph-session-capture.sh`

---

> "Hooks devem respeitar os limites das sessões" – made by Sky 🚀
