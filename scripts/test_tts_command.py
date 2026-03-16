#!/usr/bin/env python3
"""
Teste do Comando /tts - Kokoro TTS

Simula o uso do comando /tts do chat Sky.

Uso:
    python scripts/test_tts_command.py
"""

import asyncio
import sys
import os

# Adiciona src ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Configura UTF-8 para saída no Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from core.sky.chat.textual_ui.voice_commands import execute_tts_command


async def main():
    """Testa comando /tts com múltiplas chamadas."""
    print("=" * 60)
    print(" " * 15 + "Teste Comando /tts - Kokoro")
    print("=" * 60)
    print()

    testes = [
        "Olá! Eu sou a Sky.",
        "Esta é minha voz feminina em português.",
        "A primeira chamada carrega o modelo.",
        "As chamadas subsequentes são muito mais rápidas.",
        " Kokoro é incrível!"
    ]

    for i, texto in enumerate(testes, 1):
        print(f"Teste {i}/{len(testes)}: /tts {texto}")
        print("-" * 60)

        resultado = await execute_tts_command(texto)
        print(resultado)
        print()

        # Pequena pausa entre testes
        if i < len(testes):
            await asyncio.sleep(0.5)

    print("=" * 60)
    print("  ✓ Todos os testes concluídos!")
    print("  📊 Note que as chamadas após a 1ª são muito mais rápidas")
    print("=" * 60)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
