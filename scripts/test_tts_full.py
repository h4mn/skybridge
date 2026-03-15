#!/usr/bin/env python
# coding: utf-8
"""
Teste completo do TTS progressivo.
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "src")


async def test_tts_worker():
    """Simula o worker TTS progressivo."""
    from core.sky.chat.textual_ui.voice_commands import get_voice_handler

    handler = get_voice_handler()

    # Simula chunks chegando progressivamente
    chunks = [
        "Olá! Eu sou a Sky, ",
        "sua assistente de IA. ",
        "Estou aqui para ajudar você ",
        "com o que precisar. "
    ]

    print("Testando TTS progressivo com chunks...")
    print(f"Total de chunks: {len(chunks)}")

    accumulated = []
    last_spoken = 0

    for i, chunk in enumerate(chunks):
        accumulated.append(chunk)
        text = "".join(accumulated)

        print(f"\nChunk {i+1}: +{len(chunk)} chars")
        print(f"  Acumulado: {len(text)} chars")
        print(f"  Texto: {repr(text[last_spoken:])}")

        # Simula limpeza
        clean = text.strip()

        new_content = clean[last_spoken:]
        if new_content:
            print(f"  Falando: {repr(new_content)}")
            try:
                await handler.handle_tts(new_content)
                last_spoken = len(clean)
                print(f"  ✓ Falou {len(new_content)} chars")
            except Exception as e:
                print(f"  ✗ Erro: {e}")

    print(f"\nTotal falado: {last_spoken} chars")
    print(f"Total acumulado: {len(''.join(chunks))} chars")


if __name__ == "__main__":
    asyncio.run(test_tts_worker())
