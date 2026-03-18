#!/usr/bin/env python3
"""
Teste do Comando /stt - Transcrição de Voz

Demonstra o uso do comando /stt para transcrição de áudio.

Uso:
    python scripts/test_stt_command.py
"""

import sys
import os
import asyncio

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


async def main():
    """Teste do comando /stt."""
    print("=" * 60)
    print(" " * 20 + "Comando /stt - Teste")
    print("=" * 60)
    print()
    print("  Simula: /stt")
    print()

    try:
        from core.sky.chat.textual_ui.voice_commands import execute_stt_command

        # Executa comando /stt
        print("  Iniciando transcrição de 5 segundos...")
        print("  Fale algo agora...")
        print()

        result = await execute_stt_command(duration=5.0)

        print()
        print("=" * 60)
        print(result)
        print("=" * 60)

        return 0

    except ImportError as e:
        print()
        print("  ❌ Erro de importação:")
        print(f"     {e}")
        print()
        print("  Instale as dependências:")
        print("     python scripts/install_voice_deps.py")
        print()
        return 1

    except Exception as e:
        print()
        print(f"  ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
