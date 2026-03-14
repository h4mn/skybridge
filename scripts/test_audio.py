#!/usr/bin/env python3
"""
Teste de Gravação Standalone - Captura de Áudio

Este script testa APENAS a captura de áudio (sem STT/TTS).
Verifica se o microfone está funcionando e capturando áudio corretamente.

Uso:
    python scripts/test_audio.py
"""

import sys
import os
import asyncio
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
    """Teste de gravação standalone."""
    print("=" * 60)
    print(" " * 10 + "Teste de Gravação Standalone")
    print("=" * 60)
    print()
    print("  Este teste verifica APENAS a captura de áudio.")
    print("  Fale algo durante 3 segundos...")
    print()

    try:
        from core.sky.voice.audio_capture import SoundDeviceCapture
        import numpy as np

        # Configura captura
        capture = SoundDeviceCapture(sample_rate=16000, channels=1)

        print("  Iniciando gravação...")
        print()

        await capture.start_recording()

        # Feedback visual durante gravação
        duration = 3.0
        start = time.time()
        dots = 0

        while time.time() - start < duration:
            elapsed = time.time() - start
            remaining = duration - elapsed

            # Animação de pontos
            dots = (dots + 1) % 4
            progress = "." * dots + " " * (3 - dots)
            print(f"  Gravando{progress} ({remaining:.1f}s restantes)", end="\r")

            await asyncio.sleep(0.1)

        print()  # Nova linha após animação

        # Para gravação
        audio = await capture.stop_recording()

        print()
        print("=" * 60)
        print("  ✓ Gravação concluída!")
        print("=" * 60)
        print()
        print(f"  Duração: {audio.duration:.2f}s")
        print(f"  Sample rate: {audio.sample_rate} Hz")
        print(f"  Canais: {audio.channels}")
        print(f"  Tamanho: {len(audio.samples):,} bytes ({len(audio.samples)/1024:.1f} KB)")
        print()

        # Analisa volume do áudio capturado
        import numpy as np
        samples = np.frombuffer(audio.samples, dtype=np.float32)

        # Evita divisão por zero
        if len(samples) > 0:
            # Volume médio (RMS)
            rms = np.sqrt(np.mean(samples ** 2))

            # Volume máximo
            max_vol = np.max(np.abs(samples))

            # Detecta se há áudio
            has_audio = rms > 0.001

            print("  Análise de volume:")
            print(f"    RMS (volume médio): {rms:.6f}")
            print(f"    Máximo: {max_vol:.6f}")
            print(f"    Áudio detectado: {'✓ Sim' if has_audio else '✗ Não (muito baixo)'}")
            print()

            if not has_audio:
                print("  ⚠️ AVISO: Volume muito baixo!")
                print("     Verifique:")
                print("     - Microfone conectado")
                print("     - Microfone não está mudo")
                print("     - Dispositivo de áudio correto")
                return 1
        else:
            print("  ✗ ERRO: Nenhum dado de áudio capturado")
            return 1

        # Teste de reprodução (opcional)
        print()
        response = input("  Deseja reproduzir o áudio gravado? (s/N): ").strip().lower()

        if response == 's':
            print("  Reproduzindo...")
            try:
                import sounddevice as sd
                sd.play(samples, samplerate=audio.sample_rate)
                sd.wait()
                print("  ✓ Reprodução concluída")
            except Exception as e:
                print(f"  ✗ Erro na reprodução: {e}")

        print()
        print("=" * 60)
        print("  ✓ Teste concluído com sucesso!")
        print("  Microfone funcionando corretamente.")
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
