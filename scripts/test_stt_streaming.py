#!/usr/bin/env python3
"""
Teste STT Streaming - Transcrição em Tempo Real

Demonstra o modo streaming da transcrição Whisper.

Uso:
    python scripts/test_stt_streaming.py
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
    """Teste de transcrição em modo streaming."""
    print("=" * 60)
    print(" " * 15 + "STT Streaming Test")
    print("=" * 60)
    print()
    print("  Modo: Streaming (transcrições em tempo real)")
    print("  Fale algo por 5 segundos...")
    print()

    try:
        from core.sky.voice import get_voice_service
        from core.sky.voice.stt_service import TranscriptionConfig

        voice = get_voice_service()

        # Transcrições parciais serão exibidas em tempo real
        partial_transcripts = []

        def on_partial(text: str):
            """Callback para transcrições parciais."""
            if text and text.strip():
                partial_transcripts.append(text)
                # Limpa linha e mostra nova transcrição
                print(f"\r  🎤 Stream: {text}", end="", flush=True)

        print("  Gravando...")
        print()

        # Transcreve com modo streaming
        config = TranscriptionConfig(
            language="pt",
            detect_language=False,
            streaming=True  # Modo streaming ativado
        )

        text = await voice.record_and_transcribe(
            duration=5.0,
            language="pt"
        )

        print()  # Nova linha
        print()
        print("=" * 60)
        print("  ✓ Gravação concluída!")
        print("=" * 60)
        print()
        print(f"  Transcrição final: \"{text}\"")
        print(f"  Segmentos parciais: {len(partial_transcripts)}")
        print()

        # Mostra comparação batch vs streaming
        print("  Comparação:")
        print(f"    Batch (final):     \"{text}\"")
        print(f"    Streaming (último): \"{partial_transcripts[-1] if partial_transcripts else ''}\"")
        print()

        print("=" * 60)
        print("  ✓ Teste concluído!")
        print("  🎤 Modo streaming: transcrições aparecem em tempo real")
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
