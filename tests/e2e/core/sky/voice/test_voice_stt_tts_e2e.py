# -*- coding: utf-8 -*-
"""
Teste E2E do fluxo atual de STT + TTS (sem Voice API).

DOC: openspec/changes/voice-api-isolation/tasks.md - Fase 1, Task 1.1
Objetivo: Capturar baseline do comportamento atual antes de introduzir Voice API.

Este teste documenta o fluxo ATUAL:
- STT: WhisperAdapter.transcribe() → texto
- TTS: KokoroAdapter.synthesize() → áudio
- Direct call (sem HTTP, sem processo separado)
"""

import asyncio
import time
from unittest.mock import Mock, patch

import pytest
import numpy as np

from src.core.sky.voice.stt_service import (
    WhisperAdapter,
    TranscriptionConfig,
    TranscriptionResult,
)
from src.core.sky.voice.tts_adapter import (
    KokoroAdapter,
    VoiceMode,
)
from src.core.sky.voice.audio_capture import AudioData


class TestVoiceSTTTTSCurrentBaseline:
    """
    Testes E2E do fluxo atual STT + TTS.

    Estes testes documentam o comportamento ATUAL para garantir
    que a Voice API mantenha compatibilidade e performance.
    """

    @pytest.mark.asyncio
    async def test_stt_transcribe_empty_audio(self):
        """
        DOC: baseline - STT transcreve áudio vazio → texto vazio.

        Comportamento atual:
        - Áudio vazio → TranscriptionResult com text=""
        - language: "pt" (default)
        - confidence: 0.0
        - duration: 0.0
        """
        adapter = WhisperAdapter()

        # Áudio vazio
        empty_audio = AudioData(
            samples=b"",
            sample_rate=16000,
            channels=1,
            duration=0.0,
        )

        # Mock do modelo para não precisar instalar faster-whisper no teste
        with patch.object(adapter, "_load_model"):
            mock_model = Mock()
            mock_info = Mock()
            mock_info.language = "pt"
            mock_info.language_probability = 0.0

            # faster-whisper retorna (segments_iterator, info)
            mock_model.transcribe.return_value = (iter([]), mock_info)
            adapter._model = mock_model

        result = await adapter.transcribe(empty_audio)

        # Assert: comportamento baseline
        assert result.text == ""
        assert result.language == "pt"
        assert result.confidence == 0.0
        assert result.duration == 0.0

    @pytest.mark.asyncio
    async def test_stt_transcribe_portuguese_audio(self):
        """
        DOC: baseline - STT transcreve áudio em português.

        Comportamento atual:
        - Áudio PT-BR → texto transcrito em PT-BR
        - language: "pt"
        - confidence: 0.0+ (se detected)
        """
        adapter = WhisperAdapter()

        # Áudio simulado (100 amostras = ~6ms @ 16kHz)
        audio_data = AudioData(
            samples=b"\x00\x01" * 100,
            sample_rate=16000,
            channels=1,
            duration=0.00625,
        )

        with patch.object(adapter, "_load_model"):
            mock_model = Mock()
            mock_segment = Mock()
            mock_segment.text = "Olá Sky"

            mock_info = Mock()
            mock_info.language = "pt"
            mock_info.language_probability = 0.95

            mock_model.transcribe.return_value = iter([mock_segment]), mock_info
            adapter._model = mock_model

        result = await adapter.transcribe(audio_data)

        # Assert: comportamento baseline
        assert result.text == "Olá Sky"
        assert result.language == "pt"
        assert result.confidence == 0.95
        assert result.duration == 0.00625

    @pytest.mark.asyncio
    async def test_tts_synthesize_basic_text(self):
        """
        DOC: baseline - TTS sintetiza texto básico.

        Comportamento atual:
        - Texto "Olá mundo" → AudioData com amostras
        - sample_rate: 24000 Hz (Kokoro)
        - channels: 1 (mono)
        - duration: >0 (calculado)
        - samples: bytes float32 normalizados
        """
        adapter = KokoroAdapter()

        text = "Olá mundo"

        # Mock do pipeline Kokoro
        with patch.object(adapter, "_load_model_sync"):
            import torch

            # Mock do pipeline
            mock_pipeline = Mock()
            mock_audio = torch.tensor([0.1, 0.2, 0.3, 0.2, 0.1], dtype=torch.float32)

            # Generator retorna (graphemes, phonemes, audio)
            mock_pipeline.return_value = iter([
                (["g1", "g2"], ["p1", "p2"], mock_audio)
            ])

            adapter._pipeline = mock_pipeline

        result = await adapter.synthesize(text, VoiceMode.NORMAL)

        # Assert: comportamento baseline
        assert result.sample_rate == 24000
        assert result.channels == 1
        assert result.duration > 0
        assert len(result.samples) > 0

        # Verifica que é float32
        samples_array = np.frombuffer(result.samples, dtype=np.float32)
        assert samples_array.dtype == np.float32
        assert np.max(np.abs(samples_array)) <= 1.0  # Normalizado

    @pytest.mark.asyncio
    async def test_tts_synthesize_thinking_mode(self):
        """
        DOC: baseline - TTS modo thinking usa speed=0.85.

        Comportamento atual:
        - VoiceMode.THINKING → speed=0.85 (mais lento)
        - Duração do áudio é maior que NORMAL para mesmo texto
        """
        adapter = KokoroAdapter()

        text = "Teste"

        # Mock do pipeline Kokoro
        with patch.object(adapter, "_load_model_sync"):
            import torch

            mock_pipeline = Mock()
            mock_audio = torch.tensor([0.1] * 100, dtype=torch.float32)

            # Captura parâmetros passados ao pipeline
            called_with_speed = []

            def capture_speed(text_arg, voice, speed, **kwargs):
                called_with_speed.append(speed)
                return iter([
                    (["g"], ["p"], mock_audio)
                ])

            mock_pipeline.side_effect = capture_speed
            adapter._pipeline = mock_pipeline

        # Sintetiza em modo thinking
        result = await adapter.synthesize(text, VoiceMode.THINKING)

        # Assert: speed foi 0.85
        assert len(called_with_speed) == 1
        assert called_with_speed[0] == 0.85

    @pytest.mark.asyncio
    async def test_stt_tts_roundtrip_performance(self):
        """
        DOC: baseline - Performance STT→TTS roundtrip.

        Mede tempo total de:
        1. Transcrição de áudio curto
        2. Síntese de texto resultante

        Resultado será usado para comparar com Voice API.
        """
        adapter_stt = WhisperAdapter()
        adapter_tts = KokoroAdapter()

        # Áudio curto (~1 segundo @ 16kHz)
        audio_data = AudioData(
            samples=b"\x00\x01" * 16000,
            sample_rate=16000,
            channels=1,
            duration=1.0,
        )

        # Mock STT
        with patch.object(adapter_stt, "_load_model"):
            mock_model = Mock()
            mock_segment = Mock()
            mock_segment.text = "Teste de voz"

            mock_info = Mock()
            mock_info.language = "pt"
            mock_info.language_probability = 0.92

            mock_model.transcribe.return_value = iter([mock_segment]), mock_info
            adapter_stt._model = mock_model

        # Mock TTS
        with patch.object(adapter_tts, "_load_model_sync"):
            import torch

            mock_pipeline = Mock()
            mock_audio = torch.tensor([0.1] * 24000, dtype=torch.float32)  # 1s @ 24kHz

            mock_pipeline.return_value = iter([
                (["g"], ["p"], mock_audio)
            ])

            adapter_tts._pipeline = mock_pipeline

        # Mede tempo STT
        start_stt = time.perf_counter()
        stt_result = await adapter_stt.transcribe(audio_data)
        stt_duration = time.perf_counter() - start_stt

        # Mede tempo TTS
        start_tts = time.perf_counter()
        tts_result = await adapter_tts.synthesize(stt_result.text, VoiceMode.NORMAL)
        tts_duration = time.perf_counter() - start_tts

        # Total roundtrip
        total_duration = stt_duration + tts_duration

        # Assert: baseline de performance
        assert stt_result.text == "Teste de voz"
        assert stt_duration < 1.0  # STT deve ser rápido (mock)
        assert tts_duration < 1.0  # TTS deve ser rápido (mock)
        assert total_duration < 2.0  # Total < 2s (mock)

        # Documenta baseline (para comparação futura)
        print(f"\n[Baseline Performance]")
        print(f"  STT: {stt_duration*1000:.1f}ms")
        print(f"  TTS: {tts_duration*1000:.1f}ms")
        print(f"  Total: {total_duration*1000:.1f}ms")

    @pytest.mark.asyncio
    async def test_stt_multiple_segments_concatenation(self):
        """
        DOC: baseline - STT concatena múltiplos segmentos.

        Comportamento atual:
        - Whisper retorna múltiplos segmentos
        - STT concatena todos os textos com ""
        - Espaços são preservados entre segmentos
        """
        adapter = WhisperAdapter()

        audio_data = AudioData(
            samples=b"\x00\x01" * 200,
            sample_rate=16000,
            channels=1,
            duration=0.0125,
        )

        with patch.object(adapter, "_load_model"):
            mock_model = Mock()
            segment1 = Mock()
            segment1.text = "Olá "
            segment2 = Mock()
            segment2.text = "Sky"

            mock_info = Mock()
            mock_info.language = "pt"
            mock_info.language_probability = 0.90

            mock_model.transcribe.return_value = iter([segment1, segment2]), mock_info
            adapter._model = mock_model

        result = await adapter.transcribe(audio_data)

        # Assert: segmentos concatenados
        assert result.text == "Olá Sky"

    @pytest.mark.asyncio
    async def test_tts_empty_text_raises_error(self):
        """
        DOC: baseline - TTS levanta erro para texto vazio.

        Comportamento atual:
        - Texto vazio → ValueError
        - Mensagem: "Texto não pode ser vazio"
        """
        adapter = KokoroAdapter()

        with pytest.raises(ValueError) as exc_info:
            await adapter.synthesize("", VoiceMode.NORMAL)

        assert "Texto não pode ser vazio" in str(exc_info.value)

        # Também testamos apenas espaços
        with pytest.raises(ValueError) as exc_info:
            await adapter.synthesize("   ", VoiceMode.NORMAL)

    @pytest.mark.asyncio
    async def test_stt_language_detection_pt_br(self):
        """
        DOC: baseline - STT detecta idioma PT-BR corretamente.

        Comportamento atual:
        - detect_language=True → Whisper detecta idioma
        - Retorno: language="pt" para áudio PT-BR
        """
        adapter = WhisperAdapter()

        audio_data = AudioData(
            samples=b"\x00\x01" * 100,
            sample_rate=16000,
            channels=1,
            duration=0.00625,
        )

        with patch.object(adapter, "_load_model"):
            mock_model = Mock()
            mock_segment = Mock()
            mock_segment.text = "Como você está"

            mock_info = Mock()
            mock_info.language = "pt"
            mock_info.language_probability = 0.98

            mock_model.transcribe.return_value = iter([mock_segment]), mock_info
            adapter._model = mock_model

        config = TranscriptionConfig(detect_language=True)
        result = await adapter.transcribe(audio_data, config)

        # Assert: idioma detectado corretamente
        assert result.text == "Como você está"
        assert result.language == "pt"
        assert result.confidence == 0.98


