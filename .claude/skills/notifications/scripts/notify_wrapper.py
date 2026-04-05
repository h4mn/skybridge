#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper para notificações Discord
Passa dados da sessão Claude Code para o notify_discord.py

Este script é chamado pelo hook e:
1. Lê a notificação via stdin
2. Adiciona dados da sessão (versão, modelo, contexto, cwd)
3. Passa tudo para notify_discord.py
"""
import json
import sys
import os
import subprocess
from pathlib import Path

def get_session_data():
    """
    Retorna dados da sessão no formato da statusline.
    Tenta obter de várias fontes (cache, env, valores padrão)
    """
    # Tenta ler do cache (se existir)
    cache_file = Path.home() / ".claude" / "session_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass

    # Fallback: valores padrão
    return {
        "version": os.environ.get("CLAUDE_CODE_VERSION", "2.1.90"),
        "model": {
            "display_name": os.environ.get("CLAUDE_MODEL", "glm-5")
        },
        "context_window": {
            "used_percentage": int(os.environ.get("CLAUDE_CONTEXT_PCT", "0"))
        },
        "cwd": os.environ.get("CLAUDE_CWD", os.getcwd())
    }

def main():
    # Lê notificação do stdin
    try:
        input_data = sys.stdin.read()
        if not input_data:
            input_data = '{"message": "Notificação"}'
        notification = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"ERRO JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Adiciona dados da sessão
    session_data = get_session_data()
    notification["session_data"] = session_data

    # Debug: mostra os dados da sessão (se DEBUG=1)
    if os.environ.get("DEBUG") == "1":
        print(f"[DEBUG] Session data: {json.dumps(session_data, indent=2)}", file=sys.stderr)

    # Caminho para notify_discord.py
    script_dir = Path(__file__).parent
    notify_script = script_dir / "notify_discord.py"

    # Executa notify_discord.py com os dados enriquecidos
    result = subprocess.run(
        [sys.executable, str(notify_script)],
        input=json.dumps(notification),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ
    )

    # Output do resultado
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
