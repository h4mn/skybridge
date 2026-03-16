#!/usr/bin/env python3
"""
Teste Kokoro TTS - Voz Feminina Natural

Este script testa a síntese de voz com Kokoro TTS.

Usage:
    python scripts/test_kokoro.py [texto]

O que acontece:
1. Carrega modelo Kokoro (primeira vez: download)
2. Sintetiza áudio com voz feminina natural
3. Reproduz via sounddevice

NOTA: Kokoro é um modelo da AI Factory com vozes muito naturais.
"""

import asyncio
import os
import sys

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

from core.sky.voice.tts_service import KokoroAdapter, VoiceConfig


async def main():
    """Função principal do teste."""

    # Texto padrão ou argumento
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "Olá! Eu sou a Sky, e esta é minha voz feminina natural."

    print("=" * 60)
    print(" " * 10 + "Kokoro TTS - Voz Feminina Natural")
    print("=" * 60)
    print()
    print(f"  Texto: \"{text}\"")
    print(f"  Engine: Kokoro TTS (Hexgrad)")
    print(f"  Modelo: hexgrad/Kokoro-82M")
    print(f"  Voz: af_heart (feminina, suave e natural)")
    print(f"  Idioma: Português Brasileiro 🇧🇷 (lang_code='p')")
    print()
    print("  Carregando modelo... (primeira vez: download via pip)")
    print()

    try:
        # Inicializa TTS com Kokoro (Português Brasileiro)
        tts = KokoroAdapter(voice="af_heart", lang_code="p")

        # Configuração
        config = VoiceConfig(
            voice_id="sky-female",
            speed=1.0,
            pitch=0,
            language="pt-BR",
        )

        # Sintetiza
        import time
        start = time.perf_counter()

        audio = await tts.synthesize(text, config)

        synth_time = time.perf_counter() - start

        print(f"  ✓ Áudio sintetizado")
        print(f"    Duração: {audio.duration:.2f}s")
        print(f"    Tamanho: {len(audio.samples):,} bytes ({len(audio.samples)/1024:.1f} KB)")
        print(f"    Sample rate: {audio.sample_rate} Hz")
        print(f"    Tempo de síntese: {synth_time*1000:.1f}ms")
        print()
        print("  Reproduzindo...")
        print()

        # Reproduz
        await tts.speak(text, config)

        print()
        print("=" * 60)
        print("  ✓ Reprodução concluída!")
        print("  🎤 Voz: Kokoro af_heart (feminina suave)")
        print("=" * 60)

        return 0

    except ImportError as e:
        print()
        print("  ❌ Erro de importação:")
        print(f"     {e}")
        print()
        print("  Instale as dependências:")
        print("     pip install kokoro sounddevice")
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
