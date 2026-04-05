#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste completo do handshake MCP para capturar erro exato."""
import os
import sys
import io
import json
from pathlib import Path

# UTF-8
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Handshake MCP completo
handshake = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "claude-code",
            "version": "1.0.0"
        }
    },
    "id": 1
}

import subprocess
import time

sys.stderr.write(f"=== MCP HANDSHAKE TEST ===\n")
sys.stderr.write(f"Executando: python run_discord_mcp.py\n")
sys.stderr.write(f"Working dir: {os.getcwd()}\n")
sys.stderr.write(f"Token set: {bool(os.environ.get('DISCORD_BOT_TOKEN'))}\n")
sys.stderr.write(f"=== INICIANDO ===\n")
sys.stderr.flush()

# Executa o MCP server
proc = subprocess.Popen(
    [sys.executable, "run_discord_mcp.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=0
)

# Envia handshake
sys.stderr.write(f"=== ENVIANDO HANDSHAKE ===\n")
sys.stderr.flush()

try:
    proc.stdin.write(json.dumps(handshake) + "\n")
    proc.stdin.flush()
except Exception as e:
    sys.stderr.write(f"ERRO ao escrever stdin: {e}\n")
    sys.stderr.flush()

# Espera resposta ou timeout
sys.stderr.write(f"=== AGUARDANDO RESPOSTA (timeout 5s) ===\n")
sys.stderr.flush()

try:
    stdout, stderr = proc.communicate(timeout=5)
    sys.stderr.write(f"=== STDOUT ===\n{stdout}\n")
    sys.stderr.write(f"=== STDERR ===\n{stderr}\n")
    sys.stderr.write(f"=== EXIT CODE: {proc.returncode} ===\n")
except subprocess.TimeoutExpired:
    proc.kill()
    stdout, stderr = proc.communicate()
    sys.stderr.write(f"=== TIMEOUT ===\n")
    sys.stderr.write(f"=== STDOUT ===\n{stdout}\n")
    sys.stderr.write(f"=== STDERR ===\n{stderr}\n")

sys.stderr.flush()
