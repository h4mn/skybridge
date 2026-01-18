# -*- coding: utf-8 -*-
"""
Fixtures para testes de delivery (API routes).
"""

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
