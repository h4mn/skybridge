#!/bin/bash
# Teste do mecanismo de retry do Ralph Loop

echo "=== TESTE DE RETRY DO RALPH LOOP HOOK ==="
echo ""

CACHE_DIR="B:\_repositorios\skybridge\.claude\cache"
CACHE_FILE="$CACHE_DIR/ralph-session-id.txt"
SESSION_ID="72dc7f6e-e0d8-4e32-8e6a-a88414294e5e"
SESSION_ID_READ=""

# Limpar arquivo anterior
rm -f "$CACHE_FILE"

echo "1. Teste: Arquivo aparece após 0.5s (dentro do prazo de retry)"
echo ""

# Simular setup script com retry em background
(
  cd "B:\_repositorios\skybridge"
  for attempt in {1..10}; do
    if [[ -f ".claude/cache/ralph-session-id.txt" ]]; then
      SESSION_ID_READ=$(cat ".claude/cache/ralph-session-id.txt")
      echo "   ✅ Arquivo encontrado na tentativa $attempt"
      break
    fi
    sleep 0.2
  done
) &

PID=$!

# Simular hook escrevendo após 0.5s
sleep 0.5
mkdir -p "$CACHE_DIR"
echo "$SESSION_ID" > "$CACHE_FILE"
echo "   [Hook] Escreveu session_id após 0.5s"

# Esperar setup terminar
wait $PID

if [[ "$SESSION_ID_READ" == "$SESSION_ID" ]]; then
  echo "   ✅ SESSION_ID correto: $SESSION_ID_READ"
else
  echo "   ❌ SESSION_ID incorreto ou vazio: '$SESSION_ID_READ'"
fi

echo ""
echo "2. Teste: Arquivo NUNCA aparece (fallback para UUID)"
echo ""

# Limpar
rm -f "$CACHE_FILE"
SESSION_ID_READ=""

# Simular setup script com retry + fallback
(
  cd "B:\_repositorios\skybridge"
  for attempt in {1..10}; do
    if [[ -f ".claude/cache/ralph-session-id.txt" ]]; then
      SESSION_ID_READ=$(cat ".claude/cache/ralph-session-id.txt")
      break
    fi
    sleep 0.2
  done

  # Fallback para UUID
  if [[ -z "$SESSION_ID_READ" ]]; then
    SESSION_ID_READ=$(python -c "import uuid; print(uuid.uuid4())")
  fi
) &

PID=$!
wait $PID

# Verificar se é um UUID válido
if [[ "$SESSION_ID_READ" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
  echo "   ✅ Fallback UUID gerado: $SESSION_ID_READ"
else
  echo "   ❌ Fallback falhou: '$SESSION_ID_READ'"
fi

echo ""
echo "=== FIM DO TESTE ==="
