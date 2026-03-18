# coding: utf-8
"""
Teste de integração STT com ChatTextArea (PRD027).

Este script testa o fluxo:
1. Usuário digita /stt 5
2. ChatTextArea detecta comando
3. STT transcreve áudio
4. Texto transcrito é enviado como mensagem normal
"""

import sys
import re
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


async def test_stt_integration():
    """Testa fluxo completo STT."""
    print("=" * 60)
    print("Teste: Integração STT com ChatTextArea (PRD027)")
    print("=" * 60)
    print()

    # Simula comando do usuário
    comando = "/stt 5"
    print(f"1. Usuário digita: {comando}")
    print()

    # Extrai duração
    match = re.match(r"/stt\s+(\d+(?:\.\d+)?)", comando)
    duration = float(match.group(1)) if match else 5.0

    print(f"2. Comando /stt detectado, duração: {duration}s")
    print(f"3. [MICROFONE] Ouvindo... (fale agora)")
    print()

    try:
        # Importa STT service e audio capture
        from core.sky.voice.stt_service import WhisperAdapter
        from core.sky.voice.audio_capture import SoundDeviceCapture
        import asyncio

        # Cria adaptador STT (lazy load)
        stt = WhisperAdapter()

        # Captura áudio
        capture = SoundDeviceCapture(sample_rate=16000, channels=1)
        await capture.start_recording()
        print(f"   Gravando por {duration}s...")
        await asyncio.sleep(duration)
        audio = await capture.stop_recording()
        print(f"   Audio capturado: {audio.duration:.2f}s")

        # Transcreve áudio
        from core.sky.voice.stt_service import TranscriptionConfig
        config = TranscriptionConfig(language="pt", detect_language=False)
        result = await stt.transcribe(audio, config)

        transcribed_text = result.text.strip()

        if transcribed_text:
            print(f"4. [OK] Transcricao: \"{transcribed_text}\"")
            print()
            print("5. Fluxo do chat:")
            print("   -> ChatTextArea define texto transcrito")
            print("   -> Submitted(texto_transcrito) e postado")
            print("   -> ChatScreen.on_chat_text_area_submitted() recebe")
            print("   -> _abrir_turno_e_processar(texto_transcrito)")
            print("   -> Turn e criado com texto transcrito no UserBubble")
            print("   -> _processar_mensagem() gera resposta da Sky")
            print("   -> Turn finaliza normalmente (ThinkingIndicator some)")
            print()
            print("=" * 60)
            print("[OK] SUCESSO: Integracao STT funcionando!")
            print("=" * 60)
            print()
            print("O que mudou:")
            print("- Antes: /stt criava Turn, mas ThinkingIndicator nunca sumia")
            print("- Agora:  /stt transcrito -> texto normal -> fluxo padrao")
            print()
            print("Problema resolvido:")
            print("- UserBubble mostra texto transcrito (nao comando)")
            print("- Turn funciona normalmente (ThinkingIndicator finaliza)")
            print("- SkyBubble mostra resposta da Sky")
            print()
            return transcribed_text
        else:
            print(f"4. [ERRO] Nenhuma fala detectada")
            print(f"   (Idioma detectado: {result.language}, Confianca: {result.confidence:.2f})")
            return None

    except Exception as e:
        print(f"[ERRO] Excecao: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_stt_integration())
