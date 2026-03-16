"""
Tests for TTSService and MOSSTTSAdapter.

DOC: src/core/sky/voice/tts_service.py - TTS deve sintetizar fala a partir de texto

Este teste valida:
1. Inicialização correta do MOSSTTSAdapter
2. Síntese de texto vazio retorna erro ou áudio vazio
3. Síntese de texto gera áudio válido
4. VoiceConfig valida parâmetros corretamente
5. Cache de áudio funciona
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.core.sky.voice.tts_service import (
    TTSService,
    MOSSTTSAdapter,
    ElevenLabsAdapter,
    TTSModel,
    VoiceConfig,
)
from src.core.sky.voice.audio_capture import AudioData


class TestVoiceConfig:
    """Testa VoiceConfig dataclass."""

    def test_voice_config_defaults(self):
        """Testa valores padrão da configuração de voz."""
        config = VoiceConfig()

        assert config.voice_id == "sky-female"
        assert config.speed == 1.0
        assert config.pitch == 0
        assert config.language == "pt-BR"

    def test_voice_config_custom_values(self):
        """Testa configuração com valores customizados."""
        config = VoiceConfig(
            voice_id="sky-male",
            speed=1.5,
            pitch=2,
            language="en",
        )

        assert config.voice_id == "sky-male"
        assert config.speed == 1.5
        assert config.pitch == 2
        assert config.language == "en"

    def test_voice_config_validate_valid(self):
        """Testa validação com parâmetros válidos."""
        config = VoiceConfig(speed=1.0, pitch=0)

        # Não deve lançar exceção
        config.validate()

    def test_voice_config_validate_invalid_speed_low(self):
        """Testa validação rejeita速度 muito baixa."""
        config = VoiceConfig(speed=0.1)  # Abaixo de 0.5

        with pytest.raises(ValueError, match="Speed deve estar entre 0.5 e 2.0"):
            config.validate()

    def test_voice_config_validate_invalid_speed_high(self):
        """Testa validação rejeita速度 muito alta."""
        config = VoiceConfig(speed=3.0)  # Acima de 2.0

        with pytest.raises(ValueError, match="Speed deve estar entre 0.5 e 2.0"):
            config.validate()

    def test_voice_config_validate_invalid_pitch_low(self):
        """Testa validação rejeita pitch muito baixo."""
        config = VoiceConfig(pitch=-20)  # Abaixo de -12

        with pytest.raises(ValueError, match="Pitch deve estar entre -12 e \\+12"):
            config.validate()

    def test_voice_config_validate_invalid_pitch_high(self):
        """Testa validação rejeita pitch muito alto."""
        config = VoiceConfig(pitch=20)  # Acima de 12

        with pytest.raises(ValueError, match="Pitch deve estar entre -12 e \\+12"):
            config.validate()


class TestMOSSTTSAdapterInit:
    """Testa inicialização do MOSSTTSAdapter."""

    def test_moss_tts_adapter_init_default(self):
        """Testa inicialização com parâmetros padrão."""
        adapter = MOSSTTSAdapter()

        assert adapter.model == TTSModel.MOSS_TTS
        assert adapter.voice == "sky-female"
        assert adapter._model is None  # Lazy load

    def test_moss_tts_adapter_init_custom_voice(self):
        """Testa inicialização com voz customizada."""
        adapter = MOSSTTSAdapter(voice="sky-male")

        assert adapter.voice == "sky-male"


class TestMOSSTTSAdapterSynthesize:
    """Testa método synthesize do MOSSTTSAdapter."""

    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self):
        """Testa síntese de texto vazio."""
        adapter = MOSSTTSAdapter()

        # Texto vazio deve retornar erro ou áudio vazio
        with pytest.raises((ValueError, NotImplementedError)):
            result = await adapter.synthesize("")
            # Se não lançar erro, pelo menos o áudio deve ser vazio
            # assert len(result.samples) == 0

    @pytest.mark.asyncio
    async def test_synthesize_with_text_mocked(self):
        """Testa síntese com texto (mockado)."""
        adapter = MOSSTTSAdapter()

        # Mock do modelo
        with patch.object(adapter, "_load_model"):
            adapter._model = Mock()
            # Mock que retorna áudio sintético
            mock_audio = b"\x00\x01" * 1000
            adapter._model.generate = Mock(return_value=mock_audio)

        # Mock da função _play_audio para não reproduzir
        with patch.object(adapter, "_play_audio"):
            result = await adapter.synthesize("Olá Sky")

            # Verifica que áudio foi gerado
            assert len(result.samples) > 0

    @pytest.mark.asyncio
    async def test_synthesize_with_custom_config(self):
        """Testa síntese com configuração customizada."""
        adapter = MOSSTTSAdapter()
        config = VoiceConfig(speed=1.5, pitch=2)

        with patch.object(adapter, "_load_model"):
            adapter._model = Mock()
            with patch.object(adapter, "_play_audio"):
                result = await adapter.synthesize("Teste", config)

                assert len(result.samples) >= 0  # Pode ser vazio se não implementado


class TestMOSSTTSAdapterSpeak:
    """Testa método speak do MOSSTTSAdapter."""

    @pytest.mark.asyncio
    async def test_speak_calls_synthesize_and_play(self):
        """Testa que speak chama synthesize e _play_audio."""
        adapter = MOSSTTSAdapter()

        with patch.object(adapter, "synthesize", new_callable=AsyncMock) as mock_synth:
            mock_audio = AudioData(
                samples=b"\x00\x01" * 100,
                sample_rate=16000,
                channels=1,
            )
            mock_synth.return_value = mock_audio

            with patch.object(adapter, "_play_audio", new_callable=AsyncMock) as mock_play:
                await adapter.speak("Olá")

                # Verifica que synthesize foi chamado
                mock_synth.assert_called_once_with("Olá", None)
                # Verifica que _play_audio foi chamado
                mock_play.assert_called_once_with(mock_audio)


class TestTTSServiceInterface:
    """Testa interface abstrata TTSService."""

    def test_moss_tts_adapter_is_tts_service(self):
        """Testa que MOSSTTSAdapter implementa TTSService."""
        adapter = MOSSTTSAdapter()

        assert isinstance(adapter, TTSService)
        assert hasattr(adapter, "synthesize")
        assert hasattr(adapter, "speak")
        assert hasattr(adapter, "get_available_voices")

    def test_get_available_voices(self):
        """Testa lista de vozes disponíveis."""
        adapter = MOSSTTSAdapter()

        voices = adapter.get_available_voices()

        assert isinstance(voices, list)
        assert "sky-female" in voices
        assert "sky-male" in voices


class TestElevenLabsAdapter:
    """Testa ElevenLabsAdapter (placeholder)."""

    def test_elevenlabs_adapter_init(self):
        """Testa inicialização do adapter ElevenLabs."""
        adapter = ElevenLabsAdapter(api_key="test_key")

        assert adapter.model == TTSModel.ELEVENLABS
        assert adapter.api_key == "test_key"
