# -*- coding: utf-8 -*-
"""
Workspace Middleware — Middleware de workspace para FastAPI.

DOC: ADR024 - Header X-Workspace define workspace ativo.
DOC: PB013 - Workspaces disabled=False retornam 404.

Este middleware intercepta todas as requisições para:
1. Ler o header X-Workspace
2. Validar se o workspace existe e está habilitado
3. Carregar o .env específico do workspace
4. Injetar o workspace_id no request.state

Uso:
    app = FastAPI()
    config = WorkspaceConfig.load(Path(".workspaces"))
    app.add_middleware(WorkspaceMiddleware, config=config)

Nas rotas:
    @app.get("/api/jobs")
    async def list_jobs(request: Request):
        workspace = request.state.workspace  # 'core', 'trading', etc.
        ...
"""

from fastapi import Request, HTTPException
from dotenv import load_dotenv
from pathlib import Path

from runtime.config.workspace_config import WorkspaceConfig


DEFAULT_WORKSPACE = "core"


class WorkspaceMiddleware:
    """
    Middleware que gerencia o contexto de workspace.

    Funcionalidades:
    - Lê header X-Workspace (padrão: core)
    - Valida workspace existe e está enabled
    - Carrega .env específico do workspace
    - Injeta workspace_id em request.state
    """

    def __init__(self, app, config: WorkspaceConfig):
        """
        Inicializa middleware.

        Args:
            app: Instância do FastAPI (obrigatório para middleware)
            config: WorkspaceConfig com workspaces disponíveis
        """
        self.config = config

    async def __call__(self, request: Request, call_next):
        """
        Processa requisição e define workspace.

        Args:
            request: Requisição FastAPI
            call_next: Próximo middleware/handler na chain

        Returns:
            Response do próximo middleware/handler

        Raises:
            HTTPException: 404 se workspace não existe ou está disabled
        """
        # 1. Lê header X-Workspace (case-insensitive)
        headers_dict = dict(request.headers)
        workspace_id = headers_dict.get("x-workspace", DEFAULT_WORKSPACE)

        # 2. Valida se workspace existe e está habilitado
        workspace = self.config.workspaces.get(workspace_id)
        if not workspace or not workspace.enabled:
            raise HTTPException(
                status_code=404,
                detail=f"Workspace '{workspace_id}' not found or disabled"
            )

        # 3. Carrega .env do workspace (se existir)
        env_path = Path(workspace.path) / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)

        # 4. Injeta no contexto da requisição
        request.state.workspace = workspace_id

        # 5. Continua chain
        response = await call_next(request)
        return response
