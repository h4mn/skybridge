# coding: utf-8
"""
Bootstrap - Orquestrador do carregamento do Sky Chat.

Coordena a inicialização de todos os componentes com feedback visual.
"""

import logging
import os
import re
import sys
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Optional

# Imports leves primeiro
from .stage import Stage
from .progress import Progress

# Feature flags
USE_RAG_MEMORY = os.getenv("USE_RAG_MEMORY", "false").lower() in ("true", "1", "yes")

# Voice API feature flag
USE_VOICE_API = os.getenv("SKYBRIDGE_VOICE_API_ENABLED", "0").lower() in ("1", "true", "yes")


def _setup_external_libs():
    """
    Configura silenciamento de bibliotecas externas para evitar poluição visual.

    Configura variáveis de ambiente e logging levels para silenciar:
    - sentence_transformers
    - torch
    - transformers
    - huggingface_hub

    Isso evita mensagens como:
    - "Warning: You are sending unauthenticated requests to the HF Hub"
    - "BertModel LOAD REPORT" (tabela verbose)
    """
    # Variáveis de ambiente
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # Logging do Python
    logging.getLogger("sentence_transformers").setLevel(logging.CRITICAL)
    logging.getLogger("torch").setLevel(logging.CRITICAL)
    logging.getLogger("transformers").setLevel(logging.CRITICAL)
    logging.getLogger("huggingface_hub").setLevel(logging.CRITICAL)


def _get_db_size_mb(db_path: Path) -> Optional[float]:
    """
    Calcula tamanho do banco em megabytes.

    Args:
        db_path: Caminho para o arquivo do banco.

    Returns:
        Tamanho em MB, ou None se arquivo não existir.
    """
    if db_path.exists():
        size_bytes = db_path.stat().st_size
        return size_bytes / (1024 * 1024)
    return None


def _get_collection_names() -> list[str]:
    """
    Retorna nomes das coleções RAG disponíveis.

    Returns:
        Lista de nomes de coleções.
    """
    return ["identity", "shared-moments", "teachings", "operational"]


def _get_stages(use_rag: bool, use_voice_api: bool) -> list[Stage]:
    """
    Retorna lista de estágios baseado em configuração RAG e Voice API.

    Args:
        use_rag: Se True, inclui estágios RAG (embedding, model_weights, vector_db, collections)
        use_voice_api: Se True, inclui estágio voice_api (Voice API isolada)

    Returns:
        Lista de estágios configurados.
    """
    stages = [
        Stage("environment", "Configurando ambiente...", weight=0.1),
    ]

    if use_rag:
        stages.extend([
            Stage("embedding", "Inicializando cliente de embedding...", weight=0.5),
            Stage("model_weights", "Carregando pesos do modelo...", weight=10.0),
            Stage("vector_db", "Inicializando banco vetorial...", weight=1.0),
            Stage("collections", "Configurando coleções...", weight=0.5),
        ])

    # Voice API - inicia subprocess isolado para STT/TTS
    # Deve vir antes do "textual" para estar pronto quando a UI iniciar
    if use_voice_api:
        stages.append(
            Stage("voice_api", "Inicializando Voice API...", weight=5.0)
        )

    stages.append(
        Stage("textual", "Iniciando interface...", weight=0.5)
    )

    return stages


def _stage_environment(progress: "Progress", ctx=None) -> None:
    """Estágio 1: Configuração do ambiente."""
    # PYTHONPATH já está configurado pelo sky.cmd
    # .env já foi carregado pelo sky_bootstrap.py
    pass


def _stage_embedding(progress: "Progress", ctx=None) -> None:
    """Estágio 2: Inicialização do cliente de embedding."""
    from core.sky.memory.embedding import get_embedding_client

    # Apenas inicializa o cliente (sem carregar o modelo ainda)
    _ = get_embedding_client()


_MODEL_WEIGHT_MSGS = [
    "Carregando pesos do modelo...",
    "Inicializando camadas de atenção...",
    "Preparando embeddings (384 dims)...",
    "Aquecendo self-attention heads...",
    "Compilando transformer layers...",
    "Mapeando vocabulário...",
    "Quase pronto...",
]


