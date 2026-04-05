#!/bin/bash
# Ralph Loop Session Capture Hook
# Captura session_id quando usuário executa /ralph-loop:ralph-loop
# Salva em arquivo temporário para setup-ralph-loop.sh ler

set -euo pipefail

# Ler stdin (JSON enviado pelo Claude Code)
INPUT=$(cat)

# Extrair session_id e user_prompt
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
USER_PROMPT=$(echo "$INPUT" | jq -r '.user_prompt // empty')

# Debug log
CACHE_DIR="${CLAUDE_PROJECT_DIR}/.claude/cache"
mkdir -p "$CACHE_DIR"

LOG_FILE="$CACHE_DIR/ralph-hook-debug.log"
echo "=== UserPromptSubmit Hook ===" >> "$LOG_FILE"
echo "SESSION_ID: $SESSION_ID" >> "$LOG_FILE"
echo "USER_PROMPT: $USER_PROMPT" >> "$LOG_FILE"

# Verificar se é um comando /ralph-loop (sintaxe completa ou curta)
if echo "$USER_PROMPT" | grep -qE "(ralph-loop:ralph-loop|^/ralph-loop)"; then
  # Salvar session_id para o setup script ler
  echo "$SESSION_ID" > "$CACHE_DIR/ralph-session-id.txt"

  echo "[Ralph Hook] Detectado /ralph-loop, session_id salvo: $SESSION_ID" >&2
  echo "ARQUIVO: $CACHE_DIR/ralph-session-id.txt" >&2
fi

# Sempre retornar sucesso e continuar
exit 0
