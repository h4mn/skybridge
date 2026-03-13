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


def _get_stages(use_rag: bool) -> list[Stage]:
    """
    Retorna lista de estágios baseado em configuração RAG.

    Args:
        use_rag: Se True, inclui estágios RAG (embedding, model_weights, vector_db, collections)

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

    stages.append(
        Stage("textual", "Iniciando interface...", weight=0.5)
    )

    return stages


def _stage_environment(progress: "Progress") -> None:
    """Estágio 1: Configuração do ambiente."""
    # PYTHONPATH já está configurado pelo sky.cmd
    # .env já foi carregado pelo sky_bootstrap.py
    pass


def _stage_embedding(progress: "Progress") -> None:
    """Estágio 2: Inicialização do cliente de embedding."""
    from core.sky.memory.embedding import get_embedding_client

    # Apenas inicializa o cliente (sem carregar o modelo ainda)
    _ = get_embedding_client()


def _stage_model_weights(progress: "Progress") -> None:
    """Estágio 3: Carregamento dos pesos do modelo."""
    from core.sky.memory.embedding import get_embedding_client
    from contextlib import redirect_stderr
    import io

    # Capturar stderr para ler progresso
    stderr_capture = io.StringIO()

    # Thread para mostrar progresso enquanto carrega
    stop_flag = [False]
    last_pct = [None]

    def show_progress():
        """Mostra progresso do modelo em tempo real."""
        pattern = re.compile(r'Loading weights:\s*(\d+)%')
        last_len = 0

        while not stop_flag[0]:
            content = stderr_capture.getvalue()
            matches = list(pattern.finditer(content))
            if matches:
                pct = matches[-1].group(1)
                if pct != last_pct[0]:
                    # Limpar linha anterior e mostrar novo percentual
                    clear = '\r' + ' ' * last_len + '\r'
                    print(f"{clear}Carregando pesos: {pct}%", end='', flush=True)
                    last_pct[0] = pct
                    last_len = len(f"Carregando pesos: {pct}%")
            time.sleep(0.03)

    # Iniciar thread de progresso
    progress_thread = threading.Thread(target=show_progress, daemon=True)
    progress_thread.start()

    try:
        with redirect_stderr(stderr_capture):
            # Força carregamento do modelo (lazy load)
            client = get_embedding_client()
            _ = client._get_model()
    finally:
        stop_flag[0] = True
        progress_thread.join(timeout=0.3)
        # Limpar linha
        print('\r' + ' ' * 50 + '\r', end='', flush=True)


def _stage_vector_db(progress: "Progress") -> None:
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


def _stage_collections(progress: "Progress") -> None:
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


def _stage_textual(progress: "Progress") -> None:
    """Estágio 5: Inicialização da interface Textual."""
    from core.sky.chat.textual_ui import SkyApp

    # Apenas importa para garantir que está disponível
    # A instância será criada pelo caller
    pass


def run(console: Optional["Console"] = None) -> "SkyApp":
    """
    Executa bootstrap do Sky Chat com barra de progresso.

    Orquestra o carregamento de todos os componentes em ordem,
    mostrando progresso visual e tempo de cada estágio.

    Args:
        console: Console Rich para output. Padrão: novo console.

    Returns:
        Instância de SkyApp pronta para executar.
    """
    # Configurar silenciamento de bibliotecas externas (antes de importar)
    _setup_external_libs()

    # Print inicial ANTES de importar Rich (usando print simples)
    print("Iniciando Sky Chat...", flush=True)

    # Import Rich e criar console
    from rich.console import Console
    console = console or Console()

    # Criar stages
    use_rag = USE_RAG_MEMORY
    stages = _get_stages(use_rag)

    # Criar progress
    progress = Progress(console)

    # Mapeamento de estágios para funções
    stage_functions = {
        "environment": _stage_environment,
        "embedding": _stage_embedding if use_rag else None,
        "model_weights": _stage_model_weights if use_rag else None,
        "vector_db": _stage_vector_db if use_rag else None,
        "collections": _stage_collections if use_rag else None,
        "textual": _stage_textual,
    }

    # Adicionar stages ao progress
    for stage in stages:
        progress.add_stage(stage)

    # Executar bootstrap
    with progress.run() as ctx:
        for stage in stages:
            func = stage_functions.get(stage.name)
            if func is not None:
                ctx.run_stage(stage.name, func, progress)

    # Importar e retornar SkyApp
    from core.sky.chat.textual_ui import SkyApp

    console.print("[bold green]✓ Sky Chat pronto![/bold green]")
    return SkyApp()