def _stage_model_weights(progress: "Progress", ctx: Optional["_ProgressContext"] = None) -> None:
    """Estágio: Carregamento dos pesos do modelo com progresso real do tqdm."""
    from core.sky.memory.embedding import get_embedding_client, set_progress_callback

    done_event = threading.Event()
    error_holder: list = [None]

    # Callback que será chamado pelo tqdm com a porcentagem real
    def _on_progress(percent: int) -> None:
        """Atualiza a descrição com a porcentagem real do tqdm."""
        if ctx is not None:
            ctx.update_stage_description("model_weights", f"Carregando pesos... {percent}%")

    # Define o callback para ser usado pelo _get_model
    set_progress_callback(_on_progress)

    def _load() -> None:
        try:
            client = get_embedding_client()
            client._get_model()  # força carregamento real (lazy)
        except Exception as exc:
            error_holder[0] = exc
        finally:
            done_event.set()

    load_thread = threading.Thread(target=_load, daemon=True)
    load_thread.start()

    # Aguarda o carregamento completar
    # O tqdm vai chamar _on_progress a cada atualização
    done_event.wait()

    # Limpa o callback
    set_progress_callback(None)

    load_thread.join(timeout=1.0)

    if error_holder[0] is not None:
        raise error_holder[0]


def _stage_vector_db(progress: "Progress", ctx=None) -> None:
    """Estágio 3: Inicialização do banco vetorial."""
    from core.sky.memory.vector_store import get_vector_store

    # Tamanho do banco
    from pathlib import Path
    data_dir = Path.home() / ".skybridge"
    db_path = data_dir / "sky_memory.db"
    size_mb = _get_db_size_mb(db_path)

    # Força inicialização do banco
    store = get_vector_store()

    # Atualiza descrição com tamanho
    stages = progress._stages
    for i, stage in enumerate(stages):
        if stage.name == "vector_db":
            stages[i] = stage.with_size_info(size_mb)
            break


def _stage_collections(progress: "Progress", ctx=None) -> None:
    """Estágio 4: Configuração das coleções."""
    from core.sky.memory.collections import get_collection_manager

    # Nomes das coleções
    collection_names = _get_collection_names()

    # Inicializa gerenciador de coleções
    manager = get_collection_manager()

    # Atualiza descrição com nomes
    stages = progress._stages
    for i, stage in enumerate(stages):
        if stage.name == "collections":
            stages[i] = stage.with_collections_info(collection_names)
            break


def _stage_textual(progress: "Progress", ctx=None) -> None:
    """Estágio: Inicialização da interface Textual."""
    from core.sky.chat.textual_ui import SkyApp

    # Apenas importa para garantir que está disponível
    # A instância será criada pelo caller
    pass


def _stage_voice_api(progress: "Progress", ctx=None) -> str:
    """
    Estágio: Inicialização da Voice API como subprocess isolado.

    DOC: openspec/changes/voice-api-isolation/tasks.md - Seções 12 e 13

    Este estágio:
    - Inicia a Voice API como subprocess separado
    - Aguarda until ready (polling /health)
    - Retorna URL da API para ser usada pelo MainScreen

    Returns:
        URL base da Voice API (ex: "http://127.0.0.1:8765")

    Raises:
        RuntimeError: Se Voice API falhar após retries
    """
    from .stages.voice_api import get_voice_api_stage

    stage = get_voice_api_stage()

    # Executa e retorna URL
    # O callback de progresso será usado internamente pelo stage
    voice_api_url = stage.execute(
        progress_update_callback=None,
        progress_context=ctx
    )

    if voice_api_url:
        logger.info(f"Voice API inicializada em {voice_api_url}")
    else:
        logger.info("Voice API desabilitada (feature flag OFF)")

    return voice_api_url