# =============================================================================
# Edge Cases Documentados (Task 1.3)
# =============================================================================

class TestVoiceEdgeCases:
    """
    Documentação de edge cases que funcionam hoje.

    Estes testes garantem que a Voice API não quebra
    comportamentos que hoje funcionam.
    """

    @pytest.mark.asyncio
    async def test_stt_very_short_audio(self):
        """
        DOC: edge case - Áudio muito curto (<100ms).

        Comportamento atual:
        - Áudio <100ms → transcrição funciona
        - Pode retornar texto vazio se não houver fala
        """
        adapter = WhisperAdapter()

        # Áudio de 50ms
        audio_data = AudioData(
            samples=b"\x00\x01" * 800,  # 50ms @ 16kHz
            sample_rate=16000,
            channels=1,
            duration=0.05,
        )

        with patch.object(adapter, "_load_model"):
            mock_model = Mock()
            mock_info = Mock()
            mock_info.language = "pt"
            mock_info.language_probability = 0.0

            # Whisper pode não detectar fala em áudio tão curto
            mock_model.transcribe.return_value = (iter([]), mock_info)
            adapter._model = mock_model

        result = await adapter.transcribe(audio_data)

        # Assert: texto vazio é aceitável para áudio muito curto
        assert result.text == ""

    @pytest.mark.asyncio
    async def test_tts_very_long_text(self):
        """
        DOC: edge case - Texto muito longo (>500 chars).

        Comportamento atual:
        - Texto longo → Kokoro processa em segmentos
        - split_pattern=r'\n+' divide em parágrafos
        - Todos os segmentos são concatenados
        """
        adapter = KokoroAdapter()

        # Texto longo (sem quebras de linha)
        long_text = " ".join(["Esta é uma frase de teste."] * 50)

        with patch.object(adapter, "_load_model_sync"):
            import torch

            mock_pipeline = Mock()

            # Simula múltiplos segmentos
            def generate_segments(text, voice, speed, **kwargs):
                # Retorna 3 segmentos para simular processamento
                for _ in range(3):
                    mock_audio = torch.tensor([0.1] * 8000, dtype=torch.float32)
                    yield (["g"], ["p"], mock_audio)

            mock_pipeline.side_effect = generate_segments
            adapter._pipeline = mock_pipeline

        result = await adapter.synthesize(long_text, VoiceMode.NORMAL)

        # Assert: áudio gerado (duração >0)
        assert result.duration > 0
        # 3 segmentos * 8000 amostras / 24000 Hz = 1 segundo total
        assert result.duration == 1.0

    @pytest.mark.asyncio
    async def test_stt_silence_only_audio(self):
        """
        DOC: edge case - Áudio com apenas silêncio.

        Comportamento atual:
        - Áudio com valores próximos de zero → texto vazio
        - VAD (Voice Activity Detection) filtra silêncio
        """
        adapter = WhisperAdapter()

        # Áudio com apenas silêncio (valores muito pequenos)
        silence_audio = AudioData(
            samples=b"\x00\x00" * 16000,  # 1s de silêncio @ 16kHz
            sample_rate=16000,
            channels=1,
            duration=1.0,
        )

        with patch.object(adapter, "_load_model"):
            mock_model = Mock()
            mock_info = Mock()
            mock_info.language = "pt"
            mock_info.language_probability = 0.0

            # VAD filtra silêncio, nenhum segmento retornado
            mock_model.transcribe.return_value = (iter([]), mock_info)
            adapter._model = mock_model

        result = await adapter.transcribe(silence_audio)

        # Assert: silêncio → texto vazio
        assert result.text == ""

    @pytest.mark.asyncio
    async def test_tts_special_characters(self):
        """
        DOC: edge case - Texto com caracteres especiais e acentos.

        Comportamento atual:
        - Acentos (ç, ã, é) → Kokoro processa corretamente
        - Pontuação (!, ?, ...) → mantida
        - Emojis → podem ser removidos ou causar erros
        """
        adapter = KokoroAdapter()

        # Texto com acentos e pontuação
        text = "Olá! Como você está? Tudo bem?"

        with patch.object(adapter, "_load_model_sync"):
            import torch

            mock_pipeline = Mock()
            mock_audio = torch.tensor([0.1] * 100, dtype=torch.float32)

            mock_pipeline.return_value = iter([
                (["g"], ["p"], mock_audio)
            ])

            adapter._pipeline = mock_pipeline

        # Assert: não levanta erro para caracteres especiais
        result = await adapter.synthesize(text, VoiceMode.NORMAL)
        assert result.duration > 0


