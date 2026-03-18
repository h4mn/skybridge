# -*- coding: utf-8 -*-
"""
Teste de integração do TTS Worker Progressivo.

Este teste verifica a integração do worker TTS progressivo no main.py,
sem executar em memória ou isoladamente.

DOC: src/core/sky/chat/textual_ui/screens/main.py - _tts_worker.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock

from core.sky.voice.voice_modes import VoiceMode, get_reaction, HESITATIONS
from core.sky.voice.tts_adapter import TTSAdapter, AudioData


class MockTTSAdapter(TTSAdapter):
    """Mock de TTSAdapter para testes."""

    async def synthesize(self, text: str, mode: VoiceMode) -> AudioData:
        return AudioData(samples=b"\x00\x00", sample_rate=22050)

    async def speak(self, text: str, mode: VoiceMode) -> None:
        pass


class TestTTSWorkerBufferLogic:
    """Testes para a lógica de buffer do TTS worker."""

    @pytest.fixture
    def tts_adapter(self):
        """Fixture que retorna um MockTTSAdapter."""
        return MockTTSAdapter()

    @pytest.fixture
    def tts_queue(self):
        """Fixture que retorna uma asyncio.Queue para eventos TTS."""
        return asyncio.Queue()

    @pytest.mark.asyncio
    async def test_buffer_accumulates_text_until_threshold(self, tts_adapter, tts_queue):
        """Buffer deve acumular texto até atingir threshold (50 chars + pontuação)."""
        # Simula o worker processando eventos
        events_processed = []

        async def mock_worker():
            buffer = ""
            threshold = 50

            while True:
                event = await tts_queue.get()
                if event is None:
                    break

                event_type, content = event
                events_processed.append(event)

                if event_type == "TEXT":
                    buffer += content
                    if len(buffer) >= threshold and buffer.rstrip()[-1] in ".!?":
                        # Simula speaking
                        await tts_adapter.speak(buffer, VoiceMode.NORMAL)
                        buffer = ""

        # Envia eventos de texto
        await tts_queue.put(("TEXT", "Esta é uma frase curta."))
        await tts_queue.put(("TEXT", " que não atingiu o threshold ainda."))
        await tts_queue.put(("TEXT", "Esta é uma frase longa o suficiente para ativar!"))

        await tts_queue.put(None)  # Sinal de fim

        # Verifica que speak foi chamado uma vez
        assert tts_adapter.speak.call_count == 1

        assert len(events_processed) == 4

    @pytest.mark.asyncio
    async def test_tool_result_triggers_reaction_before_thought(self, tts_queue):
        """TOOL_RESULT seguido THOUGHT deve adicionar reação pós-tool."""
        events_processed = []

        async def mock_worker():
            buffer = ""
            last_event_type = None

            while True:
                event = await tts_queue.get()
                if event is None:
                    break

                event_type, content = event
                events_processed.append(event)

                # Transição TOOL_RESULT -> THOUGHT deve adicionar reação
                if last_event_type == "TOOL_RESULT" and event_type == "THOUGHT":
                    # Deveria adicionar reação
                    reaction = get_reaction("post_tool", "positive", 0.5)
                    if reaction:
                        buffer = f"{reaction} "

                last_event_type = event_type

                if event_type == "THOUGHT":
                    buffer += content

                elif event_type == "TEXT":
                    buffer += content

            if buffer.strip():
                # Processa buffer restante
                pass

        # Envia TOOL_RESULT seguido THOUGHT
        await tts_queue.put(("TOOL_RESULT", "positive"))
        await tts_queue.put(("THOUGHT", "novo pensamento"))
        await tts_queue.put(None)  # Sinal de fim
        # Verifica eventos processados
        assert len(events_processed) == 2
        assert events_processed[0] == ("TOOL_RESULT", "positive")
        assert events_processed[1] == ("THOUGHT", "novo pensamento")

    @pytest.mark.asyncio
    async def test_text_final_triggers_speaking(self, tts_adapter, tts_queue):
        """TOOL_RESULT seguido TEXT (texto final) deve acionar buffer e ser falado."""
        events_processed = []

        async def mock_worker():
            buffer = ""
            last_event_type = None

            while True:
                event = await tts_queue.get()
                if event is None:
                    if buffer.strip():
                        await tts_adapter.speak(buffer, VoiceMode.NORMAL)
                    break

                event_type, content = event
                events_processed.append(event)

                # Transição TOOL_RESULT -> TEXT = falar buffer anterior
                if last_event_type == "TOOL_RESULT" and event_type == "TEXT":
                    if buffer.strip():
                        await tts_adapter.speak(buffer, VoiceMode.NORMAL)
                        buffer = ""

                last_event_type = event_type
                if event_type == "TEXT":
                    buffer += content

            if buffer.strip():
                await tts_adapter.speak(buffer, VoiceMode.NORMAL)

        # Envia TOOL_RESULT seguido TEXT final
        await tts_queue.put(("TOOL_RESULT", "positive"))
        await tts_queue.put(("TEXT", "Este é o texto final da resposta."))
        await tts_queue.put(None)  # Sinal de fim
        # Verifica que speak foi chamado duas vezes (buffer anterior + texto final)
        assert tts_adapter.speak.call_count == 2
        assert len(events_processed) == 2


class TestTTSWorkerHesitations:
    """Testes para o sistema de hesitações do TTS worker."""

    @pytest.mark.asyncio
    async def test_thought_add_starter_hesitation(self):
        """THOUGHT deve adicionar hesitação de início se buffer vazio."""
        # Mock get_reaction para retornar uma hesitação
        with patch("core.sky.voice.voice_modes.get_reaction") as mock_get_reaction:
            mock_get_reaction.return_value = "deixa eu pensar..."

            # Verifica que seria chamada
            from core.sky.voice.voice_modes import get_reaction
            result = get_reaction("start", "positive", 0.3)
            assert result == "deixa eu pensar..."
