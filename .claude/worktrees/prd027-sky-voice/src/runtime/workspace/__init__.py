# -*- coding: utf-8 -*-
"""
Runtime Workspace Module.

Gerencia contexto de workspaces multi-instância (ADR024).
"""

from runtime.workspace.workspace_context import get_current_workspace, set_current_workspace
from runtime.workspace.workspace_initializer import WorkspaceInitializer

__all__ = [
    "get_current_workspace",
    "set_current_workspace",
    "WorkspaceInitializer",
]
