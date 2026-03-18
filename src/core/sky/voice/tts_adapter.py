# -*- coding: utf-8 -*-
"""
TTS Adapter - Interface abstrata para backends de Text-to-Speech.

Permite trocar backend TTS (Kokoro, MOSS, etc) sem mudar código consumidor.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from typing import Optional

from core.sky.voice.audio_capture import AudioData
from core.sky.voice.voice_modes import VoiceMode, add_hesitations


class TTSAdapter(ABC):
    """
    Interface abstrata para backends de Text-to-Speech.

    Cada adapter deve implementar speak() e synthesize() com suporte
    a VoiceMode para controlar velocidade e hesitações.
    """

    @abstractmethod
    async def speak(self, text: str, mode: VoiceMode = VoiceMode.NORMAL) -> None:
        """
        Sintetiza e reproduz áudio.

        Args:
            text: Texto para falar
            mode: Modo de voz (NORMAL ou THINKING)
        """
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        mode: VoiceMode = VoiceMode.NORMAL,
    ) -> AudioData:
        """
        Sintetiza áudio sem reproduzir.

        Args:
            text: Texto para sintetizar
            mode: Modo de voz (NORMAL ou THINKING)

        Returns:
            AudioData com o áudio gerado
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> list[str]:
        """Retorna lista de vozes disponíveis."""
        pass


