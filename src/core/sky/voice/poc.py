"""POC SIMPLES - API e Cliente no mesmo processo."""

import asyncio
import io
import sys
from pathlib import Path

# UTF-8
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
import sounddevice as sd

# Path
src_path = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(src_path))


async def main():
    print("=" * 60)
    print("[POC] Sky Voice API - Teste DIRETO")
    print("=" * 60)

    # Inicializa serviços
    print("\n[1/2] Carregando modelos...")
    from core.sky.voice.api.services.stt_service import get_stt_service
    from core.sky.voice.api.services.tts_service import get_tts_service

    stt = get_stt_service()
    await stt.load_model()
    print("      ✅ STT (faster-whisper) carregado")

    tts = get_tts_service()
    await tts.initialize()
    print("      ✅ TTS (Kokoro) carregado")

    print("\n" + "=" * 60)
    print("MENU:")
    print("  1. 🎤 Falar → Transcrever")
    print("  2. 🔊 Texto → Falar")
    print("  3. 🚪 Sair")
    print("=" * 60)

    while True:
        try:
            choice = input("\nOpção (1-3): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == "1":
            print("\n🎤 GRAVAÇÃO (5s)")
            print("   Fale agora...")

            audio = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='float32')
            sd.wait()

            print("   📡 Transcrevendo...")
            text = await stt.transcribe(audio.tobytes())
            print(f"   ✅ '{text}'")

        elif choice == "2":
            text = input("\n🔊 Texto: ").strip() or "Eu sou a Sky."
            print("   📡 Sintetizando...")

            # Usa KokoroAdapter direto (sem passar pelo serviço)
            from core.sky.voice.tts_adapter import KokoroAdapter, VoiceMode

            adapter = KokoroAdapter(voice="af_heart", lang_code="p")
            await adapter._load_model()

            audio_data = await adapter.synthesize(text, VoiceMode.NORMAL)
            audio_bytes = audio_data.samples

            print("   🔊 Tocando...")
            sd.play(np.frombuffer(audio_bytes, dtype=np.float32), samplerate=24000)
            sd.wait()
            print("   ✅ Fim!")

        elif choice == "3":
            print("\n👋 Tchau!")
            break

    print("\n" + "=" * 60)
    print("[POC] Fim!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
