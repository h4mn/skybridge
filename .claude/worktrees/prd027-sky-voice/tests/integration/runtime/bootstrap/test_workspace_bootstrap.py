# -*- coding: utf-8 -*-
"""
Testes de auto-criação de workspace core no bootstrap.

DOC: ADR024 - Workspace core é auto-criado na primeira execução.

Estes testes verificam que o bootstrap cria automaticamente o workspace
core quando ele não existe.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestWorkspaceCoreBootstrap:
    """Testes de auto-criação de workspace core."""

    def test_bootstrap_cria_workspace_core_quando_nao_existe(self, tmp_path):
        """
        DOC: ADR024 - Bootstrap cria workspace core automaticamente.

        Quando workspace/core não existe, o bootstrap deve:
        1. Criar estrutura completa
        2. Copiar .env.example → .env
        3. Registrar no data/workspaces.db
        """
        # GIVEN - ambiente sem workspace core
        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir(parents=True, exist_ok=True)

        workspaces_db = tmp_path / "data" / "workspaces.db"
        workspaces_db.parent.mkdir(parents=True, exist_ok=True)

        # WHEN - simula bootstrap
        from runtime.workspace.workspace_initializer import WorkspaceInitializer
        from runtime.config.workspace_repository import WorkspaceRepository

        initializer = WorkspaceInitializer(workspace_path)

        # Simula criação do core
        if not (workspace_path / "core").exists():
            initializer.create_core()

        # Registrar no banco
        repo = WorkspaceRepository.create(workspaces_db)
        from runtime.config.workspace_config import Workspace
        core_ws = Workspace(
            id="core",
            name="Skybridge Core",
            path=str(workspace_path / "core"),
            description="Instância principal",
            auto=True,
            enabled=True
        )
        if not repo.exists("core"):
            repo.save(core_ws)

        # THEN
        core_path = workspace_path / "core"
        assert core_path.exists()
        assert (core_path / "data").exists()
        assert (core_path / "worktrees").exists()
        assert (core_path / ".env").exists()
        assert (core_path / ".env.example").exists()
        assert (core_path / "config.json").exists()
        assert (core_path / "data" / "jobs.db").exists()
        assert (core_path / "data" / "executions.db").exists()

        # Verificar registro no banco
        registered = repo.get("core")
        assert registered is not None
        assert registered.id == "core"
        assert registered.name == "Skybridge Core"
        assert registered.auto is True

    def test_bootstrap_nao_recria_core_se_ja_existe(self, tmp_path):
        """
        DOC: ADR024 - Bootstrap é idempotente - não recria se existe.

        Se workspace/core já existe, não deve recriar (idempotente).
        """
        # GIVEN - workspace core já existe
        workspace_path = tmp_path / "workspace"
        core_path = workspace_path / "core"
        core_path.mkdir(parents=True, exist_ok=True)

        # Criar um arquivo marker
        marker = core_path / ".marker"
        marker.write_text("already exists", encoding="utf-8")

        # WHEN - simula bootstrap
        from runtime.workspace.workspace_initializer import WorkspaceInitializer

        initializer = WorkspaceInitializer(workspace_path)

        # Tentar criar core (não deve sobrescrever)
        initializer.create_core()

        # THEN - marker ainda existe (não foi sobrescrito)
        assert marker.exists()
        assert marker.read_text(encoding="utf-8") == "already exists"
