"""Voice API - Starlette app setup."""

from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware

from core.sky.voice.api.models import StartupStatus
from core.sky.voice.api.services.stt_service import startup_state, get_stt_service
from core.sky.voice.api.services.tts_service import get_tts_service
from core.sky.voice.api.endpoints.health import get_health_routes
from core.sky.voice.api.endpoints.stt import get_stt_routes
from core.sky.voice.api.endpoints.tts import get_tts_routes


@asynccontextmanager
async def lifespan(app: Starlette):
    """Lifecycle da aplicação."""

    # Startup
    startup_state.status = StartupStatus.STARTING
    startup_state.message = "Starting Voice API..."
    startup_state.progress = 0.0

    try:
        # Inicializa STT
        stt_service = get_stt_service()
        await stt_service.load_model()

        # Inicializa TTS (Kokoro)
        tts_service = get_tts_service()
        await tts_service.initialize()

        # Pronto!
        startup_state.status = StartupStatus.READY
        startup_state.message = "Voice API ready"
        startup_state.progress = 1.0
        startup_state.stage = None

        yield

    except Exception as e:
        startup_state.status = StartupStatus.ERROR
        startup_state.message = f"Startup failed: {e}"
        startup_state.error = str(e)
        raise

    finally:
        # Shutdown
        tts_service = get_tts_service()
        await tts_service.shutdown()


def create_app() -> Starlette:
    """Cria e retorna a aplicação Starlette.

    Usado para testes e para criar múltiplas instâncias se necessário.
    """
    app = Starlette(
        lifespan=lifespan,
        routes=[
            # Health
            *get_health_routes(),
            # STT
            *get_stt_routes(),
            # TTS
            *get_tts_routes(),
        ],
    )

    # Adiciona CORS (para desenvolvimento)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


# Cria app Starlette (instância global)
app = create_app()
