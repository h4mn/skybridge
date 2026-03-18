# -*- coding: utf-8 -*-
"""
Testes unitários para TTSAdapter e fábrica.

DOC: src/core/sky/voice/tts_adapter.py - Interface e fábrica para TTS.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio

from core.sky.voice.tts_adapter import (
    TTSAdapter,
    AudioData,
    get_tts_adapter,
)
from core.sky.voice.voice_modes import VoiceMode


from core.sky.voice.voice_modes import VoiceMode


class TestAudioData:
    """Testes para a dataclass AudioData."""

    def test_audio_data_creation(self):
        """AudioData deve ser criado com valores corretos."""
        samples = b"\x00\x01\x02"
        audio = AudioData(samples=samples, sample_rate=22050)

        assert audio.samples == samples
        assert audio.sample_rate == 22050

    def test_audio_data_duration_seconds(self):
        """AudioData.duration_seconds deve retornar duração correta."""
        # 22050 samples @ 22050 Hz = 1 segundo
        samples = b"\x00" * 22050 * 4  # float32 = 4 bytes per sample
        audio = AudioData(samples=samples, sample_rate=22050)

        assert audio.duration_seconds == 1.0

    def test_audio_data_duration_milliseconds(self):
        """AudioData.duration_ms deve retornar duração em milissegundos."""
        # 22050 samples @ 22050 Hz = 1 segundo = 1000ms
        samples = b"\x00" * 22050 * 4
        audio = AudioData(samples=samples, sample_rate=22050)

        assert audio.duration_ms == 1000.0


class TestTTSAdapter:
    """Testes para a classe abstrata TTSAdapter."""

    def test_tts_adapter_cannot_be_instantiated(self):
        """TTSAdapter é abstrata e não pode ser instanciada diretamente."""
        with pytest.raises(TypeError):
            TTSAdapter()

    def test_tts_adapter_subclass_must_implement_methods(self):
        """Subclasses de TTSAdapter devem implementar métodos abstratos."""

        class IncompleteAdapter(TTSAdapter):
            pass

        with pytest.raises(TypeError):
            IncompleteAdapter()

    def test_tts_adapter_subclass_with_implementation(self):
        """Subclass completa de TTSAdapter pode ser instanciada."""

        class CompleteAdapter(TTSAdapter):
            async def synthesize(self, text: str, mode: VoiceMode = VoiceMode.NORMAL) -> AudioData:
                return AudioData(samples=b"\x00\x00", sample_rate=22050)

            async def speak(self, text: str, mode: VoiceMode = VoiceMode.NORMAL) -> None:
                pass

        adapter = CompleteAdapter()
        assert isinstance(adapter, TTSAdapter)


class TestGetTTSAdapter:
    """Testes para a fábrica get_tts_adapter()."""

    @patch("core.sky.voice.tts_adapter._ADapters")
    def test_get_tts_adapter_returns_kokoro_by_default(self, mock_adapters):
        """get_tts_adapter() deve retornar KokoroAdapter por padrão."""
        mock_kokoro = MagicMock(spec=TTSAdapter)
        mock_adapters.get.return_value = mock_kokoro

        adapter = get_tts_adapter()

        mock_adapters.get.assert_called_once_with("kokoro")
        assert adapter == mock_kokoro

    @patch("core.sky.voice.tts_adapter._adapters")
    def test_get_tts_adapter_respects_env_var(self, mock_adapters):
        """get_tts_adapter() deve respeitar a variável de ambiente TTS_BACKEND."""
        mock_custom = MagicMock(spec=TTSAdapter)
        mock_adapters.get.return_value = mock_custom

        adapter = get_tts_adapter(backend="custom")

        mock_adapters.get.assert_called_once_with("custom")
        assert adapter == mock_custom

    @patch("core.sky.voice.tts_adapter._adapters")
    def test_get_tts_adapter_fallback_to_kokoro(self, mock_adapters):
        """get_tts_adapter() deve fazer fallback para Kokoro se backend desconhecido."""
        mock_kokoro = MagicMock(spec=TTSAdapter)
        mock_adapters.get.return_value = None
        mock_adapters.__getitem__.return_value = mock_kokoro

        adapter = get_tts_adapter(backend="unknown")

        # Deve usar o primeiro adapter disponível como fallback
        assert adapter == mock_kokoro


class TestKokoroAdapter:
    """Testes para KokoroAdapter (implementação concreta)."""

    @pytest.fixture
    def mock_kokoro(self):
        """Fixture que cria um mock do KokoroAdapter."""
        from core.sky.voice.tts_adapter import KokoroAdapter

        with patch("core.sky.voice.tts_adapter.KOKORO_AVAILABLE", True):
            with patch("core.sky.voice.tts_adapter.KPipeline"):
                adapter = KokoroAdapter()
                yield adapter

    @pytest.mark.asyncio
    async def test_kokoro_synthesize_returns_audio_data(self, mock_kokoro):
        """KokoroAdapter.synthesize() deve retornar AudioData."""
        with patch.object(mock_kokoro, "_synthesize_sync") as mock_sync:
            mock_sync.return_value = AudioData(
                samples=b"\x00\x00\x00\x00",
                sample_rate=24000
            )

            result = await mock_kokoro.synthesize("teste", VoiceMode.NORMAL)

            assert isinstance(result, AudioData)
            assert result.sample_rate == 24000

    @pytest.mark.asyncio
    async def test_kokoro_speak_calls_synthesize_and_plays(self, mock_kokoro):
        """KokoroAdapter.speak() deve chamar synthesize e tocar áudio."""
        with patch.object(mock_kokoro, "synthesize") as mock_synthesize:
            with patch.object(mock_kokoro, "_play_audio") as mock_play:
                mock_synthesize.return_value = AudioData(
                    samples=b"\x00\x00",
                    sample_rate=24000
                )

                await mock_kokoro.speak("teste", VoiceMode.NORMAL)

                mock_synthesize.assert_called_once_with("teste", VoiceMode.NORMAL)
                mock_play.assert_called_once()
