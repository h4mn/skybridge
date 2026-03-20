"""TTS endpoint - Text-to-Speech usando Kokoro."""

from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.routing import Route
from typing import Any

from core.sky.voice.api.services.tts_service import get_tts_service
from core.sky.voice.tts_adapter import VoiceMode


async def tts_endpoint(request: Request) -> Response:
    """Sintetiza texto em áudio.

    POST /voice/tts
    Content-Type: application/json

    Response: audio/raw (bytes float32 @ 24000Hz)
    """
    service = get_tts_service()

    try:
        body = await request.json()
        text = body.get("text", "")
        mode_str = body.get("mode", "normal")

        if not text:
            return JSONResponse(
                {"error": "No text provided", "error_type": "missing_text"},
                status_code=400
            )

        # Valida modo
        if mode_str not in ("normal", "thinking"):
            # Retorna lista de modos válidos
            return JSONResponse(
                {
                    "error": f"Invalid mode: '{mode_str}'. Valid modes: 'normal', 'thinking'",
                    "error_type": "invalid_mode",
                    "valid_modes": ["normal", "thinking"]
                },
                status_code=400
            )

        # Converte mode string para VoiceMode enum
        mode = VoiceMode.THINKING if mode_str == "thinking" else VoiceMode.NORMAL

        # Sintetiza usando Kokoro
        audio_bytes = await service.synthesize(text, mode)

        return Response(
            audio_bytes,
            media_type="audio/raw",
            headers={
                "X-Sample-Rate": "24000",
                "X-Audio-Format": "float32",
                "X-Channels": "1"
            }
        )

    except ValueError as e:
        # Erro de validação (ex: voz inválida se implementado no futuro)
        error_msg = str(e)

        # Se o erro menciona voz, tenta obter lista de vozes disponíveis
        if "voice" in error_msg.lower():
            available_voices = _get_available_voices(service)
            return JSONResponse(
                {
                    "error": error_msg,
                    "error_type": "invalid_voice",
                    "available_voices": available_voices
                },
                status_code=400
            )

        return JSONResponse(
            {"error": error_msg, "error_type": "validation_error"},
            status_code=400
        )

    except Exception as e:
        return JSONResponse(
            {"error": str(e), "error_type": "internal_error"},
            status_code=500
        )


def _get_available_voices(service) -> list[str]:
    """Retorna lista de vozes disponíveis do TTS service.

    Args:
        service: Instância do TTSService

    Returns:
        Lista de nomes de vozes disponíveis
    """
    try:
        if service._adapter is not None:
            return service._adapter.get_available_voices()
    except Exception:
        pass

    # Fallback para lista padrão se adapter não disponível
    return ["af_heart", "af_sky", "af_bella", "sky-female"]


def get_tts_routes() -> list[Route]:
    """Retorna rotas do TTS endpoint."""
    return [
        Route("/voice/tts", tts_endpoint, methods=["POST"]),
    ]
