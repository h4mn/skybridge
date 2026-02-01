# -*- coding: utf-8 -*-
"""
Workspace Config — Configuração de workspaces do Skybridge.

DOC: ADR024 - Arquivo .workspaces define workspaces disponíveis.
DOC: PB013 - Workspaces têm name, path, description, auto, enabled.

O arquivo .workspaces é um JSON que define os workspaces disponíveis no sistema.
Cada workspace representa uma instância isolada do Skybridge com seus próprios:
- Variáveis de ambiente (.env)
- Bancos de dados (data/)
- Worktrees (worktrees/)
- Snapshots (snapshots/)
- Logs (logs/)

Example (.workspaces):
    {
      "default": "core",
      "workspaces": {
        "core": {
          "name": "Skybridge Core",
          "path": "workspace/core",
          "description": "Instância principal",
          "auto": true,
          "enabled": true
        },
        "trading": {
          "name": "Trading Bot",
          "path": "workspace/trading",
          "description": "Bot de trading",
          "auto": false,
          "enabled": true
        }
      }
    }
"""

from dataclasses import dataclass
from pathlib import Path
import json


class WorkspaceConfigNotFound(Exception):
    """Levantada quando o arquivo .workspaces não foi encontrado."""


class WorkspaceConfigInvalid(Exception):
    """Levantada quando o arquivo .workspaces contém JSON inválido."""


@dataclass
class Workspace:
    """Representa um workspace configurado.

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


@dataclass
class WorkspaceConfig:
    """Configuração de workspaces carregada do arquivo .workspaces.

    Attributes:
        default: ID do workspace padrão (usado quando nenhum é especificado)
        workspaces: Dicionário de ID -> Workspace
    """
    default: str
    workspaces: dict[str, Workspace]

    @classmethod
    def load(cls, path: Path) -> "WorkspaceConfig":
        """Carrega configuração do arquivo .workspaces.

        Args:
            path: Caminho para o arquivo .workspaces

        Returns:
            WorkspaceConfig com workspaces carregados

        Raises:
            WorkspaceConfigNotFound: Arquivo não existe
            WorkspaceConfigInvalid: JSON inválido
        """
        if not path.exists():
            raise WorkspaceConfigNotFound(f"Arquivo não encontrado: {path}")

        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise WorkspaceConfigInvalid(f"JSON inválido: {e}") from e

        workspaces = {}
        for ws_id, ws_data in data.get("workspaces", {}).items():
            workspaces[ws_id] = Workspace(
                id=ws_id,
                name=ws_data["name"],
                path=ws_data["path"],
                description=ws_data.get("description", ""),
                auto=ws_data.get("auto", False),
                enabled=ws_data.get("enabled", True)
            )

        return cls(
            default=data.get("default", "core"),
            workspaces=workspaces
        )
