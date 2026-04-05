#!/bin/bash
# Teste do mecanismo de retry do Ralph Loop - v2

echo "=== TESTE DE RETRY (corrigido) ==="
echo ""

CACHE_DIR="B:\_repositorios\skybridge\.claude\cache"
CACHE_FILE="$CACHE_DIR/ralph-session-id.txt"
SESSION_ID="test-session-123"

# Limpar
rm -f "$CACHE_FILE"

echo "1. Teste: Arquivo aparece após 0.5s"
echo "   [Iniciando setup com retry...]"

# Simular setup script
(
  cd "B:\_repositorios\skybridge"
  SESSION_ID=""

  for attempt in {1..10}; do
    if [[ -f ".claude/cache/ralph-session-id.txt" ]]; then
      SESSION_ID=$(cat ".claude/cache/ralph-session-id.txt")
      rm -f ".claude/cache/ralph-session-id.txt"
      echo "   ✅ Arquivo encontrado na tentativa $attempt"
      echo "   ✅ Session ID: $SESSION_ID"
      exit 0
    fi
    sleep 0.2
  done

  # Fallback
  if [[ -z "$SESSION_ID" ]]; then
    SESSION_ID=$(python -c "import uuid; print(uuid.uuid4())")
    echo "   ⚠️  Arquivo não encontrado, usando fallback UUID: $SESSION_ID"
  fi
) &

SETUP_PID=$!

# Simular hook escrevendo após 0.5s
sleep 0.5
mkdir -p "$CACHE_DIR"
echo "$SESSION_ID" > "$CACHE_FILE"
echo "   [Hook] Escreveu session_id: $SESSION_ID"

# Esperar
wait $SETUP_PID

echo ""
echo "2. Teste: Fallback UUID quando arquivo não existe"
echo ""

rm -f "$CACHE_FILE"

(
  cd "B:\_repositorios\skybridge"
  SESSION_ID=""

  for attempt in {1..10}; do
    if [[ -f ".claude/cache/ralph-session-id.txt" ]]; then
      SESSION_ID=$(cat ".claude/cache/ralph-session-id.txt")
      break
    fi
    sleep 0.2
  done

  if [[ -z "$SESSION_ID" ]]; then
    SESSION_ID=$(python -c "import uuid; print(uuid.uuid4())")
    echo "   ✅ Fallback UUID gerado: $SESSION_ID"
  fi
) &

wait $!

echo ""
echo "=== FIM DO TESTE ==="
