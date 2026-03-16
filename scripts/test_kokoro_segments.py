#!/usr/bin/env python
# coding: utf-8
"""
Teste para verificar se Kokoro gera múltiplos segmentos.
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "B:/_repositorios/skybridge/.claude/worktrees/prd027-sky-voice/src")


async def test_kokoro_segments():
    """Testa quantos segmentos o Kokoro gera para um texto longo."""
    from core.sky.voice.tts_service import KokoroAdapter, VoiceConfig

    tts = KokoroAdapter()

    # Texto longo com múltiplas quebras de linha
    texto = """Claro! Eu posso ajudar com isso.

A Sky é uma assistente de IA criada para auxiliar em diversas tarefas.

Vou explicar cada parte do sistema:

1. Primeiro componente
2. Segundo componente
3. Terceiro componente

Espero que isso ajude a entender!"""

    print("=" * 60)
    print("TESTE: Kokoro segmentos com texto longo")
    print("=" * 60)
    print(f"Texto: {len(texto)} chars")
    print(f"Quebras de linha (\\n): {texto.count(chr(10))}")
    print()

    # Carrega modelo
    print("Carregando modelo Kokoro...")
    await tts._load_model()
    print("Modelo carregado!")
    print()

    # Gera áudio
    print("Gerando áudio...")
    config = VoiceConfig(speed=1.0, language="pt-BR")

    # Verifica quantos segmentos são gerados
    from kokoro import KPipeline

    generator = tts._pipeline(
        texto,
        voice=tts.voice,
        speed=float(config.speed),
        split_pattern=r'\n+'
    )

    segments = []
    for i, (gs, ps, audio) in enumerate(generator):
        segments.append((gs, ps, audio))
        print(f"Segmento #{i+1}:")
        print(f"  Graphemes: {len(gs)} chars")
        print(f"  Phonemes: {len(ps)} itens")
        if audio is not None:
            import torch
            if hasattr(audio, 'shape'):
                print(f"  Audio shape: {audio.shape}")
                print(f"  Audio duration: {audio.shape[-1] / 24000:.2f}s")
        print()

    print(f"Total de segmentos: {len(segments)}")

    if segments:
        # Testa síntese completa com o novo código
        print("\n" + "=" * 60)
        print("Testando síntese completa (concatenando segmentos)...")
        print("=" * 60)

        try:
            audio_data = await tts.synthesize(texto, config)
            print(f"✓ Áudio gerado: {audio_data.duration:.2f}s")
        except Exception as e:
            print(f"✗ Erro: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_kokoro_segments())
