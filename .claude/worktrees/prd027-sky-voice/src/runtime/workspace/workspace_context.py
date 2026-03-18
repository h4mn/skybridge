# -*- coding: utf-8 -*-
"""
Workspace Context - Gerencia workspace ativo.

Fornece funções para obter e definir o workspace ativo,
usado por diversos componentes para isolamento (ADR024).

DOC: ADR024 - Workspace isolation
"""

from contextvars import ContextVar
from pathlib import Path
from typing import Optional

# ContextVar para armazenar o workspace ativo async-localmente
_current_workspace: ContextVar[Optional[str]] = ContextVar("current_workspace", default=None)


def get_current_workspace(request=None) -> Optional[str]:
    """
    Retorna o workspace ativo.

    Args:
        request: Opcional. Se fornecido, usa request.state.workspace

    Primeiro tenta obter do request.state (se fornecido).
    Depois tenta obter do ContextVar (thread/task local).
    Se não definido, retorna "core" como padrão.

    Returns:
        ID do workspace ativo (padrão: "core")
    """
    # Tenta obter do request.state primeiro
    if request and hasattr(request.state, "workspace"):
        return request.state.workspace

    # Tenta obter do ContextVar
    workspace_id = _current_workspace.get()
    if workspace_id:
        return workspace_id

    # Padrão é "core"
    return "core"


def set_current_workspace(workspace_id: str) -> None:
    """
    Define o workspace ativo para o contexto atual.

    Args:
        workspace_id: ID do workspace (ex: "core", "trading", "dev")
    """
    _current_workspace.set(workspace_id)


def get_workspace_path(workspace_id: Optional[str] = None) -> Path:
    """
    Retorna o caminho para um workspace.

    Args:
        workspace_id: ID do workspace (padrão: workspace ativo)

    Returns:
        Path para o diretório do workspace
    """
    if workspace_id is None:
        workspace_id = get_current_workspace()

    return Path("workspace") / workspace_id


def set_workspace(request, workspace_id: str) -> None:
    """
    Define o workspace no contexto da requisição.

    DOC: PL002 - ADR024 Workspace isolation
    Usado em testes para simular workspace no request.state.

    Args:
        request: Objeto de requisição (Starlette/FastAPI Request)
        workspace_id: ID do workspace (ex: "core", "trading")
    """
    request.state.workspace = workspace_id
