#!/usr/bin/env python3
"""
Teste Standalone - STT (Speech-to-Text)

Este script testa a transcrição de áudio com Whisper sem depender do chat.

Usage:
    cd B:/_repositorios/skybridge/.claude/worktrees/prd027-sky-voice
    python scripts/test_stt.py

O que acontece:
1. Exibe instruções para o usuário
2. Grava 5 segundos de áudio do microfone
3. Transcreve com Whisper
4. Exibe resultado na tela

Requisitos:
    - pip install faster-whisper sounddevice numpy torch
"""

import asyncio
import os
import sys
import time

# Adiciona src ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, "src"))

from src.core.sky.voice.audio_capture import SoundDeviceCapture, AudioState
from src.core.sky.voice.stt_service import WhisperAdapter, TranscriptionConfig


async def main():
    """Função principal do teste."""

    print("=" * 60)
    print(" " * 15 + "STT Test - Speech to Text")
    print("=" * 60)
    print()
    print("Este teste irá:")
    print("  1. Gravar 5 segundos do seu microfone")
    print("  2. Transcrever com Whisper (STT)")
    print("  3. Exibir o resultado na tela")
    print()
    print(">>> Fale algo agora! <<<")
    print()

    # Aguarda 2 segundos para usuário se preparar
    for i in range(2, 0, -1):
        print(f"  Gravando em {i}...", end="\r")
        await asyncio.sleep(1)

    print("  ** GRAVANDO ** [5 segundos]")
    print()

    # Inicia captura de áudio
    capture = SoundDeviceCapture(sample_rate=16000, channels=1)

    try:
        await capture.start_recording()

        # Grava por 5 segundos
        duration = 5.0
        start_time = time.time()

        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            print(f"  Gravando... {remaining:.1f}s restantes", end="\r")
            await asyncio.sleep(0.1)

        print()

        # Para gravação
        audio = await capture.stop_recording()

        print(f"  ✓ Áudio capturado: {audio.duration:.2f} segundos")
        print(f"  ✓ Tamanho: {len(audio.samples)} bytes")
        print()
        print("  Transcrevendo com Whisper...")
        print()

        # Transcreve
        stt = WhisperAdapter(model_size="base", device="cpu")

        result = await stt.transcribe(
            audio,
            config=TranscriptionConfig(
                language="pt",
                detect_language=False,
            ),
        )

        # Exibe resultado
        print("  " + "=" * 56)
        print("  RESULTADO DA TRANSCRIÇÃO")
        print("  " + "=" * 56)
        print()
        print(f"  Texto:     {result.text}")
        print(f"  Idioma:    {result.language}")
        print(f"  Confiança: {result.confidence:.2%}")
        print(f"  Duração:   {result.duration:.2f}s")
        print()
        print("=" * 60)

    except ImportError as e:
        print()
        print("  ❌ Erro de importação:")
        print(f"     {e}")
        print()
        print("  Instale as dependências:")
        print("     pip install faster-whisper sounddevice numpy torch")
        print()
        return 1

    except Exception as e:
        print()
        print(f"  ❌ Erro: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
