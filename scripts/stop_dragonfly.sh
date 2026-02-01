#!/bin/bash
# scripts/stop_dragonfly.sh
# Stop script for DragonflyDB

PID_FILE="./data/dragonfly/dragonfly.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Parando DragonflyDB (PID: $PID)..."
    kill $PID 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "✅ DragonflyDB parado"
else
    echo "DragonflyDB não está rodando"
fi
