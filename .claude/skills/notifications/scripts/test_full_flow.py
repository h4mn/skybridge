#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# Forçar UTF-8
if sys.platform == "win32":
    import io
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Simula payload do hook
payload = {
    "session_id": "test-session",
    "transcript_path": "C:/Users/hadst/.claude/projects/B---repositorios-skybridge/13087ebc-61d9-45a2-8fa1-3b8668ba2157.jsonl",
    "hook_event_name": "TaskCompleted",
    "task_id": "99",
    "task_subject": "Teste completo do sistema",
    "task_description": "Testando logging completo com Agent SDK"
}

print(f"[DEBUG] Payload: {json.dumps(payload, indent=2)}", file=sys.stderr)

# Importa função de resumo
sys.path.insert(0, str(Path(__file__).parent))
from notify_discord import summarize_text

print("[DEBUG] Chamando summarize_text...", file=sys.stderr)

try:
    resultado = summarize_text("TESTE LONGO DO SCRIPT para verificar se o resumo funciona corretamente e captura todos os logs.", payload["transcript_path"])
    print(f"[DEBUG] Resultado: {resultado}", file=sys.stderr)
except Exception as e:
    print(f"[DEBUG] ERRO: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

print(f"[DEBUG] Final: {resultado}")
