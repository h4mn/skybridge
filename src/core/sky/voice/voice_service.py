# -*- coding: utf-8 -*-
"""
VoiceService - Serviço Singleton de TTS/STT.

Gerencia modelos de voz (Kokoro TTS, Whisper STT) com lazy load.
Mantém modelos em memória após primeira inicialização.

Uso:
    from core.sky.voice import get_voice_service

    voice = get_voice_service()
    await voice.speak("Olá mundo")  # Primeira vez: carrega modelo
    await voice.speak("Segunda vez")  # Modelo já carregado (rápido!)
"""

import asyncio
from typing import Optional
from dataclasses import dataclass

from core.sky.voice.tts_service import KokoroAdapter, VoiceConfig
from core.sky.voice.stt_service import WhisperAdapter, TranscriptionConfig
from core.sky.voice.audio_capture import SoundDeviceCapture, AudioData


@dataclass
class VoiceStats:
    """Estatísticas de uso do VoiceService."""
    tts_calls: int = 0
    stt_calls: int = 0
    tts_load_time_ms: float = 0
    stt_load_time_ms: float = 0


class VoiceService:
    """
    Serviço de voz singleton para TTS e STT.

    Características:
    - Lazy load: Modelos carregados sob demanda
    - Warm cache: Modelos permanecem em memória
    - Thread-safe: Uso em ambientes async
    - Multi-idioma: pt-BR padrão, auto-detecção disponível

    Performance:
    - Cold start TTS: ~3s (primeira vez)
    - Warm start TTS: ~0.3s (RTF 0.35x - mais rápido que tempo real!)
    - Warm start STT: ~0.1s (RTF 0.06x - 16x mais rápido!)
    """

    _instance: Optional["VoiceService"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        """Inicializa serviço (use get_voice_service() em vez disso)."""
        self._tts: Optional[KokoroAdapter] = None
        self._stt: Optional[WhisperAdapter] = None
        self._stats = VoiceStats()
        self._tts_loading = False
        self._stt_loading = False

    @classmethod
    def get_instance(cls) -> "VoiceService":
        """Retorna instância singleton do VoiceService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def _ensure_tts(self) -> KokoroAdapter:
        """Garante que TTS está carregado (lazy load com lock)."""
        if self._tts is None and not self._tts_loading:
            async with self._lock:
                # Double-check pattern
                if self._tts is None and not self._tts_loading:
                    self._tts_loading = True
                    try:
                        import time
                        start = time.perf_counter()

                        self._tts = KokoroAdapter(
                            voice="af_heart",  # Feminina suave
                            lang_code="p"       # Português Brasileiro
                        )
                        await self._tts._load_model()

                        load_time = time.perf_counter() - start
                        self._stats.tts_load_time_ms = load_time * 1000

                    finally:
                        self._tts_loading = False

        return self._tts

    async def _ensure_stt(self) -> WhisperAdapter:
        """Garante que STT está carregado (lazy load com lock)."""
        if self._stt is None and not self._stt_loading:
            async with self._lock:
                # Double-check pattern
                if self._stt is None and not self._stt_loading:
                    self._stt_loading = True
                    try:
                        import time
                        start = time.perf_counter()

                        self._stt = WhisperAdapter(
                            model_size="base",
                            device="cpu"
                        )

                        load_time = time.perf_counter() - start
                        self._stats.stt_load_time_ms = load_time * 1000

                    finally:
                        self._stt_loading = False

        return self._stt

    async def speak(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> None:
        """
        Sintetiza e reproduz áudio (TTS).

        Args:
            text: Texto para falar
            voice: Voz Kokoro (padrão: af_heart)
            speed: Velocidade da fala (1.0 = normal)
        """
        tts = await self._ensure_tts()
        config = VoiceConfig(speed=speed, pitch=0, language="pt-BR")
        await tts.speak(text, config)
        self._stats.tts_calls += 1

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> AudioData:
        """
        Sintetiza áudio sem reproduzir.

        Args:
            text: Texto para falar
            voice: Voz Kokoro (padrão: af_heart)
            speed: Velocidade da fala (1.0 = normal)

        Returns:
            AudioData com o áudio sintetizado
        """
        tts = await self._ensure_tts()
        config = VoiceConfig(speed=speed, pitch=0, language="pt-BR")
        audio = await tts.synthesize(text, config)
        self._stats.tts_calls += 1
        return audio

    async def transcribe(
        self,
        audio: AudioData,
        language: str = "auto",
        detect_language: bool = True
    ) -> str:
        """
        Transcreve áudio para texto (STT).

        Args:
            audio: AudioData para transcrever
            language: Idioma ("auto", "pt", "en", etc.)
            detect_language: Auto-detectar idioma

        Returns:
            Texto transcrito
        """
        stt = await self._ensure_stt()

        lang = None if language == "auto" else language
        config = TranscriptionConfig(
            language=lang,
            detect_language=detect_language
        )

        result = await stt.transcribe(audio, config)
        self._stats.stt_calls += 1
        return result.text

    async def record_and_transcribe(
        self,
        duration: float = 5.0,
        language: str = "auto"
    ) -> str:
        """
        Grava áudio do microfone e transcreve.

        Args:
            duration: Duração da gravação em segundos
            language: Idioma ("auto", "pt", "en", etc.)

        Returns:
            Texto transcrito
        """
        stt = await self._ensure_stt()

        # Grava áudio
        capture = SoundDeviceCapture(sample_rate=16000, channels=1)
        await capture.start_recording()
        await asyncio.sleep(duration)
        audio = await capture.stop_recording()

        # Transcreve
        return await self.transcribe(audio, language=language)

    @property
    def stats(self) -> VoiceStats:
        """Retorna estatísticas de uso."""
        return self._stats

    @property
    def is_tts_ready(self) -> bool:
        """Verifica se TTS está carregado."""
        return self._tts is not None

    @property
    def is_stt_ready(self) -> bool:
        """Verifica se STT está carregado."""
        return self._stt is not None

    async def preload_tts(self) -> None:
        """Pré-carrega modelo TTS (opcional, para warm start)."""
        await self._ensure_tts()

    async def preload_stt(self) -> None:
        """Pré-carrega modelo STT (opcional, para warm start)."""
        await self._ensure_stt()

    async def preload_all(self) -> None:
        """Pré-carrega ambos os modelos (opcional)."""
        await self._ensure_tts()
        await self._ensure_stt()


# Singleton accessor
_voice_service: Optional[VoiceService] = None


def get_voice_service() -> VoiceService:
    """Retorna instância singleton do VoiceService."""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService.get_instance()
    return _voice_service


__all__ = [
    "VoiceService",
    "VoiceStats",
    "get_voice_service",
]
