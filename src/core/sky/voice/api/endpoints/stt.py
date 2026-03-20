"""STT endpoint - Speech-to-Text."""

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.datastructures import UploadFile

from core.sky.voice.api.services.stt_service import (
    get_stt_service,
    AudioEmptyError,
    AudioTooShortError,
    InvalidAudioFormatError,
    STTError,
)


async def stt_endpoint(request: Request) -> JSONResponse:
    """Transcreve áudio para texto.

    POST /voice/stt
    Content-Type: multipart/form-data OU application/json (POC)

    Suporta dois formatos:
    1. multipart/form-data com campo 'audio' (conforme spec)
    2. JSON com campo 'audio' em base64 (POC, compatibilidade)
    """
    service = get_stt_service()

    try:
        # Tenta multipart/form-data primeiro (conforme spec)
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            # Parsing de multipart/form-data
            form = await request.form()
            audio_file: UploadFile | None = form.get("audio")

            if audio_file is None:
                return JSONResponse(
                    {"error": "No audio file provided", "error_type": "missing_audio"},
                    status_code=400
                )

            if not audio_file.filename:
                return JSONResponse(
                    {"error": "Audio file has no filename", "error_type": "invalid_file"},
                    status_code=400
                )

            # Lê bytes do arquivo
            audio_bytes = await audio_file.read()

            if not audio_bytes:
                return JSONResponse(
                    {"error": "Audio file is empty", "error_type": "empty_audio"},
                    status_code=400
                )

        else:
            # Fallback para JSON com base64 (POC, compatibilidade)
            try:
                body = await request.json()
            except Exception as e:
                return JSONResponse(
                    {"error": f"Invalid JSON: {e}", "error_type": "invalid_json"},
                    status_code=400
                )

            audio_b64 = body.get("audio", "")

            if not audio_b64:
                return JSONResponse(
                    {"error": "No audio provided", "error_type": "missing_audio"},
                    status_code=400
                )

            # Decodifica base64
            import base64
            try:
                audio_bytes = base64.b64decode(audio_b64)
            except Exception as e:
                return JSONResponse(
                    {"error": f"Invalid base64 encoding: {e}", "error_type": "invalid_encoding"},
                    status_code=400
                )

        # Transcreve
        text = await service.transcribe(audio_bytes)

        return JSONResponse({
            "text": text,
            "language": "pt"
        })

    except AudioEmptyError as e:
        return JSONResponse(
            {"error": str(e), "error_type": "empty_audio"},
            status_code=400
        )
    except AudioTooShortError as e:
        return JSONResponse(
            {"error": str(e), "error_type": "audio_too_short"},
            status_code=400
        )
    except InvalidAudioFormatError as e:
        return JSONResponse(
            {"error": str(e), "error_type": "invalid_format"},
            status_code=400
        )
    except STTError as e:
        return JSONResponse(
            {"error": str(e), "error_type": "transcription_error"},
            status_code=500
        )
    except Exception as e:
        return JSONResponse(
            {"error": f"Unexpected error: {e}", "error_type": "internal_error"},
            status_code=500
        )


def get_stt_routes() -> list[Route]:
    """Retorna rotas do STT endpoint."""
    return [
        Route("/voice/stt", stt_endpoint, methods=["POST"]),
    ]
