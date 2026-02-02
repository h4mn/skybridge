# -*- coding: utf-8 -*-
"""
Testes da CLI de Workspace.

DOC: ADR024 - CLI workspace para gerenciar workspaces.
DOC: PB013 - Comandos: list, create, use, delete, current.

Testes unitários para commands em apps/cli/workspace.py.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from typer.testing import CliRunner
from apps.cli.workspace import workspace_app, get_active_workspace, ACTIVE_WORKSPACE_FILE

runner = CliRunner()


class TestWorkspaceList:
    """Testa comando workspace list."""

    @patch("apps.cli.workspace.requests.get")
    def test_workspace_list_mostra_tabela_com_workspaces(self, mock_get):
        """
        DOC: ADR024 - list mostra workspaces da API em tabela.

        Deve fazer GET /api/workspaces e exibir tabela com:
        - ID, Nome, Path, Auto, Status
        """
        # GIVEN - API retorna workspaces
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "workspaces": [
                {
                    "id": "core",
                    "name": "Skybridge Core",
                    "path": "workspace/core",
                    "description": "Instância principal",
                    "auto": True,
                    "enabled": True,
                },
                {
                    "id": "trading",
                    "name": "Trading Bot",
                    "path": "workspace/trading",
                    "description": "Bot de trading",
                    "auto": False,
                    "enabled": True,
                },
            ]
        }

        # WHEN
        result = runner.invoke(workspace_app, ["list"])

        # THEN
        assert result.exit_code == 0
        assert "core" in result.stdout
        assert "Skybridge Core" in result.stdout
        assert "trading" in result.stdout
        mock_get.assert_called_once_with("http://127.0.0.1:8000/api/workspaces")

    @patch("apps.cli.workspace.requests.get")
    def test_workspace_list_trata_erro_da_api(self, mock_get):
        """
        DOC: ADR024 - list trata erro da API graciosamente.

        Se API retorna erro, deve mostrar mensagem e exit code 1.
        """
        # GIVEN - API retorna erro
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Internal Server Error"

        # WHEN
        result = runner.invoke(workspace_app, ["list"])

        # THEN
        assert result.exit_code == 1
        assert "Erro" in result.stdout


class TestWorkspaceCreate:
    """Testa comando workspace create."""

    @patch("apps.cli.workspace.requests.post")
    def test_workspace_create_cria_novo_workspace(self, mock_post):
        """
        DOC: PB013 - create cria workspace via POST /api/workspaces.
        """
        # GIVEN - API cria workspace
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "id": "trading",
            "name": "Trading Bot",
            "path": "workspace/trading",
            "description": "Bot de trading",
            "auto": False,
            "enabled": True,
        }

        # WHEN
        result = runner.invoke(workspace_app, [
            "create",
            "trading",
            "--name", "Trading Bot",
        ])

        # THEN
        assert result.exit_code == 0
        assert "Workspace criado com sucesso" in result.stdout
        assert "trading" in result.stdout
        mock_post.assert_called_once()

    @patch("apps.cli.workspace.requests.post")
    def test_workspace_create_trata_conflito(self, mock_post):
        """
        DOC: PB013 - create trata 409 (workspace já existe).
        """
        # GIVEN - API retorna conflito
        mock_post.return_value.status_code = 409
        mock_post.return_value.text = "Conflict"

        # WHEN
        result = runner.invoke(workspace_app, [
            "create",
            "core",
            "--name", "Core",
        ])

        # THEN
        assert result.exit_code == 1
        assert "já existe" in result.stdout

    @patch("apps.cli.workspace.requests.post")
    def test_workspace_create_usa_path_padrao_se_nao_informado(self, mock_post):
        """
        DOC: PB013 - create usa workspace/<id> como path padrão.
        """
        # GIVEN
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": "dev", "name": "Dev"}

        # WHEN - sem --path
        result = runner.invoke(workspace_app, [
            "create",
            "dev",
            "--name", "Dev Environment",
        ])

        # THEN - payload deve ter path padrão
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["path"] == "workspace/dev"


class TestWorkspaceUse:
    """Testa comando workspace use."""

    def test_workspace_use_salva_workspace_ativo(self, tmp_path):
        """
        DOC: PB013 - use salva workspace em .workspace_active.
        """
        # GIVEN
        test_file = tmp_path / ".ws_active"

        with patch("apps.cli.workspace.ACTIVE_WORKSPACE_FILE", test_file):
            # WHEN
            result = runner.invoke(workspace_app, ["use", "trading"])

            # THEN
            assert result.exit_code == 0
            assert "Workspace ativo definido para" in result.stdout
            assert "trading" in result.stdout

            # Verificar arquivo
            assert test_file.exists()
            assert test_file.read_text() == "trading"

    def test_workspace_use_mostra_workspace_anterior(self, tmp_path):
        """
        DOC: PB013 - use mostra workspace anterior se existir.
        """
        # GIVEN - workspace anterior definido
        test_file = tmp_path / ".ws_active"
        test_file.write_text("core")

        with patch("apps.cli.workspace.ACTIVE_WORKSPACE_FILE", test_file):
            # WHEN
            result = runner.invoke(workspace_app, ["use", "trading"])

            # THEN
            assert result.exit_code == 0
            assert "Anterior: core" in result.stdout


class TestWorkspaceDelete:
    """Testa comando workspace delete."""

    @patch("apps.cli.workspace.requests.delete")
    def test_workspace_delete_deleta_workspace(self, mock_delete):
        """
        DOC: PB013 - delete deleta workspace via DELETE /api/workspaces/:id.
        """
        # GIVEN
        mock_delete.return_value.status_code = 200
        mock_delete.return_value.json.return_value = {"message": "Workspace deleted"}

        # WHEN
        result = runner.invoke(workspace_app, ["delete", "trading", "--force"])

        # THEN
        assert result.exit_code == 0
        assert "deleted" in result.stdout.lower()
        mock_delete.assert_called_once_with("http://127.0.0.1:8000/api/workspaces/trading")

    def test_workspace_delete_nao_permite_deletar_core(self):
        """
        DOC: PB013 - delete não permite deletar workspace 'core'.
        """
        # WHEN
        result = runner.invoke(workspace_app, ["delete", "core", "--force"])

        # THEN
        assert result.exit_code == 1
        assert "não é possível deletar" in result.stdout.lower()

    @patch("apps.cli.workspace.requests.delete")
    def test_workspace_delete_trata_workspace_nao_encontrado(self, mock_delete):
        """
        DOC: PB013 - delete trata 404 (workspace não encontrado).
        """
        # GIVEN
        mock_delete.return_value.status_code = 404
        mock_delete.return_value.text = "Not found"

        # WHEN
        result = runner.invoke(workspace_app, ["delete", "inexistente", "--force"])

        # THEN
        assert result.exit_code == 1
        assert "não encontrado" in result.stdout.lower()


class TestWorkspaceCurrent:
    """Testa comando workspace current."""

    def test_workspace_current_mostra_ativo(self, tmp_path):
        """
        DOC: PB013 - current mostra workspace salvo em .workspace_active.
        """
        # GIVEN - workspace ativo definido
        test_file = tmp_path / ".ws_active"
        test_file.write_text("trading")

        with patch("apps.cli.workspace.ACTIVE_WORKSPACE_FILE", test_file):
            # WHEN
            result = runner.invoke(workspace_app, ["current"])

            # THEN
            assert result.exit_code == 0
            assert "Workspace ativo: trading" in result.stdout

    def test_workspace_current_mostra_mensagem_se_nenhum_definido(self, tmp_path):
        """
        DOC: PB013 - current mostra mensagem se nenhum workspace ativo.
        """
        # GIVEN - nenhum workspace definido
        test_file = tmp_path / ".ws_active"

        with patch("apps.cli.workspace.ACTIVE_WORKSPACE_FILE", test_file):
            # WHEN
            result = runner.invoke(workspace_app, ["current"])

            # THEN
            assert result.exit_code == 0
            assert "Nenhum workspace ativo" in result.stdout


class TestGetActiveWorkspace:
    """Testa função auxiliar get_active_workspace."""

    def test_get_active_workspace_retorna_workspace_salvo(self, tmp_path):
        """
        DOC: PB013 - get_active_workspace() lê de .workspace_active.
        """
        # GIVEN
        test_file = tmp_path / ".ws_active"
        test_file.write_text("trading")

        with patch("apps.cli.workspace.ACTIVE_WORKSPACE_FILE", test_file):
            # WHEN
            result = get_active_workspace()

            # THEN
            assert result == "trading"

    def test_get_active_workspace_retorna_none_se_arquivo_nao_existe(self, tmp_path):
        """
        DOC: PB013 - get_active_workspace() retorna None se arquivo não existe.
        """
        # GIVEN - arquivo não existe
        test_file = tmp_path / ".ws_active_nao_existe"

        with patch("apps.cli.workspace.ACTIVE_WORKSPACE_FILE", test_file):
            # WHEN
            result = get_active_workspace()

            # THEN
            assert result is None
