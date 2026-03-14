#!/usr/bin/env python3
"""
Teste VoiceService Singleton

Demonstra o uso do VoiceService singleton com lazy load.

Uso:
    python scripts/test_voice_service.py
"""

import asyncio
import sys
import os
import time

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
    """Testa VoiceService singleton."""
    print("=" * 60)
    print(" " * 15 + "VoiceService Singleton Test")
    print("=" * 60)
    print()

    from core.sky.voice import get_voice_service, VoiceStats

    voice = get_voice_service()

    print("  Estado inicial:")
    print(f"    TTS pronto: {voice.is_tts_ready}")
    print(f"    STT pronto: {voice.is_stt_ready}")
    print()

    # Teste 1: Primeira chamada TTS (cold start)
    print("  1ª chamada TTS (cold start):")
    start = time.perf_counter()
    await voice.speak("Olá! Esta é a primeira vez que eu falo.")
    elapsed = time.perf_counter() - start
    print(f"    Tempo: {elapsed*1000:.1f}ms")
    print()

    # Verifica estado
    print("  Estado após 1ª chamada:")
    print(f"    TTS pronto: {voice.is_tts_ready}")
    print(f"    STT pronto: {voice.is_stt_ready}")
    stats = voice.stats
    print(f"    Chamadas TTS: {stats.tts_calls}")
    print(f"    Tempo load TTS: {stats.tts_load_time_ms:.1f}ms")
    print()

    # Teste 2: Segunda chamada TTS (warm start)
    print("  2ª chamada TTS (warm start):")
    start = time.perf_counter()
    await voice.speak("Agora o modelo já está carregado na memória.")
    elapsed = time.perf_counter() - start
    print(f"    Tempo: {elapsed*1000:.1f}ms")
    print()

    # Teste 3: Terceira chamada (ainda warm)
    print("  3ª chamada TTS (warm):")
    start = time.perf_counter()
    await voice.speak("As chamadas seguintes são muito mais rápidas!")
    elapsed = time.perf_counter() - start
    print(f"    Tempo: {elapsed*1000:.1f}ms")
    print()

    # Teste 4: STT
    print("  Teste STT:")
    print("    Gravando 3 segundos... (fale algo)")
    start = time.perf_counter()
    try:
        text = await voice.record_and_transcribe(3.0, language="auto")
        elapsed = time.perf_counter() - start
        print(f"    Transcrição: \"{text}\"")
        print(f"    Tempo: {elapsed*1000:.1f}ms")
    except Exception as e:
        print(f"    Erro: {e}")
    print()

    # Estatísticas finais
    print("=" * 60)
    print("  Estatísticas Finais:")
    print(f"    Chamadas TTS: {voice.stats.tts_calls}")
    print(f"    Chamadas STT: {voice.stats.stt_calls}")
    print(f"    TTS pronto: {voice.is_tts_ready}")
    print(f"    STT pronto: {voice.is_stt_ready}")
    print("=" * 60)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
