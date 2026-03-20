"""Health endpoint - Status da Voice API."""

from starlette.responses import JSONResponse
from starlette.routing import Route

from core.sky.voice.api.models import HealthResponse, StartupStatus
from core.sky.voice.api.services.stt_service import startup_state


async def health_check(request) -> JSONResponse:
    """Retorna status atual da Voice API."""
    response = HealthResponse(
        status=startup_state.status,
        progress=startup_state.progress,
        message=startup_state.message,
        stage=startup_state.stage
    )
    return JSONResponse({
        "status": response.status.value,
        "progress": response.progress,
        "message": response.message,
        "stage": response.stage
    })


def get_health_routes() -> list[Route]:
    """Retorna rotas do health endpoint."""
    return [
        Route("/health", health_check, methods=["GET"]),
    ]