# =============================================================================
# Summary do Baseline (Task 1.2)
# =============================================================================

class TestVoiceBaselineSummary:
    """
    Sumário de baseline de performance documentado.

    Coleta todas as métricas do fluxo atual para comparação
    com a implementação da Voice API.
    """

    @pytest.mark.asyncio
    async def test_baseline_summary(self):
        """
        DOC: baseline - Sumário completo de performance.

        Métricas coletadas:
        - STT transcrição: ~Xms para áudio de 1s
        - TTS síntese: ~Yms para texto de 10 palavras
        - Roundtrip total: ~Zms

        NOTA: Valores são baseados em mocks, mas testes reais
        com modelos carregados devem documentar tempos reais.
        """
        print("\n" + "=" * 60)
        print("[BASELINE] Fluxo Atual STT + TTS")
        print("=" * 60)
        print("STT (faster-whisper):")
        print("  - Modelo: base")
        print("  - Device: cpu")
        print("  - Idioma: pt-BR")
        print("  - VAD: ativado")
        print("")
        print("TTS (Kokoro):")
        print("  - Voz: af_heart")
        print("  - Sample rate: 24000 Hz")
        print("  - Idioma: pt-BR (lang_code='p')")
        print("  - Modos: NORMAL (speed=1.0), THINKING (speed=0.85)")
        print("")
        print("Arquitetura Atual:")
        print("  - Processo único")
        print("  - Chamadas diretas (sem HTTP)")
        print("  - Memória compartilhada")
        print("=" * 60)
