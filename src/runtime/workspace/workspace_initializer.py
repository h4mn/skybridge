# -*- coding: utf-8 -*-
"""
Workspace Initializer - Cria estrutura de workspaces.

Responsável por criar a estrutura de diretórios e arquivos
para um workspace Skybridge (ADR024).

DOC: ADR024 - Workspace isolation
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WorkspaceInitializer:
    """
    Initializer para workspaces Skybridge.

    Responsável por:
    - Criar estrutura de diretórios base
    - Criar arquivo .env inicial
    - Garantir permissões corretas

    Atributes:
        base_path: Caminho base onde os workspaces ficam (ex: "workspace/")
    """

    def __init__(self, base_path: str | Path):
        """
        Inicializa o initializer.

        Args:
            base_path: Caminho base para workspaces (ex: "workspace")
        """
        self.base_path = Path(base_path)

    def create_core(self) -> None:
        """
        Cria o workspace core com estrutura completa.

        Cria:
        - workspace/core/
        - workspace/core/.env (vazio ou com defaults)
        - workspace/core/.env.example (copiado da raiz)
        - workspace/core/config.json (configuração do workspace)
        - workspace/core/data/ (para bancos como jobs.db, kanban.db)
        - workspace/core/data/jobs.db (arquivo vazio)
        - workspace/core/data/executions.db (arquivo vazio)
        - workspace/core/worktrees/ (para worktrees do Git)

        Raises:
            OSError: Se não conseguir criar diretórios
        """
        core_path = self.base_path / "core"

        logger.info(f"Criando workspace core em: {core_path}")

        # Cria diretórios
        core_path.mkdir(parents=True, exist_ok=True)
        (core_path / "data").mkdir(exist_ok=True)
        (core_path / "worktrees").mkdir(exist_ok=True)

        # Cria arquivo .env inicial
        env_file = core_path / ".env"
        if not env_file.exists():
            env_file.write_text("# Environment variables para workspace core\n", encoding="utf-8")
            logger.info(f"Arquivo .env criado: {env_file}")

        # Copia .env.example da raiz do projeto para o workspace
        env_example_src = Path(__file__).parent.parent.parent.parent / ".env.example"
        env_example_dst = core_path / ".env.example"
        if env_example_src.exists() and not env_example_dst.exists():
            import shutil
            shutil.copy(env_example_src, env_example_dst)
            logger.info(f"Arquivo .env.example copiado: {env_example_dst}")

        # Cria config.json básico
        config_file = core_path / "config.json"
        if not config_file.exists():
            import json
            config = {
                "workspace_id": "core",
                "name": "Skybridge Core",
                "description": "Instância principal",
                "created_at": None,  # Será preenchendo pelo WorkspaceRepository
            }
            config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
            logger.info(f"Arquivo config.json criado: {config_file}")

        # Cria jobs.db vazio (será inicializado pelo JobQueue)
        jobs_db = core_path / "data" / "jobs.db"
        if not jobs_db.exists():
            jobs_db.touch()
            logger.info(f"Arquivo jobs.db criado: {jobs_db}")

        # Cria executions.db vazio (será inicializado pelo AgentExecutionStore)
        executions_db = core_path / "data" / "executions.db"
        if not executions_db.exists():
            executions_db.touch()
            logger.info(f"Arquivo executions.db criado: {executions_db}")

        logger.info(f"Workspace core criado com sucesso em: {core_path}")

    def create_workspace(self, workspace_id: str) -> Path:
        """
        Cria um novo workspace com a estrutura padrão.

        Args:
            workspace_id: ID do workspace (ex: "dev", "trading")

        Returns:
            Path para o diretório do workspace criado

        Raises:
            OSError: Se não conseguir criar diretórios
        """
        workspace_path = self.base_path / workspace_id

        logger.info(f"Criando workspace '{workspace_id}' em: {workspace_path}")

        # Cria diretórios
        workspace_path.mkdir(parents=True, exist_ok=True)
        (workspace_path / "data").mkdir(exist_ok=True)
        (workspace_path / "worktrees").mkdir(exist_ok=True)

        # Cria arquivo .env inicial
        env_file = workspace_path / ".env"
        if not env_file.exists():
            env_file.write_text(f"# Environment variables para workspace {workspace_id}\n", encoding="utf-8")
            logger.info(f"Arquivo .env criado: {env_file}")

        logger.info(f"Workspace '{workspace_id}' criado com sucesso")

        return workspace_path

    def create(self, workspace_id: str, name: Optional[str] = None) -> Path:
        """
        Cria um workspace (alias para create_workspace).

        Args:
            workspace_id: ID do workspace
            name: Nome do workspace (opcional)

        Returns:
            Path para o diretório do workspace criado
        """
        return self.create_workspace(workspace_id)
