"""
Testes unitários para Eventos de Domínio.

Testa:
- DomainEvent base
- OrdemCriada, OrdemExecutada, OrdemCancelada
- StopLossAcionado, PosicaoAtualizada
- Serialização to_dict/from_dict
"""

from datetime import datetime

import pytest

from src.core.paper.domain.events import (
    DomainEvent,
    OrdemCriada,
    OrdemExecutada,
    OrdemCancelada,
    StopLossAcionado,
    PosicaoAtualizada,
    Lado,
)


class TestDomainEvent:
    """Testes para DomainEvent base."""

    def test_domain_event_cria_timestamp_automatico(self):
        """DomainEvent deve criar timestamp automaticamente."""
        before = datetime.now()
        event = DomainEvent()
        after = datetime.now()

        assert before <= event.occurred_at <= after

    def test_domain_event_event_type_é_nome_classe(self):
        """event_type deve ser o nome da classe."""
        event = OrdemCriada(
            ordem_id="123",
            ticker="PETR4",
            lado=Lado.COMPRA,
            quantidade=100
        )

        assert event.event_type == "OrdemCriada"

    def test_domain_event_to_dict(self):
        """to_dict deve serializar evento corretamente."""
        event = OrdemCriada(
            ordem_id="123",
            ticker="PETR4",
            lado=Lado.COMPRA,
            quantidade=100,
            preco_limit=25.50
        )

        data = event.to_dict()

        assert data["ordem_id"] == "123"
        assert data["ticker"] == "PETR4"
        assert data["lado"] == "compra"
        assert data["quantidade"] == 100
        assert data["preco_limit"] == 25.50
        assert "occurred_at" in data
        assert data["event_type"] == "OrdemCriada"

    def test_domain_event_from_dict(self):
        """from_dict deve desserializar evento corretamente."""
        data = {
            "ordem_id": "123",
            "ticker": "PETR4",
            "lado": "compra",
            "quantidade": 100,
            "preco_limit": 25.50,
            "occurred_at": "2026-03-31T16:00:00",
            "event_type": "OrdemCriada"
        }

        event = OrdemCriada.from_dict(data)

        assert event.ordem_id == "123"
        assert event.ticker == "PETR4"
        assert event.lado == "compra"
        assert event.quantidade == 100
        assert event.preco_limit == 25.50


class TestOrdemCriada:
    """Testes para OrdemCriada."""

    def test_ordem_criada_com_atributos_obrigatorios(self):
        """OrdemCriada deve criar com atributos obrigatórios."""
        event = OrdemCriada(
            ordem_id="ordem-001",
            ticker="PETR4",
            lado=Lado.COMPRA,
            quantidade=100
        )

        assert event.ordem_id == "ordem-001"
        assert event.ticker == "PETR4"
        assert event.lado == "compra"
        assert event.quantidade == 100

    def test_ordem_criada_com_preco_limit(self):
        """OrdemCriada pode ter preco_limit opcional."""
        event = OrdemCriada(
            ordem_id="ordem-001",
            ticker="PETR4",
            lado=Lado.COMPRA,
            quantidade=100,
            preco_limit=25.50
        )

        assert event.preco_limit == 25.50


class TestOrdemExecutada:
    """Testes para OrdemExecutada."""

    def test_ordem_executada_atributos(self):
        """OrdemExecutada deve criar com todos os atributos."""
        event = OrdemExecutada(
            ordem_id="ordem-001",
            ticker="PETR4",
            lado=Lado.VENDA,
            quantidade_executada=50,
            preco_execucao=26.00
        )

        assert event.ordem_id == "ordem-001"
        assert event.ticker == "PETR4"
        assert event.lado == "venda"
        assert event.quantidade_executada == 50
        assert event.preco_execucao == 26.00


class TestOrdemCancelada:
    """Testes para OrdemCancelada."""

    def test_ordem_cancelada_atributos(self):
        """OrdemCancelada deve ter ordem_id e motivo."""
        event = OrdemCancelada(
            ordem_id="ordem-001",
            motivo="usuario"
        )

        assert event.ordem_id == "ordem-001"
        assert event.motivo == "usuario"


class TestStopLossAcionado:
    """Testes para StopLossAcionado."""

    def test_stop_loss_atributos(self):
        """StopLossAcionado deve ter dados da perda."""
        event = StopLossAcionado(
            ticker="BTCBRL",
            preco_trigger=285000.00,
            perda_percentual=1.5,
            quantidade=1
        )

        assert event.ticker == "BTCBRL"
        assert event.preco_trigger == 285000.00
        assert event.perda_percentual == 1.5
        assert event.quantidade == 1


class TestPosicaoAtualizada:
    """Testes para PosicaoAtualizada."""

    def test_posicao_atualizada_atributos(self):
        """PosicaoAtualizada deve ter dados da mudança."""
        event = PosicaoAtualizada(
            ticker="PETR4",
            quantidade_anterior=0,
            quantidade_nova=100,
            preco_medio_novo=25.50,
            preco_atual=26.00,
            pnl_nao_realizado=50.00
        )

        assert event.ticker == "PETR4"
        assert event.quantidade_anterior == 0
        assert event.quantidade_nova == 100
        assert event.preco_medio_novo == 25.50
        assert event.preco_atual == 26.00
        assert event.pnl_nao_realizado == 50.00
