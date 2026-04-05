# -*- coding: utf-8 -*-
"""Testes unitários para a facade HelloWorld do sandbox.

Valida que os endpoints /portfolio e /ordens funcionam sem TypeError
nem field mismatch.

DOC: src/core/paper/facade/sandbox/helloworld.py
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


def _make_facade_with_mocks() -> "HelloWorldFacade":
    """Cria HelloWorldFacade com todos os adapters mockados."""
    from src.core.paper.facade.sandbox.helloworld import HelloWorldFacade

    with patch("src.core.paper.facade.sandbox.helloworld.YahooFinanceFeed"), \
         patch("src.core.paper.facade.sandbox.helloworld.YahooCurrencyAdapter"), \
         patch("src.core.paper.facade.sandbox.helloworld.JsonFilePaperState"), \
         patch("src.core.paper.facade.sandbox.helloworld.JsonFilePaperBroker") as MockBroker, \
         patch("src.core.paper.facade.sandbox.helloworld.CriarOrdemHandler"), \
         patch("src.core.paper.facade.sandbox.helloworld.ConsultarCotacaoHandler"), \
         patch("src.core.paper.facade.sandbox.helloworld.ConsultarHistoricoHandler"), \
         patch("src.core.paper.facade.sandbox.helloworld.ConsultarPortfolioHandler"), \
         patch("src.core.paper.facade.sandbox.helloworld.ConsultarOrdensHandler"):
        facade = HelloWorldFacade()
    return facade


class TestPortfolioEndpoint:
    """Testa que /portfolio calcula PnL sem TypeError float vs Decimal."""

    def test_portfolio_com_posicoes_nao_gera_type_error(self):
        """
        Bug reproduzido: TypeError: unsupported operand type(s) for -: 'float' and 'Decimal'

        Cenário: listar_posicoes_marcadas() retorna float em valor_atual,
        e SALDO_INICIAL é Decimal. A subtração lança TypeError.

        Esperado: endpoint retorna 200 com PnL calculado corretamente.
        """
        facade = _make_facade_with_mocks()

        # Configura o mock do broker para simular posições com floats
        facade.broker.listar_posicoes_marcadas = AsyncMock(return_value=[
            {
                "ticker": "PETR4.SA",
                "quantidade": 100,
                "preco_medio": 49.26,
                "preco_atual": 52.00,
                "custo_total": 4926.0,
                "valor_atual": 5200.0,
                "pnl": 274.0,
                "pnl_percentual": 5.56,
            }
        ])
        facade.broker.saldo = 50000.0  # float

        client = TestClient(facade.app)

        # Este request causava TypeError no código original
        response = client.get("/portfolio")

        assert response.status_code == 200, f"Esperado 200, obtido {response.status_code}: {response.text}"
        data = response.json()
        assert "pnl" in data
        assert "patrimonio_total" in data


class TestOrdensEndpoint:
    """Testa que /ordens mapeia campos do broker para o schema correto."""

    def test_ordens_retorna_lista_sem_validation_error(self):
        """
        Bug reproduzido: ValidationError — field 'ordem_id' required, got 'id'.

        Cenário: broker.listar_ordens() retorna dicts com chave 'id',
        mas OrdemResponse espera 'ordem_id'.

        Esperado: endpoint retorna 200 com ordens mapeadas.
        """
        facade = _make_facade_with_mocks()

        facade.broker.listar_ordens = MagicMock(return_value=[
            {
                "id": "abc-123",
                "ticker": "PETR4.SA",
                "lado": "COMPRA",
                "quantidade": 100,
                "preco_execucao": 49.26,
                "valor_total": 4926.0,
                "status": "EXECUTADA",
                "timestamp": "2026-03-28T15:43:56",
            }
        ])

        client = TestClient(facade.app)

        # Este request causava ValidationError no código original
        response = client.get("/ordens")

        assert response.status_code == 200, f"Esperado 200, obtido {response.status_code}: {response.text}"
        data = response.json()
        assert len(data) == 1
        assert data[0]["ordem_id"] == "abc-123"
