# -*- coding: utf-8 -*-
"""
Workspace Repository — Persistência de metadados de workspaces.

DOC: ADR024 - data/workspaces.db persiste metadados de workspaces.
DOC: PB013 - Workspaces podem ser criados, listados e deletados.

O WorkspaceRepository usa SQLite para persistir informações sobre workspaces:
- ID, nome, caminho
- Descrição
- Flags auto e enabled

Uso:
    repo = WorkspaceRepository.create(Path("data/workspaces.db"))
    repo.save(workspace)
    ws = repo.get("trading")
    all_ws = repo.list_all()
"""

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.config.workspace_config import Workspace as WorkspaceConfig


@dataclass
class Workspace:
    """Representa um workspace no repositório.

    Attributes:
        id: Identificador único do workspace (ex: "core", "trading")
        name: Nome amigável do workspace
        path: Caminho do diretório do workspace (relativo ou absoluto)
        description: Descrição do propósito do workspace
        auto: Se True, workspace é auto-criado na primeira execução
        enabled: Se False, workspace não é acessível via API
    """
    id: str
    name: str
    path: str
    description: str
    auto: bool
    enabled: bool


class WorkspaceRepository:
    """
    Repositório de workspaces usando SQLite.

    Gerencia persistência de metadados de workspaces em data/workspaces.db.

    A tabela workspaces tem a seguinte estrutura:
    - id: TEXT PRIMARY KEY
    - name: TEXT NOT NULL
    - path: TEXT NOT NULL
    - description: TEXT
    - auto: BOOLEAN DEFAULT 0
    - enabled: BOOLEAN DEFAULT 1
    """

    def __init__(self, db_path: Path):
        """
        Inicializa repositório com banco existente.

        Args:
            db_path: Caminho para o arquivo SQLite
        """
        self.db_path = db_path
        # NOTA: Não chamamos _init_table() aqui para permitir
        # uso com bancos já existentes

    @classmethod
    def create(cls, db_path: Path) -> "WorkspaceRepository":
        """
        Cria novo repositório com tabela inicializada.

        Args:
            db_path: Caminho para o arquivo SQLite

        Returns:
            WorkspaceRepository com tabela workspaces criada
        """
        repo = cls(db_path)
        repo._init_table()
        return repo

    def _init_table(self) -> None:
        """Cria tabela workspaces se não existir."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = self._get_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    description TEXT,
                    auto BOOLEAN DEFAULT 0,
                    enabled BOOLEAN DEFAULT 1
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Retorna conexão com SQLite configurada.

        Configurações:
        - check_same_thread=False (permite conexões entre threads)
        - row_factory=sqlite3.Row (acesso por nome da coluna)
        """
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        return conn

    def save(self, workspace: Workspace) -> None:
        """
        Salva ou atualiza workspace.

        Usa INSERT OR REPLACE para upsert.

        Args:
            workspace: Workspace a salvar
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO workspaces
                (id, name, path, description, auto, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    workspace.id,
                    workspace.name,
                    workspace.path,
                    workspace.description,
                    1 if workspace.auto else 0,
                    1 if workspace.enabled else 0,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get(self, workspace_id: str) -> Workspace | None:
        """
        Recupera workspace por ID.

        Args:
            workspace_id: ID do workspace

        Returns:
            Workspace ou None se não encontrado
        """
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM workspaces WHERE id = ?",
                (workspace_id,)
            ).fetchone()

            if not row:
                return None

            return Workspace(
                id=row["id"],
                name=row["name"],
                path=row["path"],
                description=row["description"] or "",
                auto=bool(row["auto"]),
                enabled=bool(row["enabled"]),
            )
        finally:
            conn.close()

    def list_all(self) -> list[Workspace]:
        """
        Lista todos os workspaces.

        Returns:
            Lista de todos os workspaces cadastrados
        """
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM workspaces").fetchall()
            return [
                Workspace(
                    id=row["id"],
                    name=row["name"],
                    path=row["path"],
                    description=row["description"] or "",
                    auto=bool(row["auto"]),
                    enabled=bool(row["enabled"]),
                )
                for row in rows
            ]
        finally:
            conn.close()

    def delete(self, workspace_id: str) -> None:
        """
        Deleta workspace por ID.

        Idempotente: não levanta erro se workspace não existir.

        Args:
            workspace_id: ID do workspace a deletar
        """
        conn = self._get_connection()
        try:
            conn.execute(
                "DELETE FROM workspaces WHERE id = ?",
                (workspace_id,)
            )
            conn.commit()
        finally:
            conn.close()

    def exists(self, workspace_id: str) -> bool:
        """
        Verifica se workspace existe.

        Args:
            workspace_id: ID do workspace

        Returns:
            True se workspace existe, False caso contrário
        """
        return self.get(workspace_id) is not None
