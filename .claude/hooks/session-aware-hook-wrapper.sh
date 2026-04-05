#!/bin/bash
# Session-Aware Hook Wrapper
# Executa comando apenas se o session_id corresponder ao esperado
#
# Uso:
#   bash session-aware-hook-wrapper.sh <EXPECTED_SESSION_ID> <COMMAND> [ARGS...]
#
# Exemplo em hook:
#   {
#     "type": "command",
#     "command": "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/session-aware-hook-wrapper.sh 135c02a7-c03c-4420-8200-c2ed168a0dbg bash ${CLAUDE_PROJECT_DIR}/script.sh",
#     "timeout": 30
#   }

set -euo pipefail

EXPECTED_SESSION_ID="$1"
shift
COMMAND=("$@")

# Ler hook input do stdin
HOOK_INPUT=$(cat)

# Extrair session_id do HOOK_INPUT
CURRENT_SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // ""')

# Verificar se session_id corresponde
if [[ "$CURRENT_SESSION_ID" != "$EXPECTED_SESSION_ID" ]]; then
  # Session_id não corresponde - não executar comando
  exit 0
fi

# Session_id corresponde - executar comando e passar HOOK_INPUT via stdin
echo "$HOOK_INPUT" | "${COMMAND[@]}"
exit $?