def run(console: Optional["Console"] = None, cold_start_start: Optional[float] = None, initial_print_done: bool = False) -> "SkyApp":
    """
    Executa bootstrap do Sky Chat com barra de progresso.

    Orquestra o carregamento de todos os componentes em ordem,
    mostrando progresso visual e tempo de cada estágio.

    Args:
        console: Console Rich para output. Padrão: novo console.
        cold_start_start: Timestamp de início do cold start (time.perf_counter()).
        initial_print_done: Se True, o print inicial já foi feito pelo caller.

    Returns:
        Instância de SkyApp pronta para executar.
    """
    # Configurar silenciamento de bibliotecas externas (antes de importar)
    _setup_external_libs()

    # MARK: Cold Start Timer - FIM (depois dos imports pesados)
    cold_start_end = time.perf_counter()
    cold_start_elapsed = cold_start_end - cold_start_start if cold_start_start else 0

    # Import Rich e criar console
    from rich.console import Console
    console = console or Console()

    # Atualiza o print inicial com formato Rich profissional
    if initial_print_done:
        # Limpa a linha simples e substitui com Rich formatado
        console.clear()
        if cold_start_elapsed > 0:
            console.print(f"[bold green]✓[/bold green] Carregando Sky Chat... [dim italic](cold start: {cold_start_elapsed*1000:.0f}ms)[/dim italic]")
        else:
            console.print("[bold green]✓[/bold green] Carregando Sky Chat...")
    else:
        if cold_start_elapsed > 0:
            console.print(f"[bold green]✓[/bold green] Iniciando Sky Chat... [dim italic](cold start: {cold_start_elapsed*1000:.0f}ms)[/dim italic]")
        else:
            console.print("[bold green]✓[/bold green] Iniciando Sky Chat...")
    # Criar stages
    use_rag = USE_RAG_MEMORY
    use_voice_api = USE_VOICE_API
    stages = _get_stages(use_rag, use_voice_api)

    # Criar progress
    progress = Progress(console)

    # Mapeamento de estágios para funções
    stage_functions = {
        "environment": _stage_environment,
        "embedding": _stage_embedding if use_rag else None,
        "model_weights": _stage_model_weights if use_rag else None,
        "vector_db": _stage_vector_db if use_rag else None,
        "collections": _stage_collections if use_rag else None,
        "voice_api": _stage_voice_api if use_voice_api else None,
        "textual": _stage_textual,
    }

    # Variável para armazenar URL da Voice API
    voice_api_url: Optional[str] = None

    # Adicionar stages ao progress
    for stage in stages:
        progress.add_stage(stage)

    # Executar bootstrap
    with progress.run() as ctx:
        for stage in stages:
            func = stage_functions.get(stage.name)
            if func is not None:
                result = ctx.run_stage(stage.name, func, progress, ctx)

                # Captura URL da Voice API
                if stage.name == "voice_api" and isinstance(result, str):
                    voice_api_url = result

    # Importar e retornar SkyApp
    from core.sky.chat.textual_ui import SkyApp

    console.print("[bold green][OK] Sky Chat pronto![/bold green]")

    # TODO: Passar voice_api_url para SkyApp quando a integração estiver pronta
    # Por ora, a URL será obtida via feature_toggle.get_voice_api_url()
    # Se necessário, adicionar parâmetro ao construtor do SkyApp

    # Registra cleanup da Voice API no shutdown
    _register_voice_api_cleanup()

    return SkyApp()


def _register_voice_api_cleanup() -> None:
    """
    Registra signal handlers para encerrar Voice API graciosamente no shutdown.

    DOC: openspec/changes/voice-api-isolation/tasks.md - 13.4

    Quando SkyChat receber SIGTERM/SIGINT:
    1. Envia SIGTERM para Voice API subprocess
    2. Aguarda até 5 segundos para shutdown graciosos
    3. Se não responder, envia SIGKILL
    """
    if not USE_VOICE_API:
        return

    def _cleanup_handler(signum, frame):
        """Handler para SIGTERM/SIGINT."""
        from .stages.voice_api import get_voice_api_stage

        stage = get_voice_api_stage()

        if stage.is_ready():
            logger.info("Encerrando Voice API (shutdown signal received)...")
            stage.shutdown(timeout=SHUTDOWN_TIMEOUT)

        # Re-leva signal para comportamento padrão
        import signal
        signal.signal(signum, signal.SIG_DFL)
        signal.raise_signal(signum)

    # Registra handlers
    if sys.platform == "win32":
        # Windows: SIGINT é o principal (CTRL+C)
        signal.signal(signal.SIGINT, _cleanup_handler)
    else:
        # Unix-like: SIGTERM e SIGINT
        signal.signal(signal.SIGTERM, _cleanup_handler)
        signal.signal(signal.SIGINT, _cleanup_handler)


# Constante para timeout de shutdown
SHUTDOWN_TIMEOUT = 5.0
