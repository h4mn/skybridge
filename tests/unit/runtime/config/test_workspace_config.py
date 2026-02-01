# -*- coding: utf-8 -*-
"""
Testes para WorkspaceConfig.

TDD Estrito: Testes que documentam o comportamento esperado da configuração de workspaces.

DOC: ADR024 - Arquivo .workspaces define workspaces disponíveis.
DOC: PB013 - Workspaces têm name, path, description, auto, enabled.
"""
import pytest
from pathlib import Path

from runtime.config.workspace_config import (
    WorkspaceConfig,
    Workspace,
    WorkspaceConfigNotFound,
    WorkspaceConfigInvalid,
)


class TestWorkspaceConfigLoad:
    """Testa carregamento do arquivo .workspaces."""

    def test_load_workspaces_from_file(self, tmp_path):
        """
        DOC: ADR024 - Arquivo .workspaces define workspaces disponíveis.

        O arquivo .workspaces deve ser um JSON com:
        - default: workspace padrão (geralmente "core")
        - workspaces: objeto com workspaces configurados
        """
        # Criar arquivo .workspaces de teste
        workspaces_file = tmp_path / ".workspaces"
        workspaces_file.write_text('''{
  "default": "core",
  "workspaces": {
    "core": {
      "name": "Skybridge Core",
      "path": "workspace/core",
      "description": "Instancia principal",
      "auto": true,
      "enabled": true
    }
  }
}''', encoding="utf-8")

        config = WorkspaceConfig.load(workspaces_file)

        assert config.default == "core"
        assert "core" in config.workspaces
        assert config.workspaces["core"].name == "Skybridge Core"
        assert config.workspaces["core"].path == "workspace/core"
        assert config.workspaces["core"].description == "Instancia principal"
        assert config.workspaces["core"].auto is True
        assert config.workspaces["core"].enabled is True

    def test_workspace_config_file_not_found_raises_error(self, tmp_path):
        """
        DOC: Arquivo .workspaces inexistente levanta erro.

        WorkspaceConfigNotFound deve ser levantada quando o arquivo não existe.
        """
        nonexistent = tmp_path / "nonexistent" / ".workspaces"

        with pytest.raises(WorkspaceConfigNotFound) as exc:
            WorkspaceConfig.load(nonexistent)

        assert "Arquivo não encontrado" in str(exc.value)

    def test_workspace_config_invalid_json_raises_error(self, tmp_path):
        """
        DOC: JSON inválido levanta erro de parsing.

        WorkspaceConfigInvalid deve ser levantada quando o JSON é inválido.
        """
        invalid_file = tmp_path / ".workspaces.invalid.json"
        invalid_file.write_text('{"default": "core", "workspaces": {"core": {', encoding="utf-8")

        with pytest.raises(WorkspaceConfigInvalid) as exc:
            WorkspaceConfig.load(invalid_file)

        assert "JSON inválido" in str(exc.value)

    def test_workspace_config_default_values(self, tmp_path):
        """
        DOC: Valores padrão são aplicados quando campos omitidos.

        Campos com valores padrão:
        - description: "" (vazio)
        - auto: false
        - enabled: true
        - default: "core"
        """
        workspaces_file = tmp_path / ".workspaces"
        workspaces_file.write_text('''{
  "workspaces": {
    "minimal": {
      "name": "Minimal Workspace",
      "path": "workspace/minimal"
    }
  }
}''', encoding="utf-8")

        config = WorkspaceConfig.load(workspaces_file)

        assert config.default == "core"  # padrão
        assert config.workspaces["minimal"].description == ""
        assert config.workspaces["minimal"].auto is False
        assert config.workspaces["minimal"].enabled is True


class TestWorkspace:
    """Testa o dataclass Workspace."""

    def test_workspace_has_required_fields(self):
        """
        DOC: ADR024 - Cada workspace tem name, path, description, auto, enabled.

        O dataclass Workspace deve ter todos os campos obrigatórios.
        """
        workspace = Workspace(
            id="core",
            name="Skybridge Core",
            path="workspace/core",
            description="Instância principal",
            auto=True,
            enabled=True
        )

        assert workspace.id == "core"
        assert workspace.name == "Skybridge Core"
        assert workspace.path == "workspace/core"
        assert workspace.description == "Instância principal"
        assert workspace.auto is True
        assert workspace.enabled is True

    def test_workspace_core_is_auto_created(self):
        """
        DOC: ADR024 - Workspace 'core' é auto-criada na primeira execução.

        O workspace core deve ter auto=True por padrão.
        """
        workspace = Workspace(
            id="core",
            name="Skybridge Core",
            path="workspace/core",
            description="Instância principal",
            auto=True,
            enabled=True
        )

        assert workspace.auto is True

    def test_workspace_custom_is_not_auto_created(self):
        """
        DOC: PB013 - Workspaces customizados têm auto=False por padrão.

        Workspaces criados pelo usuário não são auto-criados.
        """
        workspace = Workspace(
            id="trading",
            name="Trading Bot",
            path="workspace/trading",
            description="Bot de trading",
            auto=False,
            enabled=True
        )

        assert workspace.auto is False

    def test_workspace_can_be_disabled(self):
        """
        DOC: PB013 - Workspaces podem ser desabilitados com enabled=False.

        Workspaces desabilitados não devem ser acessíveis via API.
        """
        workspace = Workspace(
            id="disabled",
            name="Disabled Workspace",
            path="workspace/disabled",
            description="Workspace desabilitado",
            auto=False,
            enabled=False
        )

        assert workspace.enabled is False


class TestWorkspaceConfigMultipleWorkspaces:
    """Testa configuração com múltiplos workspaces."""

    def test_load_multiple_workspaces(self, tmp_path):
        """
        DOC: ADR024 - Arquivo .workspaces pode definir múltiplos workspaces.

        Vários workspaces podem ser configurados no mesmo arquivo.
        """
        workspaces_file = tmp_path / ".workspaces"
        workspaces_file.write_text('''{
  "default": "core",
  "workspaces": {
    "core": {
      "name": "Skybridge Core",
      "path": "workspace/core",
      "description": "Instancia principal",
      "auto": true,
      "enabled": true
    },
    "trading": {
      "name": "Trading Bot",
      "path": "workspace/trading",
      "description": "Bot de trading",
      "auto": false,
      "enabled": true
    },
    "futura": {
      "name": "Futura AI",
      "path": "workspace/futura",
      "description": "IA futurista",
      "auto": false,
      "enabled": true
    }
  }
}''', encoding="utf-8")

        config = WorkspaceConfig.load(workspaces_file)

        assert len(config.workspaces) == 3
        assert "core" in config.workspaces
        assert "trading" in config.workspaces
        assert "futura" in config.workspaces
        assert config.workspaces["trading"].name == "Trading Bot"
        assert config.workspaces["futura"].description == "IA futurista"

    def test_workspace_default_can_be_custom(self, tmp_path):
        """
        DOC: ADR024 - Workspace padrão pode ser configurado.

        O campo 'default' define qual workspace é usado quando nenhum é especificado.
        """
        workspaces_file = tmp_path / ".workspaces"
        workspaces_file.write_text('''{
  "default": "trading",
  "workspaces": {
    "core": {
      "name": "Skybridge Core",
      "path": "workspace/core",
      "description": "Instancia principal",
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
}''', encoding="utf-8")

        config = WorkspaceConfig.load(workspaces_file)

        assert config.default == "trading"
