#!/usr/bin/env python3
"""
Debug script para capturar payload do PostToolUse
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# UTF-8
if sys.platform == "win32":
    import io
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DEBUG_LOG = Path.home() / "posttooluse_debug.log"

# Lê stdin
try:
    input_data = sys.stdin.read()
except:
    input_data = '{}'

# Parse JSON
try:
    payload = json.loads(input_data)
except:
    payload = {"raw": input_data}

# Log completo
with open(DEBUG_LOG, "a", encoding="utf-8") as f:
    f.write(f"\n{'='*60}\n")
    f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
    f.write(f"RAW INPUT:\n{input_data[:1000]}...\n")
    f.write(f"PARSED PAYLOAD:\n{json.dumps(payload, indent=2)}\n")
    f.write(f"{'='*60}\n\n")

print(json.dumps({"status": "debug_logged", "log_file": str(DEBUG_LOG)}))
