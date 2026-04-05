# -*- coding: utf-8 -*-
"""Testes de integração para os endpoints da Paper Trading API.

Testa os endpoints principais da API REST de paper trading.
"""
import pytest
from fastapi.testclient import TestClient

from src.core.paper.facade.api.app import create_app


@pytest.fixture
def client():
    """Cliente de teste para a API."""
    app = create_app()
    return TestClient(app)


class TestMercadoEndpoints:
    """Testes para endpoints de mercado."""

    def test_health_check(self, client):
        """Teste: health check retorna status healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "paper-trading-api"

    def test_cotacao_endpoint_format(self, client):
        """Teste: endpoint de cotacao retorna formato correto."""
        response = client.get("/api/v1/paper/mercado/cotacao/BTC-USD")
        # Aceita 200 (sucesso) ou 502 (Yahoo down)
        assert response.status_code in [200, 502]

        if response.status_code == 200:
            data = response.json()
            assert "ticker" in data
            assert "preco" in data
            assert data["ticker"] == "BTC-USD"

    def test_cotacao_ticker_invalido(self, client):
        """Teste: ticker invalido retorna erro."""
        response = client.get("/api/v1/paper/mercado/cotacao/TICKER_INVALIDO_12345")
        # Pode retornar 404 ou 502 dependendo do Yahoo
        assert response.status_code in [404, 502]

    def test_historico_endpoint_format(self, client):
        """Teste: endpoint de historico retorna formato correto."""
        response = client.get("/api/v1/paper/mercado/historico/BTC-USD?dias=7")
        assert response.status_code in [200, 502]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_historico_dias_invalido(self, client):
        """Teste: dias fora do range retorna erro."""
        response = client.get("/api/v1/paper/mercado/historico/BTC-USD?dias=500")
        assert response.status_code == 400


class TestPortfolioEndpoints:
    """Testes para endpoints de portfolio."""

    def test_consultar_portfolio(self, client):
        """Teste: consultar portfolio retorna estrutura correta."""
        response = client.get("/api/v1/paper/portfolio/")
        assert response.status_code == 200
        data = response.json()
        # Verifica campos esperados
        assert "saldo_atual" in data or "saldo_disponivel" in data

    def test_listar_ordens(self, client):
        """Teste: listar ordens retorna estrutura correta."""
        response = client.get("/api/v1/paper/ordens/")
        assert response.status_code == 200
        data = response.json()
        assert "ordens" in data
        assert "total" in data


class TestOrdensEndpoints:
    """Testes para endpoints de ordens."""

    def test_criar_ordem_sem_saldo(self, client):
        """Teste: criar ordem com valor muito alto deve falhar."""
        response = client.post(
            "/api/v1/paper/ordens/",
            json={
                "ticker": "BTC-USD",
                "lado": "COMPRA",
                "quantidade": 10000  # Muito alto, deve falhar por saldo
            }
        )
        # Pode retornar 422 (saldo insuficiente) ou 502 (Yahoo down)
        assert response.status_code in [422, 502]
