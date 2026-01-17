# -*- coding: utf-8 -*-
"""
Bootstrap — Inicialização da aplicação Skybridge.

Orquestra a composição de todos os componentes.
"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import threading
import uuid
import yaml

from runtime.config.config import get_config, get_fileops_config
from runtime.observability.logger import get_logger, print_separator, Colors
from kernel import get_query_registry
from kernel.registry.discovery import discover_modules
from kernel.registry.skyrpc_registry import get_skyrpc_registry
from infra.fileops.filesystem_adapter import create_filesystem_adapter
from core.fileops.application.queries.read_file import ReadFileQuery, set_read_file_query

# Webhook worker (PRD013)
_webhook_worker_thread = None


def start_webhook_worker():
    """Inicia worker em thread separada."""
    import asyncio
    from runtime.background.webhook_worker import main as worker_main
    from runtime.config.config import get_webhook_config

    webhook_config = get_webhook_config()

    if "github" not in webhook_config.enabled_sources:
        return

    logger = get_logger()
    logger.info(f"Iniciando worker de {Colors.WHITE}Webhook{Colors.RESET} em thread de background")

    # Run worker in new event loop
    asyncio.run(worker_main())


def start_webhook_worker_sync():
    """Inicia worker de forma síncrona (para rodar em thread)."""
    import asyncio
    from runtime.background.webhook_worker import WebhookWorker
    from core.webhooks.application.job_orchestrator import (
        JobOrchestrator,
    )
    from core.webhooks.application.worktree_manager import (
        WorktreeManager,
    )
    from core.webhooks.application.handlers import get_job_queue
    from runtime.config.config import get_webhook_config

    webhook_config = get_webhook_config()

    if "github" not in webhook_config.enabled_sources:
        return

    logger = get_logger()
    logger.info(f"Iniciando worker de {Colors.WHITE}Webhook{Colors.RESET}")

    job_queue = get_job_queue()
    worktree_manager = WorktreeManager(webhook_config.worktree_base_path)
    orchestrator = JobOrchestrator(job_queue, worktree_manager)
    worker = WebhookWorker(job_queue, orchestrator)

    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(worker.start())
    finally:
        loop.close()




class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware para adicionar correlation_id."""

    async def dispatch(self, request: Request, call_next):
        # Gera correlation_id
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Processa request
        response = await call_next(request)

        # Adiciona correlation_id no response
        response.headers["x-correlation-id"] = correlation_id
        return response


