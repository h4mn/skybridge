#!/usr/bin/env python3
"""
Teste Kokoro Warm Start - Múltiplas sínteses no mesmo processo

Demonstra a diferença de performance entre:
1. Cold start (primeira síntese com carregamento)
2. Warm start (sínteses subsequentes)

Uso:
    python scripts/test_kokoro_warm.py
"""

import sys
import os
import time

# Configura UTF-8 para saída no Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Adiciona src ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


async def main():
    """Teste warm start do Kokoro."""
    print("=" * 60)
    print(" " * 10 + "Kokoro TTS - Teste Warm Start")
    print("=" * 60)
    print()

    # Texto de teste
    text = "Olá! Eu sou a Sky, sua assistente virtual. Como posso ajudar você hoje?"

    print(f"  Texto: \"{text}\"")
    print(f"  Engine: Kokoro TTS (Hexgrad)")
    print(f"  Voz: af_heart (feminina, suave e natural)")
    print(f"  Idioma: Português Brasileiro 🇧🇷")
    print()
    print("  Carregando modelo... (uma única vez)")
    print()

    try:
        from core.sky.voice.tts_service import KokoroAdapter, VoiceConfig
        import sounddevice as sd
        import numpy as np

        # Inicializa adapter
        tts = KokoroAdapter(voice="af_heart", lang_code="p")
        config = VoiceConfig(speed=1.0)

        # Carrega modelo uma vez
        load_start = time.perf_counter()
        await tts._load_model()
        load_time = time.perf_counter() - load_start

        print(f"  ✓ Modelo carregado em {load_time*1000:.1f}ms")
        print()

        # Teste 1: Primeira síntese (warm start, modelo já carregado)
        print("  1ª Síntese:")
        synth_start = time.perf_counter()
        audio = await tts.synthesize(text, config)
        synth_time = time.perf_counter() - synth_start

        print(f"     Duração áudio: {audio.duration:.2f}s")
        print(f"     Tempo síntese: {synth_time*1000:.1f}ms")
        print(f"     RTF: {synth_time/audio.duration:.2f}x")
        print()
        print("  Reproduzindo...")
        samples = np.frombuffer(audio.samples, dtype=np.float32)
        sd.play(samples, samplerate=audio.sample_rate)
        sd.wait()
        print()

        # Teste 2: Segunda síntese
        print("  2ª Síntese:")
        synth_start = time.perf_counter()
        audio = await tts.synthesize(text, config)
        synth_time = time.perf_counter() - synth_start

        print(f"     Duração áudio: {audio.duration:.2f}s")
        print(f"     Tempo síntese: {synth_time*1000:.1f}ms")
        print(f"     RTF: {synth_time/audio.duration:.2f}x")
        print()
        print("  Reproduzindo...")
        samples = np.frombuffer(audio.samples, dtype=np.float32)
        sd.play(samples, samplerate=audio.sample_rate)
        sd.wait()
        print()

        # Teste 3: Terceira síntese
        print("  3ª Síntese:")
        synth_start = time.perf_counter()
        audio = await tts.synthesize(text, config)
        synth_time = time.perf_counter() - synth_start

        print(f"     Duração áudio: {audio.duration:.2f}s")
        print(f"     Tempo síntese: {synth_time*1000:.1f}ms")
        print(f"     RTF: {synth_time/audio.duration:.2f}x")
        print()
        print("  Reproduzindo...")
        samples = np.frombuffer(audio.samples, dtype=np.float32)
        sd.play(samples, samplerate=audio.sample_rate)
        sd.wait()
        print()

        print("=" * 60)
        print("  ✓ Teste concluído!")
        print("  📊 Com modelo em memória, RTF estável e baixo")
        print("=" * 60)

    except Exception as e:
        print(f"  ✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
