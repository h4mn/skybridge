# -*- coding: utf-8 -*-
"""
Workspaces Routes — API de management de workspaces.

DOC: ADR024 - GET /api/workspaces lista todos.
DOC: PB013 - POST /api/workspaces cria nova instância.
DOC: PB013 - DELETE /api/workspaces/:id deleta workspace.

Esta API NÃO requer header X-Workspace, pois é usada para gerenciar
os próprios workspaces.

Rotas:
- GET /api/workspaces - Listar todos os workspaces
- GET /api/workspaces/:id - Obter workspace específico
- POST /api/workspaces - Criar novo workspace
- DELETE /api/workspaces/:id - Deletar workspace
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from runtime.config.workspace_config import WorkspaceConfig
from runtime.config.workspace_repository import WorkspaceRepository
from runtime.workspace.workspace_initializer import WorkspaceInitializer


# Schemas Pydantic
class WorkspaceResponse(BaseModel):
    """Resposta com dados de um workspace."""
    id: str
    name: str
    path: str
    description: str = ""
    auto: bool = False
    enabled: bool = True

    @classmethod
    def from_domain(cls, workspace):
        """Converte Workspace do domínio para resposta."""
        return cls(
            id=workspace.id,
            name=workspace.name,
            path=workspace.path,
            description=workspace.description,
            auto=workspace.auto,
            enabled=workspace.enabled
        )


class CreateWorkspaceRequest(BaseModel):
    """Request para criar novo workspace."""
    id: str = Field(..., min_length=1, pattern="^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., min_length=1)
    description: str = Field(default="", max_length=500)

    @field_validator('id')
    @classmethod
    def id_must_be_lowercase(cls, v: str) -> str:
        """Valida que ID contém apenas caracteres permitidos."""
        if not all(c.islower() or c.isdigit() or c in ('_', '-') for c in v):
            raise ValueError('ID must contain only lowercase letters, digits, hyphens and underscores')
        return v


class WorkspacesListResponse(BaseModel):
    """Resposta com lista de workspaces."""
    workspaces: list[WorkspaceResponse]


class MessageResponse(BaseModel):
    """Resposta genérica com mensagem."""
    message: str


def create_router(
    config: WorkspaceConfig,
    repository: WorkspaceRepository,
    initializer: WorkspaceInitializer
) -> APIRouter:
    """
    Cria router de workspaces com injeção de dependências.

    Args:
        config: WorkspaceConfig com workspaces disponíveis
        repository: WorkspaceRepository para persistência
        initializer: WorkspaceInitializer para criação de estrutura

    Returns:
        APIRouter configurado
    """
    router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])

    @router.get("", response_model=WorkspacesListResponse)
    async def list_workspaces() -> WorkspacesListResponse:
        """
        Lista todos os workspaces (sem header necessário).

        DOC: ADR024 - GET /api/workspaces lista todos.
        """
        workspaces = repository.list_all()
        return WorkspacesListResponse(
            workspaces=[WorkspaceResponse.from_domain(ws) for ws in workspaces]
        )

    @router.get("/{workspace_id}", response_model=WorkspaceResponse)
    async def get_workspace(workspace_id: str) -> WorkspaceResponse:
        """
        Obter workspace específico por ID.

        Args:
            workspace_id: ID do workspace

        Returns:
            Dados do workspace

        Raises:
            HTTPException: 404 se workspace não existe
        """
        workspace = repository.get(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace '{workspace_id}' not found"
            )
        return WorkspaceResponse.from_domain(workspace)

    @router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
    async def create_workspace(req: CreateWorkspaceRequest) -> WorkspaceResponse:
        """
        Criar novo workspace.

        DOC: PB013 - POST /api/workspaces cria nova instância.

        Cria estrutura de diretórios e salva no repositório.

        Args:
            req: Dados do workspace a criar

        Returns:
            Workspace criado
        """
        # Verificar se já existe
        existing = repository.get(req.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Workspace '{req.id}' already exists"
            )

        # Criar estrutura de diretórios
        initializer.create(req.id, req.name, auto=False)

        # Salvar no repositório
        from runtime.config.workspace_repository import Workspace
        workspace = Workspace(
            id=req.id,
            name=req.name,
            path=req.path,
            description=req.description,
            auto=False,
            enabled=True
        )
        repository.save(workspace)

        return WorkspaceResponse.from_domain(workspace)

    @router.delete("/{workspace_id}", response_model=MessageResponse)
    async def delete_workspace(workspace_id: str) -> MessageResponse:
        """
        Deletar workspace.

        DOC: PB013 - DELETE /api/workspaces/:id deleta workspace.

        Args:
            workspace_id: ID do workspace a deletar

        Returns:
            Mensagem de confirmação

        Raises:
            HTTPException: 404 se workspace não existe
        """
        # Verificar se existe
        workspace = repository.get(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace '{workspace_id}' not found"
            )

        # Não permitir deletar workspace core
        if workspace_id == "core":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete 'core' workspace"
            )

        # Deletar do repositório
        repository.delete(workspace_id)

        return MessageResponse(message=f"Workspace '{workspace_id}' deleted")

    return router
