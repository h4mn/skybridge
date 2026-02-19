# -*- coding: utf-8 -*-
"""
Fixtures para testes de delivery (API routes).
"""

import sys
from pathlib import Path

# Adiciona src ao path ANTES de qualquer import
# Isso é necessário porque alguns módulos importam runtime.observability
src_path = Path(__file__).parent.parent.parent.parent / "src"
apps_path = Path(__file__).parent.parent.parent.parent / "apps"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
if str(apps_path) not in sys.path:
    sys.path.insert(0, str(apps_path))


def pytest_configure(config):
    """
    Hook executado antes dos testes para garantir o path correto.

    Isso garante que o módulo runtime.observability possa ser importado
    durante a carga dos módulos do servidor webhook.
    """
    # Já adicionamos o path no nível do módulo, mas este hook
    # garante que o path esteja disponível para todos os testes


import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client():
    """
    Cliente HTTP assíncrono para testes de API.

    Este fixture cria um client que não inicia o servidor
    real, mas simula requests para a aplicação FastAPI.
    """
    from runtime.bootstrap.app import get_app

    app = get_app()

    # Usa ASGITransport para evitar warnings de async
    transport = ASGITransport(app=app.app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as ac:
        yield ac
