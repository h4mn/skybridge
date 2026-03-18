#!/usr/bin/env python3
"""
Script de Instalação Automatizada - Sky Voice

Instala todas as dependências necessárias para o sistema de voz.

Uso:
    python scripts/install_voice_deps.py
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Executa comando e exibe progresso."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    print(f"  Comando: {cmd}")
    print()

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n  ✓ {description} - OK")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n  ✗ Erro: {e}")
        return False


def main():
    """Instala dependências de voz."""
    print("=" * 60)
    print(" " * 15 + "Sky Voice - Instalação")
    print("=" * 60)
    print()

    # Verifica Python
    if sys.version_info < (3, 11):
        print("  ✗ Python 3.11+ requerido")
        print(f"    Atual: {sys.version}")
        return 1

    print(f"  Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print()

    # Lista de pacotes para instalar
    packages = [
        # Áudio
        ("sounddevice>=0.4.6", "sounddevice - Captura/reprodução de áudio"),
        ("soundfile>=0.12.0", "soundfile - Leitura/escrita de áudio"),
        ("numpy>=1.24.0", "numpy - Arrays de áudio"),

        # STT - Speech-to-Text
        ("faster-whisper>=1.0.0", "faster-whisper - Whisper otimizado"),

        # TTS - Text-to-Speech
        ("kokoro>=0.9.4", "kokoro - Voz feminina natural"),
        ("transformers>=4.30.0", "transformers - Modelos TTS alternativos"),
        ("scipy>=1.10.0", "scipy - Processamento de sinal"),

        # PyTorch (dependência ML)
        ("torch>=2.1.0", "torch - Machine learning framework"),

        # Alternativa TTS (fallback)
        ("pyttsx3>=2.90", "pyttsx3 - Voz offline fallback"),
    ]

    success_count = 0
    failed_count = 0

    for package, description in packages:
        cmd = f"{sys.executable} -m pip install {package}"
        if run_command(cmd, description):
            success_count += 1
        else:
            failed_count += 1

    # Resumo
    print()
    print("=" * 60)
    print(" " * 20 + "Resumo da Instalação")
    print("=" * 60)
    print(f"  ✓ Sucesso: {success_count}/{len(packages)} pacotes")
    if failed_count > 0:
        print(f"  ✗ Falhas: {failed_count}/{len(packages)} pacotes")
        print()
        print("  ⚠️ Alguns pacotes falharam. Verifique os erros acima.")
        return 1
    else:
        print()
        print("  ✓ Todas as dependências instaladas com sucesso!")
        print()
        print("  Próximos passos:")
        print("    1. Teste TTS: python scripts/test_kokoro.py")
        print("    2. Teste STT: python scripts/test_stt.py")
        print("    3. Teste VoiceService: python scripts/test_voice_service.py")
        print()
        print("=" * 60)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
