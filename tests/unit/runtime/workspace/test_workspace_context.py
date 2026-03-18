# -*- coding: utf-8 -*-
"""
Testes de get_current_workspace.

DOC: ADR024 - get_current_workspace() retorna workspace ativo do contexto.

Estes testes verificam que a função recupera o workspace do request.state
e faz fallback para o workspace padrão quando não especificado.
"""

import pytest
from unittest.mock import Mock, patch

from runtime.workspace.workspace_context import get_current_workspace, set_current_workspace


class TestGetCurrentWorkspace:
    """Testes de get_current_workspace."""

    def test_get_current_workspace_retorna_workspace_do_request_state(self):
        """
        DOC: ADR024 - Retorna workspace definido no request.state.workspace.

        Quando o middleware define request.state.workspace, get_current_workspace()
        deve retornar esse valor.
        """
        # GIVEN - request state com workspace definido
        mock_request = Mock()
        mock_request.state.workspace = "trading"

        with patch('runtime.workspace.workspace_context.get_request', return_value=mock_request):
            # WHEN
            workspace = get_current_workspace()

            # THEN
            assert workspace == "trading"

    def test_get_current_workspace_retorna_default_quando_nao_definido(self):
        """
        DOC: ADR024 - Fallback para workspace padrão ("core") quando não definido.

        Se request.state.workspace não existe, deve retornar "core".
        """
        # GIVEN - request state sem workspace
        mock_request = Mock()
        mock_request.state.workspace = None

        with patch('runtime.workspace.workspace_context.get_request', return_value=mock_request):
            # WHEN
            workspace = get_current_workspace()

            # THEN
            assert workspace == "core"

    def test_get_current_workspace_sem_request_ativo_retorna_default(self):
        """
        DOC: ADR024 - Fallback para "core" quando não há request ativo.

        Fora de contexto de request (ex: worker threads), retorna "core".
        """
        # GIVEN - sem request ativo
        with patch('runtime.workspace.workspace_context.get_request', return_value=None):
            # WHEN
            workspace = get_current_workspace()

            # THEN
            assert workspace == "core"

    def test_set_current_workspace_define_workspace_no_contexto(self):
        """
        DOC: ADR024 - set_current_workspace() define workspace para testes/worker.

        Permite definir workspace explicitamente para contextos sem request.
        """
        # GIVEN - sem request ativo
        with patch('runtime.workspace.workspace_context.get_request', return_value=None):
            from runtime.workspace.workspace_context import _current_workspace

            # Limpar contexto anterior
            token = _current_workspace.set(None)

            # WHEN
            set_current_workspace("trading")

            # THEN
            assert _current_workspace.get() == "trading"

            # Cleanup
            _current_workspace.reset(token)

    def test_set_current_workspace_com_none_limpa_contexto(self):
        """
        DOC: ADR024 - set_current_workspace(None) limpa contexto explícito.
        """
        # GIVEN - contexto definido
        from runtime.workspace.workspace_context import _current_workspace

        token = _current_workspace.set("trading")
        assert _current_workspace.get() == "trading"

        # WHEN
        set_current_workspace(None)

        # THEN
        assert _current_workspace.get() is None

        # Cleanup
        _current_workspace.reset(token)