class SkybridgeApp:
    """
    Aplicação Skybridge FastAPI.

    Responsável por:
    - Configurar FastAPI
    - Registrar middlewares
    - Registrar queries
    """

    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(level=self.config.log_level)
        self.app = FastAPI(
            title=self.config.title,
            version=self.config.version,
            description=self.config.description,
            docs_url=self.config.docs_url,
            redoc_url=self.config.redoc_url,
        )
        # Override FastAPI's auto OpenAPI to use our manual YAML
        self.app.openapi = self._custom_openapi
        self._setup_middleware()
        self._register_queries()
        self._setup_routes()
        self._start_webhook_worker()  # PRD013: inicia worker

    def _start_webhook_worker(self):
        """Inicia worker em thread separada."""
        from runtime.config.config import get_webhook_config

        webhook_config = get_webhook_config()

        if "github" in webhook_config.enabled_sources:
            global _webhook_worker_thread

            # Usa daemon=True para thread não bloquear shutdown
            _webhook_worker_thread = threading.Thread(
                target=start_webhook_worker_sync,
                daemon=True,
                name="webhook-worker"
            )
            _webhook_worker_thread.start()

            self.logger.info(f"Thread do worker de {Colors.WHITE}Webhook{Colors.RESET} iniciada")

    def _custom_openapi(self):
        """
        Gera OpenAPI Híbrido: operações estáticas (YAML), schemas dinâmicos (registry).

        Conforme ADR016 e PRD010:
        - Operações HTTP são carregadas do YAML estático
        - Schemas são injetados do registry runtime
        """
        # 1. Encontra raiz do repositório
        repo_root = None
        for parent in Path(__file__).resolve().parents:
            if (parent / "docs").is_dir() and (parent / "src").is_dir():
                repo_root = parent
                break
        if repo_root is None:
            repo_root = Path.cwd()

        openapi_path = repo_root / "docs" / "spec" / "openapi" / "openapi.yaml"

        # 2. Carrega YAML estático (operações)
        if not openapi_path.exists():
            return {}

        with open(openapi_path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)

        # 3. Inicializa components se não existir
        if "components" not in spec:
            spec["components"] = {}
        if "schemas" not in spec["components"]:
            spec["components"]["schemas"] = {}

        # 4. Injeta schemas dinâmicos do registry
        registry = get_skyrpc_registry()
        discovery = registry.get_discovery()

        # 4.1. Schemas de handlers (input/output)
        for method_name, handler_meta in discovery.discovery.items():
            spec["components"]["schemas"][f"{method_name}Input"] = handler_meta.input_schema or {"type": "object", "properties": {}}
            spec["components"]["schemas"][f"{method_name}Output"] = handler_meta.output_schema or {"type": "object", "properties": {}}

        # 5. Gera schemas reutilizáveis
        spec["components"]["schemas"].update({
            "TicketResponse": self._generate_ticket_response_schema(),
            "EnvelopeRequest": self._generate_envelope_request_schema(),
            "EnvelopeDetailStruct": self._generate_envelope_detail_struct_schema(),
            "EnvelopeResponse": self._generate_envelope_response_schema(),
            "Error": self._generate_error_schema(),
            "SkyRpcDiscovery": self._generate_discovery_schema(),
            "SkyRpcHandler": self._generate_handler_schema(),
        })

        return spec

    def _generate_ticket_response_schema(self) -> dict:
        """Gera schema de TicketResponse."""
        return {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "ticket": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "method": {"type": "string"},
                        "expires_in": {"type": "integer"},
                        "accepts": {"type": "string"}
                    },
                    "required": ["id", "method", "expires_in"]
                }
            },
            "required": ["ok"]
        }

    def _generate_envelope_request_schema(self) -> dict:
        """Gera schema de EnvelopeRequest."""
        return {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "ticket_id": {"type": "string", "format": "uuid"},
                "detail": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/EnvelopeDetailStruct"},
                        {"type": "string"}
                    ]
                }
            },
            "required": ["ticket_id", "detail"]
        }

    def _generate_envelope_detail_struct_schema(self) -> dict:
        """Gera schema de EnvelopeDetailStruct (v0.3)."""
        return {
            "type": "object",
            "properties": {
                "context": {"type": "string"},
                "action": {"type": "string"},
                "subject": {"type": "string"},
                "scope": {"type": "string"},
                "options": {"type": "object", "additionalProperties": True},
                "payload": {"type": "object", "additionalProperties": True}
            },
            "required": ["context", "action"]
        }

    def _generate_envelope_response_schema(self) -> dict:
        """Gera schema de EnvelopeResponse."""
        return {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "id": {"type": "string"},
                "result": {"type": "object", "additionalProperties": True},
                "error": {"$ref": "#/components/schemas/Error"}
            },
            "required": ["ok", "id"]
        }

    def _generate_error_schema(self) -> dict:
        """Gera schema de Error."""
        return {
            "type": "object",
            "properties": {
                "code": {"type": "integer"},
                "message": {"type": "string"},
                "details": {"type": "object", "additionalProperties": True}
            },
            "required": ["code", "message"]
        }

    def _generate_discovery_schema(self) -> dict:
        """Gera schema de SkyRpcDiscovery."""
        return {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "discovery": {
                    "type": "object",
                    "additionalProperties": {"$ref": "#/components/schemas/SkyRpcHandler"}
                }
            },
            "required": ["version", "discovery"]
        }

    def _generate_handler_schema(self) -> dict:
        """Gera schema de SkyRpcHandler."""
        return {
            "type": "object",
            "properties": {
                "method": {"type": "string"},
                "kind": {"type": "string", "enum": ["query", "command"]},
                "module": {"type": "string"},
                "description": {"type": "string"},
                "auth_required": {"type": "boolean"},
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"}
            },
            "required": ["method", "kind", "module"]
        }

    def _setup_middleware(self):
        """Configura middlewares."""
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        # Correlation ID
        self.app.add_middleware(CorrelationMiddleware)

    def _register_queries(self):
        """Registra queries no registry."""
        registry = get_query_registry()

        # Configurar FileOps
        fileops_config = get_fileops_config()
        fs_adapter = create_filesystem_adapter(
            mode=fileops_config.allowlist_mode,
            root=fileops_config.dev_root or str(Path.cwd())
        )
        read_file_query = ReadFileQuery(
            allowed_path=fs_adapter.allowed_path,
            filesystem=fs_adapter
        )
        set_read_file_query(read_file_query)

        # Auto-descoberta via decorators
        from runtime.config.config import get_discovery_config
        discovery_config = get_discovery_config()
        modules = discover_modules(
            discovery_config.packages,
            include_submodules=discovery_config.include_submodules,
        )

        self.logger.info("Queries registradas", extra={
            "count": len(registry.list_all()),
            "fileops_mode": fileops_config.allowlist_mode,
            "modules": modules,
        })

    def _setup_routes(self):
        """Configura rotas."""
        from runtime.delivery.routes import create_rpc_router
        self.app.include_router(create_rpc_router(), tags=["Sky-RPC"])
        self.logger.info("Rotas configuradas")

    def run(self, host: str | None = None, port: int | None = None):
        """Executa o servidor com uvicorn."""
        import uvicorn

        from runtime.config.config import get_ssl_config

        host = host or self.config.host
        port = port or self.config.port
        ssl_config = get_ssl_config()

        self.logger.info(
            f"Iniciando {self.config.title}",
            extra={
                "host": host,
                "port": port,
                "docs": f"http://{host}:{port}{self.config.docs_url}",
            },
        )

        uvicorn_kwargs = {
            "app": self.app,
            "host": host,
            "port": port,
            "log_level": self.config.log_level.lower(),
        }
        if ssl_config.enabled:
            if ssl_config.cert_file and ssl_config.key_file:
                uvicorn_kwargs["ssl_certfile"] = ssl_config.cert_file
                uvicorn_kwargs["ssl_keyfile"] = ssl_config.key_file
            else:
                self.logger.warning(
                    "SSL habilitado mas cert/key não configurados",
                    extra={"cert_file": ssl_config.cert_file, "key_file": ssl_config.key_file},
                )

        # Separador antes dos logs do uvicorn
        print()
        print_separator("─", 60)

        uvicorn.run(
            **uvicorn_kwargs,
        )

        # Separador depois dos logs do uvicorn
        print()
        print_separator("═", 60)


# Singleton global
_app: SkybridgeApp | None = None


def get_app() -> SkybridgeApp:
    """Retorna aplicação global."""
    global _app
    if _app is None:
        _app = SkybridgeApp()
    return _app
