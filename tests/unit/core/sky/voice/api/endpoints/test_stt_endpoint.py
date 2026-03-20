# -*- coding: utf-8 -*-
"""
Testes do STT endpoint da Voice API.

DOC: openspec/changes/voice-api-isolation/tasks.md - Fase 5, Task 5.6
Testes do endpoint POST /voice/stt usando TestClient do Starlette.
"""

import pytest
import io
from unittest.mock import Mock, AsyncMock, patch
from starlette.testclient import TestClient
from starlette.datastructures import UploadFile

from core.sky.voice.api.app import create_app
from core.sky.voice.api.services.stt_service import get_stt_service


@pytest.fixture
def test_client():
    """Retorna TestClient para a Voice API."""
    return TestClient(create_app())


@pytest.fixture
def mock_stt_service():
    """Mock do STTService."""
    mock_service = Mock()
    mock_service.transcribe = AsyncMock(return_value="Olá Sky")

    with patch("src.core.sky.voice.api.endpoints.stt.get_stt_service", return_value=mock_service):
        yield mock_service


class TestSTTEndpointMultipart:
    """Testes do endpoint com multipart/form-data."""

    def test_stt_endpoint_multipart_success(self, test_client, mock_stt_service):
        """Testa transcrição bem-sucedida com multipart/form-data."""
        # Áudio simulado em formato WAV (header simples)
        audio_data = b"RIFF" + b"\x00" * 100 + b"WAVE"

        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = test_client.post("/voice/stt", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Olá Sky"
        assert data["language"] == "pt"
        mock_stt_service.transcribe.assert_called_once()

    def test_stt_endpoint_multipart_no_audio_file(self, test_client, mock_stt_service):
        """Testa erro quando arquivo não é enviado."""
        response = test_client.post("/voice/stt", files={})

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "missing_audio"
        mock_stt_service.transcribe.assert_not_called()

    def test_stt_endpoint_multipart_empty_file(self, test_client, mock_stt_service):
        """Testa erro quando arquivo está vazio."""
        files = {"audio": ("empty.wav", io.BytesIO(b""), "audio/wav")}

        response = test_client.post("/voice/stt", files=files)

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "empty_audio"
        mock_stt_service.transcribe.assert_not_called()

    def test_stt_endpoint_multipart_no_filename(self, test_client, mock_stt_service):
        """Testa erro quando arquivo não tem nome."""
        # UploadFile sem filename
        files = {"audio": (None, io.BytesIO(b"audio data"), "audio/wav")}

        response = test_client.post("/voice/stt", files=files)

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "invalid_file"

    def test_stt_endpoint_multipart_with_mp3(self, test_client, mock_stt_service):
        """Testa transcrição com arquivo MP3."""
        audio_data = b"\xFF\xFB" + b"\x00" * 100  # MP3 header simplificado

        files = {"audio": ("test.mp3", io.BytesIO(audio_data), "audio/mpeg")}

        response = test_client.post("/voice/stt", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Olá Sky"

    def test_stt_endpoint_multipart_with_ogg(self, test_client, mock_stt_service):
        """Testa transcrição com arquivo OGG."""
        audio_data = b"OggS" + b"\x00" * 100  # OGG header simplificado

        files = {"audio": ("test.ogg", io.BytesIO(audio_data), "audio/ogg")}

        response = test_client.post("/voice/stt", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Olá Sky"


class TestSTTEndpointJSONBase64:
    """Testes do endpoint com JSON + base64 (POC/compatibilidade)."""

    def test_stt_endpoint_json_base64_success(self, test_client, mock_stt_service):
        """Testa transcrição bem-sucedida com JSON + base64."""
        import base64

        audio_bytes = b"\x00" * 1000  # Áudio simulado
        audio_b64 = base64.b64encode(audio_bytes).decode()

        response = test_client.post(
            "/voice/stt",
            json={"audio": audio_b64},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Olá Sky"
        assert data["language"] == "pt"

    def test_stt_endpoint_json_base64_no_audio(self, test_client, mock_stt_service):
        """Testa erro quando campo 'audio' não está presente."""
        response = test_client.post(
            "/voice/stt",
            json={},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "missing_audio"

    def test_stt_endpoint_json_base64_empty(self, test_client, mock_stt_service):
        """Testa erro quando campo 'audio' está vazio."""
        response = test_client.post(
            "/voice/stt",
            json={"audio": ""},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "missing_audio"

    def test_stt_endpoint_json_base64_invalid(self, test_client, mock_stt_service):
        """Testa erro quando base64 é inválido."""
        response = test_client.post(
            "/voice/stt",
            json={"audio": "not-valid-base64!@#"},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "invalid_encoding"


class TestSTTEndpointErrors:
    """Testes de tratamento de erros do endpoint."""

    def test_stt_endpoint_empty_audio_error(self, test_client, mock_stt_service):
        """Testa AudioEmptyError retorna 400."""
        from core.sky.voice.api.services.stt_service import AudioEmptyError

        mock_stt_service.transcribe.side_effect = AudioEmptyError("Áudio vazio")

        audio_data = b"\x00" * 100
        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = test_client.post("/voice/stt", files=files)

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "empty_audio"
        assert "Áudio vazio" in data["error"]

    def test_stt_endpoint_too_short_error(self, test_client, mock_stt_service):
        """Testa AudioTooShortError retorna 400."""
        from core.sky.voice.api.services.stt_service import AudioTooShortError

        mock_stt_service.transcribe.side_effect = AudioTooShortError("0.1s")

        audio_data = b"\x00" * 100
        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = test_client.post("/voice/stt", files=files)

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "audio_too_short"

    def test_stt_endpoint_invalid_format_error(self, test_client, mock_stt_service):
        """Testa InvalidAudioFormatError retorna 400."""
        from core.sky.voice.api.services.stt_service import InvalidAudioFormatError

        mock_stt_service.transcribe.side_effect = InvalidAudioFormatError("wav")

        audio_data = b"\x00" * 100
        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = test_client.post("/voice/stt", files=files)

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "invalid_format"

    def test_stt_endpoint_transcription_error(self, test_client, mock_stt_service):
        """Testa STTError retorna 500."""
        from core.sky.voice.api.services.stt_service import STTError

        mock_stt_service.transcribe.side_effect = STTError("Model failed")

        audio_data = b"\x00" * 100
        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = test_client.post("/voice/stt", files=files)

        assert response.status_code == 500
        data = response.json()
        assert data["error_type"] == "transcription_error"

    def test_stt_endpoint_invalid_json(self, test_client, mock_stt_service):
        """Testa JSON inválido retorna 400."""
        response = test_client.post(
            "/voice/stt",
            content=b"not json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error_type"] == "invalid_json"


class TestSTTEndpointEmptyResult:
    """Testes quando transcrição retorna vazio."""

    def test_stt_endpoint_no_speech_detected(self, test_client, mock_stt_service):
        """Testa que nenhuma fala detectada retorna texto vazio."""
        mock_stt_service.transcribe.return_value = ""

        audio_data = b"\x00" * 1000
        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = test_client.post("/voice/stt", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == ""
        assert data["language"] == "pt"


class TestSTTEndpointContentTypeDetection:
    """Testes de detecção de Content-Type."""

    def test_stt_endpoint_detects_multipart(self, test_client, mock_stt_service):
        """Testa que multipart é detectado corretamente."""
        audio_data = b"\x00" * 100
        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = test_client.post(
            "/voice/stt",
            files=files,
            headers={"Content-Type": "multipart/form-data; boundary=----WebKitFormBoundary"}
        )

        assert response.status_code == 200
        mock_stt_service.transcribe.assert_called_once()

    def test_stt_endpoint_defaults_to_json(self, test_client, mock_stt_service):
        """Testa que sem Content-Type, tenta JSON."""
        import base64

        audio_bytes = b"\x00" * 100
        audio_b64 = base64.b64encode(audio_bytes).decode()

        # Sem Content-Type header
        response = test_client.post("/voice/stt", json={"audio": audio_b64})

        assert response.status_code == 200
        mock_stt_service.transcribe.assert_called_once()
