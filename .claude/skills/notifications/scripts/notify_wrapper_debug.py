#!/usr/bin/env python3
"""
Wrapper para debug do notify_discord - captura stderr e loga erros
"""
import json
import sys
import os
import subprocess
from pathlib import Path

# Forçar UTF-8
if sys.platform == "win32":
    import io
    if hasattr(sys.stdin, 'buffer'):
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DEBUG_LOG = Path.home() / "notify_wrapper_debug.log"

# Lê stdin
try:
    input_data = sys.stdin.read()
    if not input_data:
        input_data = '{}'
except:
    input_data = '{}'

# Log do input
with open(DEBUG_LOG, "a", encoding="utf-8") as f:
    f.write(f"[INPUT] {input_data[:200]}...\n")

# Executa notify_discord.py
script_path = Path(__file__).parent / "notify_discord.py"
result = subprocess.run(
    [sys.executable, str(script_path)],
    input=input_data,
    capture_output=True,
    text=True,
    encoding="utf-8",
    timeout=20
)

# Log do resultado
with open(DEBUG_LOG, "a", encoding="utf-8") as f:
    f.write(f"[STDOUT] {result.stdout}\n")
    f.write(f"[STDERR] {result.stderr}\n")
    f.write(f"[RETURN] {result.returncode}\n")

# Output
sys.stdout.write(result.stdout)
if result.stderr:
    sys.stderr.write(result.stderr)

sys.exit(result.returncode)
