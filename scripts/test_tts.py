#!/usr/bin/env python3
"""
Teste Standalone - TTS (Text-to-Speech)

Este script testa a síntese de voz com o MOSSTTSAdapter.

Usage:
    python scripts/test_tts.py [texto]

Se não fornecer texto, usa um texto padrão.

O que acontece:
1. Sintetiza áudio a partir do texto
2. Reproduz via sounddevice
3. Exibe informações sobre a geração

NOTA: Esta é uma implementação protótipo que gera áudio sintético.
Para fala real, será necessário integrar com MOSS-TTS ou similar.
"""

import asyncio
import os
import sys

# Adiciona src ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from core.sky.voice.tts_service import MOSSTTSAdapter, VoiceConfig


async def main():
    """Função principal do teste."""

    # Texto padrão ou argumento
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "Olá! Eu sou a Sky, sua assistente de voz."

    print("=" * 60)
    print(" " * 12 + "TTS Test - Text to Speech")
    print("=" * 60)
    print()
    print(f"  Texto: \"{text}\"")
    print()
    print("  Sintetizando áudio...")
    print()

    try:
        # Inicializa TTS
        tts = MOSSTTSAdapter(voice="sky-female")

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
        print(f"    Tempo de síntese: {synth_time*1000:.1f}ms")
        print()
        print("  Reproduzindo...")
        print()

        # Reproduz
        await tts.speak(text, config)

        print()
        print("=" * 60)
        print("  ✓ Reprodução concluída!")
        print("=" * 60)

        return 0

    except ImportError as e:
        print()
        print("  ❌ Erro de importação:")
        print(f"     {e}")
        print()
        print("  Instale as dependências:")
        print("     pip install sounddevice numpy")
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
