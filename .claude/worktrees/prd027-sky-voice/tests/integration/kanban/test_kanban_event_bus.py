# -*- coding: utf-8 -*-
"""
Testes de Integração: KanbanEventBus.

DOC: PRD024 Task 7 - EventBus para SSE
DOC: core/kanban/application/kanban_event_bus.py

Testes para o sistema de pub/sub que conecta operações CRUD ao SSE.
"""
import pytest
import asyncio
from datetime import datetime

from core.kanban.application.kanban_event_bus import (
    KanbanEventBus,
    KanbanEvent,
)


@pytest.fixture
def event_bus() -> KanbanEventBus:
    """Retorna instância do EventBus."""
    return KanbanEventBus.get_instance()


class TestKanbanEventBus:
    """
    Testes do KanbanEventBus.

    Verifica funcionamento do pub/sub com isolamento por workspace.
    """

    def test_singleton_deve_retornar_mesma_instancia(self, event_bus: KanbanEventBus):
        """
        DOC: kanban_event_bus.py - get_instance()

        Testa que:
        - EventBus é um singleton
        - Múltiplas chamadas retornam mesma instância
        """
        another = KanbanEventBus.get_instance()
        assert another is event_bus
        assert id(another) == id(event_bus)

    @pytest.mark.asyncio
    async def test_publish_deve_adicionar_evento_na_fila(
        self, event_bus: KanbanEventBus
    ):
        """
        DOC: kanban_event_bus.py - publish()

        Testa que:
        - Evento publicado é adicionado à fila do workspace
        - Evento contém dados corretos (event_type, data, workspace_id)
        """
        # Act: Publica evento
        await event_bus.publish(
            event_type="card_created",
            data={"id": "test-123", "title": "Test Card"},
            workspace_id="test-workspace"
        )

        # Assert: Verifica que evento está na fila
        queue = event_bus._get_or_create_queue("test-workspace")
        assert not queue.empty()

        event = await queue.get()
        assert event.event_type == "card_created"
        assert event.data["id"] == "test-123"
        assert event.workspace_id == "test-workspace"
        assert isinstance(event.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_subscribe_deve_yield_eventos_publicados(
        self, event_bus: KanbanEventBus
    ):
        """
        DOC: kanban_event_bus.py - subscribe()

        Testa que:
        - Subscriber recebe eventos publicados
        - Generator yield eventos em ordem
        """
        # Arrange: Cria task que publica eventos
        async def publish_events():
            await asyncio.sleep(0.1)  # Pequeno delay
            await event_bus.publish(
                "card_created",
                {"id": "123"},
                "test-ws"
            )
            await event_bus.publish(
                "card_updated",
                {"id": "123", "title": "Updated"},
                "test-ws"
            )

        publisher_task = asyncio.create_task(publish_events())

        # Act: Subscribe e coleta eventos
        events_received = []
        async for event in event_bus.subscribe("test-ws"):
            events_received.append(event)
            if len(events_received) >= 2:
                break  # Para após receber 2 eventos

        await publisher_task

        # Assert: Verifica eventos recebidos
        assert len(events_received) == 2
        assert events_received[0].event_type == "card_created"
        assert events_received[0].data["id"] == "123"
        assert events_received[1].event_type == "card_updated"
        assert events_received[1].data["title"] == "Updated"

    @pytest.mark.asyncio
    async def test_isolamento_por_workspace(
        self, event_bus: KanbanEventBus
    ):
        """
        DOC: ADR024 - Workspace isolation
        DOC: kanban_event_bus.py - Filas por workspace

        Testa que:
        - Eventos de workspaces diferentes são isolados
        - Subscriber do workspace A não recebe eventos do workspace B
        """
        # Arrange: Publica evento no workspace A
        await event_bus.publish(
            "card_created",
            {"id": "card-a"},
            "workspace-a"
        )

        # Act: Subscribe no workspace B
        events_b = []
        try:
            # Timeout curto - não deve receber nada
            async with asyncio.timeout(0.5):
                async for event in event_bus.subscribe("workspace-b"):
                    events_b.append(event)
        except (asyncio.TimeoutError, TimeoutError):
            pass

        # Assert: Workspace B não recebeu evento do workspace A
        assert len(events_b) == 0

        # Mas workspace A recebe
        events_a = []
        async for event in event_bus.subscribe("workspace-a"):
            events_a.append(event)
            if len(events_a) >= 1:
                break

        assert len(events_a) == 1
        assert events_a[0].event_type == "card_created"

    @pytest.mark.asyncio
    async def test_subscribers_count(
        self, event_bus: KanbanEventBus
    ):
        """
        DOC: kanban_event_bus.py - get_subscribers_count()

        Testa que:
        - Contador de subscribers incrementa corretamente
        - Contador funciona para múltiplos workspaces
        """
        # Arrange: Usa workspaces únicos
        ws_a = "test-ws-count-a"
        ws_b = "test-ws-count-b"

        # Assert: Sem subscribers inicialmente
        assert event_bus.get_subscribers_count(ws_a) == 0
        assert event_bus.get_subscribers_count(ws_b) == 0

        # Act: Cria subscribers para workspace A
        async def sub_a():
            async for _ in event_bus.subscribe(ws_a):
                return  # Sai imediatamente

        task_a = asyncio.create_task(sub_a())
        await asyncio.sleep(0.05)  # Deixa iniciar

        # Assert: 1 subscriber em A, 0 em B
        assert event_bus.get_subscribers_count(ws_a) == 1
        assert event_bus.get_subscribers_count(ws_b) == 0

        # Cleanup: Cancela task
        task_a.cancel()
        try:
            await task_a
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_to_sse_format(self):
        """
        DOC: kanban_event_bus.py - to_sse_format()

        Testa que:
        - Evento é convertido para formato SSE correto
        - Formato: event: <type>\ndata: <json>\n\n
        """
        # Arrange: Cria evento
        event = KanbanEvent(
            event_type="card_created",
            data={"id": "123", "title": "Test"},
            workspace_id="core"
        )

        # Act: Converte para SSE
        sse_format = event.to_sse_format()

        # Assert: Verifica formato
        assert sse_format.startswith("event: card_created\ndata: ")
        assert sse_format.endswith("\n\n")
        assert '"id": "123"' in sse_format
        assert '"title": "Test"' in sse_format

    @pytest.mark.asyncio
    async def test_subscribe_timeout_permite_heartbeat(
        self, event_bus: KanbanEventBus
    ):
        """
        DOC: kanban_event_bus.py - subscribe() com timeout

        Testa que:
        - Subscribe retorna com timeout se não há eventos
        - Permite enviar heartbeat entre eventos
        """
        # Act: Subscribe sem publicar nada
        events_received = []
        try:
            async with asyncio.timeout(0.5):
                async for event in event_bus.subscribe("empty-ws"):
                    events_received.append(event)
        except (asyncio.TimeoutError, TimeoutError):
            pass

        # Assert: Não recebeu eventos (timeout)
        assert len(events_received) == 0

        # Mas após publicar, recebe
        await event_bus.publish("card_created", {}, "empty-ws")

        async for event in event_bus.subscribe("empty-ws"):
            events_received.append(event)
            break

        assert len(events_received) == 1
