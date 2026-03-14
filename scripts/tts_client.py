#!/usr/bin/env python3
"""
Cliente TTS Simplificado - Teste rápido do servidor persistente

Uso:
    # Terminal 1: Inicia servidor
    python scripts/tts_server.py

    # Terminal 2: Cliente envia requisição
    python scripts/tts_client_simple.py "Olá Sky"
"""

import sys
import os
import json
import time
import sounddevice as sd
import numpy as np

# Adiciona src ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def main():
    """Cliente simples que se conecta ao servidor via stdin/stdout."""
    if len(sys.argv) < 2:
        print("Uso: python scripts/tts_client_simple.py <texto>")
        sys.exit(1)

    text = " ".join(sys.argv[1:])

    print("=" * 60)
    print(" " * 15 + "Cliente TTS - Kokoro (Simples)")
    print("=" * 60)
    print(f"  Texto: \"{text}\"")
    print()
    print("  Digite requisições JSON (Ctrl+D para sair):")
    print()

    # Lê requisição do stdin
    request = {
        "action": "synthesize",
        "text": text,
        "voice": "af_heart",
        "speed": 1.0
    }

    start = time.perf_counter()

    # Envia para stdout (que será redirecionado para o servidor)
    print(json.dumps(request))
    sys.stdout.flush()

    # Lê resposta do stdin (que vem do servidor)
    response_line = sys.stdin.readline()

    if not response_line:
        print("  ✗ Nenhuma resposta do servidor")
        sys.exit(1)

    try:
        response = json.loads(response_line)
    except json.JSONDecodeError:
        print(f"  ✗ Resposta inválida: {response_line}")
        sys.exit(1)

    total_time = time.perf_counter() - start

    if response.get("status") == "ok":
        audio_file = response.get("audio_file")
        duration = response.get("duration")
        synth_time = response.get("synth_time_ms") / 1000

        print(f"  ✓ Sintetizado:", file=sys.stderr)
        print(f"     Duração: {duration:.2f}s", file=sys.stderr)
        print(f"     Síntese: {synth_time*1000:.1f}ms", file=sys.stderr)
        print(f"     RTF: {synth_time/duration:.2f}x", file=sys.stderr)
        print(f"     Total: {total_time*1000:.1f}ms", file=sys.stderr)
        print(f"     Arquivo: {audio_file}", file=sys.stderr)

        # Reproduz áudio
        print(f"  Reproduzindo...", file=sys.stderr)
        with open(audio_file, 'rb') as f:
            audio_bytes = f.read()
        samples = np.frombuffer(audio_bytes, dtype=np.float32)
        sd.play(samples, samplerate=24000)
        sd.wait()

        # Remove arquivo temporário
        os.unlink(audio_file)

        print(f"  ✓ Concluído!", file=sys.stderr)

    else:
        error = response.get("message", "Erro desconhecido")
        print(f"  ✗ Erro: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
