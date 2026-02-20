# -*- coding: utf-8 -*-
"""
pytest configuration for Skybridge tests.

Adds src directory to Python path and loads environment variables.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
import pytest
from unittest.mock import AsyncMock, Mock

# Load environment variables from .env
load_dotenv()

# NOTA: pytest_asyncio configurado via pytest.ini (asyncio_mode = auto)
# Não é necessário pytest_plugins aqui, pois o pytest.ini já configura

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Add apps directory to Python path (for CLI modules)
apps_path = Path(__file__).parent.parent / "apps"
if str(apps_path) not in sys.path:
    sys.path.insert(0, str(apps_path))


def pytest_configure(config):
    """
    Hook executado ANTES da coleta de testes.

    Garante que o path esteja configurado corretamente antes de qualquer import.
    """
    # Garante que src e apps estão no path (antes da coleta)
    import sys
    from pathlib import Path

    src_path = Path(__file__).parent.parent / "src"
    apps_path = Path(__file__).parent.parent / "apps"

    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    if str(apps_path) not in sys.path:
        sys.path.insert(0, str(apps_path))


# ============================================================================
# Override tmp_path para workspace/core/tmp_path (ADR024)
# ============================================================================

@pytest.fixture
def tmp_path(tmp_path):
    """
    Override do tmp_path para usar workspace/core/tmp_path/.

    DOC: ADR024 - Temporários de teste ficam no workspace core.
    DOC: ADR024 - Limpo automaticamente pelo hook pós-commit.

    Isso facilita debug de testes (podemos inspecionar os .db)
    enquanto mantém isolamento do ambiente de produção.
    """
    from pathlib import Path

    # Usa workspace/core/tmp_path/ ao invés de /tmp/pytest-*
    custom_tmp_path = Path.cwd() / "workspace" / "core" / "tmp_path"
    custom_tmp_path.mkdir(parents=True, exist_ok=True)

    # Cria subdiretório único para este teste (preserva isolamento)
    import uuid
    test_tmp_path = custom_tmp_path / f"test_{uuid.uuid4().hex[:8]}"
    test_tmp_path.mkdir(exist_ok=True)

    return test_tmp_path


def is_server_online() -> bool:
    """
    Verifica se o servidor Skybridge está online.

    Returns:
        True se o servidor responde em http://localhost:8000
    """
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture
def mock_job_queue():
    """
    Job Queue mock para garantir isolamento em testes.

    DOC: ADR024 - Testes NUNCA tocam data/jobs.db de produção.

    Retorna um mock de JobQueuePort com comportamentos básicos
    configurados para evitar dependência de banco de dados.

    Example:
        def test_cria_job(mock_job_queue):
            mock_job_queue.enqueue.return_value = "test-job-123"
            job_id = await mock_job_queue.enqueue(job)
            assert job_id == "test-job-123"
    """
    from core.webhooks.ports.job_queue_port import JobQueuePort

    mock_queue = AsyncMock(spec=JobQueuePort)
    mock_queue.enqueue = AsyncMock(return_value="test-job-id")
    mock_queue.get_job = AsyncMock(return_value=None)
    mock_queue.dequeue = AsyncMock(return_value=None)
    mock_queue.complete = AsyncMock()
    mock_queue.fail = AsyncMock()
    mock_queue.exists_by_delivery = AsyncMock(return_value=False)
    mock_queue.mark_delivery_processed = AsyncMock()
    mock_queue.get_metrics = AsyncMock(return_value={
        "queue_size": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0,
        "total_enqueued": 0,
        "total_completed": 0,
        "total_failed": 0,
        "success_rate": 0.0,
    })
    mock_queue.list_jobs = AsyncMock(return_value=[])
    mock_queue.update_metadata = AsyncMock()
    mock_queue.size = Mock(return_value=0)
    mock_queue.clear = AsyncMock()
    mock_queue.close = AsyncMock()
    return mock_queue


@pytest.fixture
def isolated_job_queue(tmp_path):
    """
    Job queue REAL mas isolado em tmp_path.

    DOC: ADR024 - Cada teste tem seu banco SQLite isolado.
    DOC: ADR024 - Usa tmp_path do pytest para isolamento total.

    Cria uma instância real de SQLiteJobQueue apontando para
    um banco temporário isolado, garantindo que:
    - Testes não tocam data/jobs.db de produção
    - Cada teste tem seu próprio banco
    - Isolamento total entre testes

    Example:
        def test_isolamento(isolated_job_queue):
            await isolated_job_queue.enqueue(job)
            assert isolated_job_queue.size() == 1
    """
    from infra.webhooks.adapters.sqlite_job_queue import SQLiteJobQueue

    db_path = tmp_path / "test_jobs.db"
    queue = SQLiteJobQueue(db_path=db_path)
    return queue
