#!/bin/bash
# Teste do Ralph Loop Hook

echo "=== TESTE DO RALPH LOOP HOOK ==="
echo ""

# 1. Simular o UserPromptSubmit hook
echo "1. Simulando UserPromptSubmit hook..."
SESSION_ID="72dc7f6e-e0d8-4e32-8e6a-a88414294e5e"
CACHE_DIR="B:\_repositorios\skybridge\.claude\cache"
mkdir -p "$CACHE_DIR"

echo "   SESSION_ID: $SESSION_ID"
echo "   Escrevendo em: $CACHE_DIR/ralph-session-id.txt"
echo "$SESSION_ID" > "$CACHE_DIR/ralph-session-id.txt"

# 2. Simular o setup script lendo
echo ""
echo "2. Simulando setup-ralph-loop.sh..."
CACHE_SESSION_FILE=".claude/cache/ralph-session-id.txt"

if [[ -f "$CACHE_SESSION_FILE" ]]; then
  READ_SESSION_ID=$(cat "$CACHE_SESSION_FILE")
  echo "   ✅ SUCESSO! Session ID lido: $READ_SESSION_ID"

  if [[ "$READ_SESSION_ID" == "$SESSION_ID" ]]; then
    echo "   ✅ SESSION_ID CORRESPONDE!"
  else
    echo "   ❌ SESSION_ID NÃO CORRESPONDE!"
  fi
else
  echo "   ❌ ARQUIVO NÃO ENCONTRADO: $CACHE_SESSION_FILE"
fi

# 3. Verificar arquivo de debug
echo ""
echo "3. Verificando arquivo de debug..."
if [[ -f "$CACHE_DIR/ralph-hook-debug.log" ]]; then
  echo "   📄 Log existe. Últimas linhas:"
  tail -5 "$CACHE_DIR/ralph-hook-debug.log" | sed 's/^/      /'
else
  echo "   ❌ Log não encontrado em: $CACHE_DIR/ralph-hook-debug.log"
fi

echo ""
echo "=== FIM DO TESTE ==="