class KokoroAdapter(TTSAdapter):
    """
    Adapter para Kokoro TTS (Hexgrad).

    Características:
    - Voz feminina suave e natural
    - Alta qualidade de fala
    - Modelo compacto de 82M
    - Multi-idioma: EN, ES, FR, HI, IT, JA, PT-BR
    """

    # Speed por modo
    SPEED_BY_MODE = {
        VoiceMode.NORMAL: 1.0,
        VoiceMode.THINKING: 0.85,
    }

    def __init__(
        self,
        voice: str = "af_heart",
        lang_code: str = "p",
        device: str = "auto",
        use_half_precision: bool = True,
    ):
        """
        Inicializa adapter Kokoro.

        Args:
            voice: Voz Kokoro ("af_heart" = feminina suave padrão)
            lang_code: Código do idioma ('p' = pt-BR padrão)
            device: Dispositivo ('auto', 'cuda', 'cpu')
            use_half_precision: Usar FP16 para acelerar (padrão True)
        """
        self.voice = voice
        self.lang_code = lang_code
        self.device = device
        self.use_half_precision = use_half_precision
        self._pipeline = None
        self._audio_queue: list = []
        self._playing = False

    async def _load_model(self) -> None:
        """Carrega pipeline Kokoro com otimizações (async wrapper)."""
        if self._pipeline is None:
            await asyncio.to_thread(self._load_model_sync)

    def _load_model_sync(self) -> None:
        """Carrega pipeline Kokoro (síncrono - executado em thread separada)."""
        if self._pipeline is None:
            try:
                from kokoro import KPipeline
                import torch

                device = self.device
                if device == "auto":
                    device = "cuda" if torch.cuda.is_available() else "cpu"

                self._pipeline = KPipeline(
                    lang_code=self.lang_code,
                    device=device,
                    model=self.use_half_precision,
                )

            except ImportError as e:
                raise ImportError(
                    "kokoro não está instalado. "
                    "Execute: pip install kokoro"
                ) from e

    async def speak(self, text: str, mode: VoiceMode = VoiceMode.NORMAL) -> None:
        """
        Sintetiza e reproduz áudio (NÃO bloqueia o event loop).

        Args:
            text: Texto para falar
            mode: Modo de voz (NORMAL ou THINKING)
        """
        print(f"[TTS] speak() chamado: texto={len(text)} chars, modo={mode}")

        # Aplica hesitações se modo thinking
        if mode == VoiceMode.THINKING:
            text = add_hesitations(text, intensity=0.3)

        # Executa síntese em thread separada (operações de CPU pesadas)
        print(f"[TTS] Iniciando síntese...")
        audio = await asyncio.to_thread(self._synthesize_sync, text, mode)
        print(f"[TTS] Síntese concluída: {audio.duration:.2f}s")

        await self._play_audio(audio)
        print(f"[TTS] speak() concluído")

    def _synthesize_sync(self, text: str, mode: VoiceMode) -> "AudioData":
        """Síntese síncrona - executada em thread separada via to_thread."""
        # Carrega modelo se necessário (também síncrono)
        if self._pipeline is None:
            self._load_model_sync()

        import numpy as np
        import torch

        speed = self.SPEED_BY_MODE.get(mode, 1.0)

        # Gera áudio com Kokoro
        generator = self._pipeline(
            text,
            voice=self.voice,
            speed=speed,
            split_pattern=r'\n+'
        )

        # Concatena todos os segmentos
        audio_segments = []
        for gs, ps, audio in generator:
            if audio is not None:
                audio_segments.append(audio)

        if not audio_segments:
            raise RuntimeError("Falha ao gerar áudio com Kokoro")

        audio_array = torch.cat(audio_segments, dim=-1)

        if hasattr(audio_array, 'cpu'):
            audio_array = audio_array.cpu().numpy()

        if audio_array.dtype != np.float32:
            audio_array = audio_array.astype(np.float32)

        if np.max(np.abs(audio_array)) > 0:
            audio_array = audio_array / np.max(np.abs(audio_array))

        audio_bytes = (audio_array * 0.8).astype(np.float32).tobytes()

        sample_rate = 24000
        duration = len(audio_array) / sample_rate

        from core.sky.voice.audio_capture import AudioData
        return AudioData(
            samples=audio_bytes,
            sample_rate=sample_rate,
            channels=1,
            duration=duration,
        )

    async def synthesize(
        self,
        text: str,
        mode: VoiceMode = VoiceMode.NORMAL,
    ) -> AudioData:
        """
        Sintetiza áudio sem reproduzir (NÃO bloqueia o event loop).

        Args:
            text: Texto para sintetizar
            mode: Modo de voz (NORMAL ou THINKING)

        Returns:
            AudioData com o áudio gerado
        """
        # Executa síntese em thread separada (operações de CPU pesadas)
        return await asyncio.to_thread(self._synthesize_sync, text, mode)

    async def _play_audio(self, audio: AudioData) -> None:
        """
        Reproduz áudio usando sounddevice.

        IMPORTANTE: sounddevice/PortAudio NÃO é thread-safe em threads secundárias.
        Usamos sd.play() + await asyncio.sleep() no event loop principal
        em vez de asyncio.to_thread() que causa falha silenciosa.
        """
        try:
            import sounddevice as sd
            import numpy as np

            samples = np.frombuffer(audio.samples, dtype=np.float32)

            # DEBUG: Verifica se há amostras válidas
            if len(samples) == 0:
                print("[TTS] WARNING: Tentativa de reproduzir áudio vazio")
                return

            # DEBUG: Verifica dispositivo de áudio
            try:
                devices = sd.query_devices()
                default_output = sd.default.device[1]  # Índice do dispositivo de saída
                if default_output < 0:
                    print(f"[TTS] ERROR: Nenhum dispositivo de áudio de saída configurado")
                    print(f"[TTS] Dispositivos disponíveis: {len(devices)}")
                    return
            except Exception as dev_err:
                print(f"[TTS] ERROR ao verificar dispositivo: {dev_err}")

            # sd.play() funciona corretamente no event loop principal
            # Não usar asyncio.to_thread() - PortAudio não é thread-safe
            print(f"[TTS] Reproduzindo {len(samples)} amostras @ {audio.sample_rate}Hz ({audio.duration:.2f}s)")
            sd.play(samples, samplerate=audio.sample_rate)

            # Aguarda duração do áudio sem bloquear o event loop
            # +50ms buffer para garantir reprodução completa
            try:
                await asyncio.sleep(audio.duration + 0.05)
            except asyncio.CancelledError:
                # FIX: Quando cancelado, para o áudio mas não propaga erro
                # Isso evita erro de anyio cancel scope
                print("[TTS] Reprodução interrompida (cancelada)")
                sd.stop()
                return  # Retorna silenciosamente sem propagar CancelledError

            # Para reprodução ao final
            sd.stop()
            print("[TTS] Reprodução concluída")

        except ImportError:
            raise ImportError("sounddevice não está instalado")
        except asyncio.CancelledError:
            # FIX: Captura CancelledError e faz cleanup sem propagar
            print("[TTS] CancelledError capturado, fazendo cleanup")
            try:
                import sounddevice as sd
                sd.stop()
            except Exception:
                pass
            return  # Retorna silenciosamente
        except Exception as e:
            # Garante que para o áudio em caso de erro
            print(f"[TTS] ERROR em _play_audio: {e}")
            try:
                import sounddevice as sd
                sd.stop()
            except Exception:
                pass
            raise RuntimeError(f"Erro ao reproduzir áudio: {e}")

    def get_available_voices(self) -> list[str]:
        """Retorna vozes disponíveis."""
        return [
            "af_heart",
            "af_sky",
            "af_bella",
            "sky-female",
        ]


# =============================================================================
# Fábrica de Adapters
# =============================================================================

_tts_adapter: Optional[TTSAdapter] = None


def get_tts_adapter() -> TTSAdapter:
    """
    Retorna o adapter TTS configurado.

    Usa variável de ambiente TTS_BACKEND para selecionar backend:
    - "kokoro" (padrão): KokoroAdapter
    - "moss": MOSSAdapter (TODO)

    Returns:
        Instância singleton do adapter TTS
    """
    global _tts_adapter

    if _tts_adapter is not None:
        return _tts_adapter

    backend = os.getenv("TTS_BACKEND", "kokoro").lower()

    if backend == "kokoro":
        _tts_adapter = KokoroAdapter()
    elif backend == "moss":
        # TODO: Implementar MOSSAdapter
        raise NotImplementedError("MOSSAdapter ainda não implementado")
    else:
        raise ValueError(f"Backend TTS desconhecido: {backend}")

    return _tts_adapter


__all__ = [
    "TTSAdapter",
    "KokoroAdapter",
    "get_tts_adapter",
]
