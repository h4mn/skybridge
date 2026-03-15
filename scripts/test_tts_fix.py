#!/usr/bin/env python
# coding: utf-8
"""
Teste simples do comando /tts on|off após correção.
"""

import sys
sys.path.insert(0, "src")

print("Testando comando /tts on...")

from core.sky.chat.textual_ui.voice_commands import execute_tts_toggle_command
import asyncio

async def main():
    result = await execute_tts_toggle_command("on")
    print(f"Comando /tts on executado com sucesso!")
    print(f"Resultado: {len(result)} caracteres")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            print("[OK] Teste passou!")
        else:
            print("[FAIL] Teste falhou!")
            sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
