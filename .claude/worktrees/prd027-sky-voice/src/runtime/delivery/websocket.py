# -*- coding: utf-8 -*-
"""
WebSocket Console - Streaming em tempo real do output do agente.

PRD019: Endpoint /ws/console para streaming de mensagens do agente.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Set

from fastapi import WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel


class ConsoleMessage(BaseModel):
    """
    Mensagem WebSocket para o console.

    Attributes:
        timestamp: ISO timestamp da mensagem
        job_id: ID do job associado
        level: Nível da mensagem (info, warning, error, tool_use)
        message: Conteúdo da mensagem
        metadata: Metadados adicionais
    """

    timestamp: str
    job_id: str
    level: str  # info, warning, error, tool_use
    message: str
    metadata: dict[str, Any] | None = None

    def model_dump_json(self) -> str:
        """Converte para JSON string."""
        return json.dumps({
            "timestamp": self.timestamp,
            "job_id": self.job_id,
            "level": self.level,
            "message": self.message,
            "metadata": self.metadata,
        })


class WebSocketConsoleManager:
    """
    Gerenciador de conexões WebSocket ativas.

    Mantém mapa de job_id -> set de WebSockets para broadcast de mensagens.
    """

    def __init__(self) -> None:
        """Inicializa gerenciador com mapa vazio de conexões."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, job_id: str) -> None:
        """
        Aceita e registra nova conexão WebSocket.

        Args:
            websocket: Instância do FastAPI WebSocket
            job_id: ID do job para associar à conexão
        """
        await websocket.accept()

        async with self._lock:
            if job_id not in self.active_connections:
                self.active_connections[job_id] = set()
            self.active_connections[job_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, job_id: str) -> None:
        """
        Remove conexão WebSocket do gerenciador.

        Args:
            websocket: Instância do FastAPI WebSocket
            job_id: ID do job associado
        """
        async with self._lock:
            if job_id in self.active_connections:
                self.active_connections[job_id].discard(websocket)
                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]

    async def broadcast(self, job_id: str, message: ConsoleMessage) -> None:
        """
        Envia mensagem para todas as conexões de um job.

        Args:
            job_id: ID do job
            message: Mensagem a ser enviada
        """
        async with self._lock:
            connections = self.active_connections.get(job_id, set()).copy()

        # Envia para todas as conexões fora do lock
        for connection in connections:
            try:
                await connection.send_text(message.model_dump_json())
            except Exception:
                # Conexão pode estar fechada, remove silenciosamente
                await self.disconnect(connection, job_id)

    async def broadcast_raw(
        self,
        job_id: str,
        level: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Helper para broadcast com criação de ConsoleMessage.

        Args:
            job_id: ID do job
            level: Nível da mensagem
            message: Conteúdo da mensagem
            metadata: Metadados adicionais
        """
        msg = ConsoleMessage(
            timestamp=datetime.now().isoformat(),
            job_id=job_id,
            level=level,
            message=message,
            metadata=metadata,
        )
        await self.broadcast(job_id, msg)

    def get_connection_count(self, job_id: str) -> int:
        """
        Retorna número de conexões ativas para um job.

        Args:
            job_id: ID do job

        Returns:
            Número de conexões ativas
        """
        return len(self.active_connections.get(job_id, set()))

    def get_all_jobs(self) -> list[str]:
        """
        Retorna lista de todos os jobs com conexões ativas.

        Returns:
            Lista de job_ids
        """
        return list(self.active_connections.keys())


# Singleton
_console_manager: WebSocketConsoleManager | None = None


def get_console_manager() -> WebSocketConsoleManager:
    """
    Retorna gerenciador de console (singleton).

    Returns:
        Instância única de WebSocketConsoleManager
    """
    global _console_manager
    if _console_manager is None:
        _console_manager = WebSocketConsoleManager()
    return _console_manager


def create_console_router() -> Any:
    """
    Cria router FastAPI com endpoints WebSocket.

    Endpoints:
        - /ws/console: WebSocket principal para streaming de console
        - /ws/console/status: Status de conexões ativas

    Returns:
        FastAPI APIRouter com endpoints WebSocket
    """
    from fastapi import APIRouter

    router = APIRouter(prefix="/ws", tags=["WebSocket"])
    manager = get_console_manager()

    @router.websocket("/console")
    async def console_websocket(
        websocket: WebSocket,
        job_id: str = Query(..., description="ID do job para streaming"),
    ):
        """
        Endpoint WebSocket principal para streaming de console.

        Args:
            websocket: Conexão WebSocket
            job_id: ID do job para associar à conexão

        Example:
            ```python
            import websockets

            uri = "ws://localhost:8000/ws/console?job_id=test-123"
            async with websockets.connect(uri) as ws:
                while True:
                    msg = await ws.recv()
                    print(msg)
            ```
        """
        await manager.connect(websocket, job_id)

        # Envia mensagem de boas-vindas
        await manager.broadcast_raw(
            job_id,
            "info",
            f"Conexão WebSocket estabelecida para job {job_id}",
        )

        try:
            # Mantém conexão aberta, recebendo ping/pong
            while True:
                await websocket.receive_text()

        except WebSocketDisconnect:
            await manager.disconnect(websocket, job_id)

    @router.get("/console/status")
    async def console_status():
        """
        Retorna status das conexões WebSocket ativas.

        Returns:
            Dict com contagem de conexões por job e lista de jobs ativos
        """
        jobs = manager.get_all_jobs()
        status = {
            "active_jobs": len(jobs),
            "connections_by_job": {
                job_id: manager.get_connection_count(job_id)
                for job_id in jobs
            },
        }
        return status

    return router
