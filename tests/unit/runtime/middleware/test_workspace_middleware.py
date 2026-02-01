# -*- coding: utf-8 -*-
"""
Testes para WorkspaceMiddleware.

TDD Estrito: Testes que documentam o comportamento esperado do middleware.

DOC: ADR024 - Header X-Workspace define workspace ativo.
DOC: PB013 - Workspaces disabled=False retornam 404.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from starlette.datastructures import Headers

from runtime.config.workspace_config import WorkspaceConfig, Workspace
from runtime.middleware.workspace_middleware import WorkspaceMiddleware


@pytest.fixture
def mock_workspace():
    """Fixture: Workspace mock simples."""
    ws = Mock(spec=Workspace)
    ws.id = "core"
    ws.name = "Skybridge Core"
    ws.path = "workspace/core"
    ws.enabled = True
    return ws


class MockRequest:
    """Request mock para testes que simula FastAPI Request."""

    def __init__(self, headers: dict | None = None):
        # Simula Headers do FastAPI/starlette (case-insensitive)
        self.headers = Headers(headers or {})
        self.state = MagicMock()

    async def call_next(self, request):
        """Mock do call_next."""
        response = Mock()
        return response


@pytest.mark.asyncio
class TestWorkspaceMiddlewareHeader:
    """Testa leitura do header X-Workspace."""

    async def test_middleware_reads_x_workspace_header(self):
        """
        DOC: ADR024 - Header X-Workspace define workspace ativo.

        O middleware deve ler o header X-Workspace e definir
        request.state.workspace com o valor do header.
        """
        trading_ws = Mock(
            id="trading",
            path="workspace/trading",
            enabled=True
        )
        core_ws = Mock(
            id="core",
            path="workspace/core",
            enabled=True
        )

        config = Mock(spec=WorkspaceConfig)
        config.default = "core"
        config.workspaces = {
            "core": core_ws,
            "trading": trading_ws,
        }

        mock_app = Mock()
        middleware = WorkspaceMiddleware(app=mock_app, config=config)

        request = MockRequest(headers={"X-Workspace": "trading"})
        await middleware(request, request.call_next)

        assert request.state.workspace == "trading"

    async def test_middleware_defaults_to_core_without_header(self):
        """
        DOC: ADR024 - Sem header, usa 'core' como padrão.

        Se o header X-Workspace não estiver presente,
        deve usar 'core' como padrão.
        """
        core_ws = Mock(
            id="core",
            path="workspace/core",
            enabled=True
        )

        config = Mock(spec=WorkspaceConfig)
        config.default = "core"
        config.workspaces = {
            "core": core_ws,
        }

        mock_app = Mock()
        middleware = WorkspaceMiddleware(app=mock_app, config=config)

        request = MockRequest(headers={})
        await middleware(request, request.call_next)

        assert request.state.workspace == "core"

    async def test_middleware_case_insensitive(self):
        """
        DOC: Header X-Workspace é case-insensitive.

        Deve aceitar x-workspace, X-Workspace, X-WORKSPACE, etc.
        """
        core_ws = Mock(
            id="core",
            path="workspace/core",
            enabled=True
        )

        config = Mock(spec=WorkspaceConfig)
        config.default = "core"
        config.workspaces = {
            "core": core_ws,
        }

        mock_app = Mock()
        middleware = WorkspaceMiddleware(app=mock_app, config=config)

        request = MockRequest(headers={"x-workspace": "core"})
        await middleware(request, request.call_next)

        assert request.state.workspace == "core"


@pytest.mark.asyncio
class TestWorkspaceMiddlewareValidation:
    """Testa validação de workspace."""

    async def test_middleware_returns_404_for_unknown_workspace(self):
        """
        DOC: ADR024 - Workspace inexistente retorna 404.

        Se o workspace especificado não existir, deve levantar HTTPException.
        """
        from fastapi import HTTPException

        core_ws = Mock(
            id="core",
            path="workspace/core",
            enabled=True
        )

        config = Mock(spec=WorkspaceConfig)
        config.default = "core"
        config.workspaces = {
            "core": core_ws,
        }

        mock_app = Mock()
        middleware = WorkspaceMiddleware(app=mock_app, config=config)

        request = MockRequest(headers={"X-Workspace": "nonexistent"})

        with pytest.raises(HTTPException) as exc:
            await middleware(request, request.call_next)

        assert exc.value.status_code == 404
        assert "not found" in str(exc.value.detail).lower()

    async def test_middleware_skips_disabled_workspace(self):
        """
        DOC: PB013 - Workspaces disabled=False retornam 404.

        Workspaces com enabled=False não devem ser acessíveis.
        """
        from fastapi import HTTPException

        core_ws = Mock(
            id="core",
            path="workspace/core",
            enabled=True
        )
        disabled_ws = Mock(
            id="disabled",
            path="workspace/disabled",
            enabled=False
        )

        config = Mock(spec=WorkspaceConfig)
        config.default = "core"
        config.workspaces = {
            "core": core_ws,
            "disabled": disabled_ws,
        }

        mock_app = Mock()
        middleware = WorkspaceMiddleware(app=mock_app, config=config)

        request = MockRequest(headers={"X-Workspace": "disabled"})

        with pytest.raises(HTTPException) as exc:
            await middleware(request, request.call_next)

        assert exc.value.status_code == 404


@pytest.mark.asyncio
class TestWorkspaceMiddlewareEnvLoading:
    """Testa carregamento de .env do workspace."""

    @patch("runtime.middleware.workspace_middleware.load_dotenv")
    @patch("pathlib.Path.exists", return_value=True)
    async def test_middleware_loads_workspace_env(self, mock_exists, mock_load_dotenv):
        """
        DOC: ADR024 - Middleware carrega .env do workspace.

        Deve chamar load_dotenv com o caminho do .env do workspace.
        """
        core_ws = Mock(
            id="core",
            path="workspace/core",
            enabled=True
        )

        config = Mock(spec=WorkspaceConfig)
        config.default = "core"
        config.workspaces = {
            "core": core_ws,
        }

        mock_app = Mock()
        middleware = WorkspaceMiddleware(app=mock_app, config=config)

        request = MockRequest(headers={"X-Workspace": "core"})
        await middleware(request, request.call_next)

        # Verifica que load_dotenv foi chamado
        mock_load_dotenv.assert_called_once()

    @patch("runtime.middleware.workspace_middleware.load_dotenv")
    @patch("pathlib.Path.exists", return_value=True)
    async def test_middleware_loads_env_with_override(self, mock_exists, mock_load_dotenv):
        """
        DOC: load_dotenv deve usar override=True.

        Variáveis do workspace devem sobrescrever as existentes.
        """
        core_ws = Mock(
            id="core",
            path="workspace/core",
            enabled=True
        )

        config = Mock(spec=WorkspaceConfig)
        config.default = "core"
        config.workspaces = {
            "core": core_ws,
        }

        mock_app = Mock()
        middleware = WorkspaceMiddleware(app=mock_app, config=config)

        request = MockRequest(headers={"X-Workspace": "core"})
        await middleware(request, request.call_next)

        # Verifica que override=True foi passado
        call_kwargs = mock_load_dotenv.call_args.kwargs
        assert call_kwargs.get("override") is True


@pytest.mark.asyncio
class TestWorkspaceMiddlewareCallChain:
    """Testa que o middleware continua a chain."""

    async def test_middleware_calls_next(self):
        """
        DOC: Middleware deve chamar call_next.

        O middleware não deve interromper a chain de middlewares.
        """
        core_ws = Mock(
            id="core",
            path="workspace/core",
            enabled=True
        )

        config = Mock(spec=WorkspaceConfig)
        config.default = "core"
        config.workspaces = {
            "core": core_ws,
        }

        mock_app = Mock()
        middleware = WorkspaceMiddleware(app=mock_app, config=config)

        request = MockRequest(headers={"X-Workspace": "core"})
        response = await middleware(request, request.call_next)

        # Verifica que call_next foi chamado
        assert response is not None

    async def test_middleware_returns_response_from_call_next(self):
        """
        DOC: Response de call_next deve ser retornado.

        O middleware deve retornar a response do próximo middleware/handler.
        """
        core_ws = Mock(
            id="core",
            path="workspace/core",
            enabled=True
        )

        config = Mock(spec=WorkspaceConfig)
        config.default = "core"
        config.workspaces = {
            "core": core_ws,
        }

        mock_app = Mock()
        middleware = WorkspaceMiddleware(app=mock_app, config=config)

        request = MockRequest(headers={"X-Workspace": "core"})
        response = await middleware(request, request.call_next)

        # A response deve ser retornada
        assert response is not None
