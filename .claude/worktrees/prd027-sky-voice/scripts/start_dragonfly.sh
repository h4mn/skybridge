#!/bin/bash
# scripts/start_dragonfly.sh
# Startup script for DragonflyDB in CLI mode

set -e

# Configurações
DRAGONFLY_DIR="./data/dragonfly"
DRAGONFLY_PORT=6379
LOG_FILE="./logs/dragonfly.log"
PID_FILE="./data/dragonfly/dragonfly.pid"

# Criar diretórios
mkdir -p "$DRAGONFLY_DIR"
mkdir -p "./logs"

# Verificar se já está rodando
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "DragonflyDB já está rodando (PID: $PID)"
        exit 0
    fi
fi

# Iniciar DragonflyDB em background
echo "Iniciando DragonflyDB..."
nohup dragonfly --cli \
  --log-level debug \
  --dir "$DRAGONFLY_DIR" \
  --port "$DRAGONFLY_PORT" \
  >> "$LOG_FILE" 2>&1 &

# Salvar PID
echo $! > "$PID_FILE"

# Aguardar inicialização
sleep 2

# Verificar se iniciou
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "✅ DragonflyDB iniciado com sucesso"
    echo "   Logs: $LOG_FILE"
    echo "   PID: $(cat $PID_FILE)"
    echo "   Porta: $DRAGONFLY_PORT"
else
    echo "❌ Falha ao iniciar DragonflyDB"
    rm -f "$PID_FILE"
    exit 1
fi
