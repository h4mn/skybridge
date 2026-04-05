#!/usr/bin/env python3
"""
Debug hook payloads - Log o que cada evento passa para o stdin
"""
import json
import sys
import os
from datetime import datetime

# Forçar UTF-8
if sys.platform == "win32":
    import io
    if hasattr(sys.stdin, 'buffer'):
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Arquivo de log
LOG_FILE = os.path.expanduser("~/hook_debug.log")

# Lê stdin
try:
    input_data = sys.stdin.read()
    if not input_data:
        input_data = "{}"
    payload = json.loads(input_data)
except:
    payload = {"error": "No stdin data"}

# Prepara log entry
log_entry = {
    "timestamp": datetime.now().isoformat(),
    "event": os.environ.get("CLAUDE_HOOK_EVENT", "unknown"),
    "stdin": input_data[:500] if input_data else "",  # Primeiros 500 chars
    "env_keys": list(k for k in os.environ.keys() if k.startswith("CLAUDE_"))
}

# Salva no log (append)
log_path = os.path.expanduser(LOG_FILE)
with open(log_path, "a", encoding="utf-8") as f:
    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

# Output para debug (visible no spinner status)
print(json.dumps({
    "systemMessage": f"[DEBUG] Payload loggado em {LOG_FILE}",
    "suppressOutput": True
}))
