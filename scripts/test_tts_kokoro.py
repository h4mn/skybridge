#!/usr/bin/env python
# coding: utf-8
"""
Teste simples do TTS Kokoro.
"""

import asyncio
import sys
sys.path.insert(0, "src")

from core.sky.voice import get_voice_service


async def test_tts():
    """Testa TTS Kokoro com uma frase simples."""
    print("Testando TTS Kokoro...")
    print("Falando: Olá, esta é uma teste de voz.")
    print()

    voice = get_voice_service()

    # Pré-carrega modelo
    await voice.preload_tts()

    # Fala uma frase
    await voice.speak("Olá, esta é uma teste de voz.")

    print()
    print("[OK] TTS testado com sucesso!")


if __name__ == "__main__":
    asyncio.run(test_tts())
