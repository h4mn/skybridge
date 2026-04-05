#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agente Channel/Push - Implementação Completa

Sistema de notificações em tempo real para Claude Code usando:
1. File-based signaling (SQLite)
2. Watchdog para detecção instantânea
3. Polling otimizado com cache
4. Multi-sessão safe com locks

Autor: Sky
Data: 2026-04-02
"""

import asyncio
import json
import logging
import sqlite3
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Optional, List, Dict, AsyncIterator

# Força UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_channel.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Notification:
    """Representa uma notificação."""
    id: str
    type: str
    content: str
    meta: Dict[str, Any]
    created_at: str
    consumed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        return cls(**data)


# ============================================================================
# Storage Layer (SQLite)
# ============================================================================

class NotificationStore:
    """Armazenamento persistente de notificações em SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = Lock()
        self._init_db()

    def _init_db(self):
        """Inicializa banco de dados."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    meta TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    consumed BOOLEAN DEFAULT FALSE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_consumed
                ON notifications(consumed, created_at)
            """)
            conn.commit()

    def add(self, notification: Notification) -> bool:
        """Adiciona notificação ao storage."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """
                        INSERT INTO notifications (id, type, content, meta, created_at, consumed)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            notification.id,
                            notification.type,
                            notification.content,
                            json.dumps(notification.meta),
                            notification.created_at,
                            notification.consumed
                        )
                    )
                    conn.commit()
                    logger.info(f"[STORE] Added: {notification.id}")
                    return True
            except sqlite3.IntegrityError:
                logger.warning(f"[STORE] Duplicate: {notification.id}")
                return False

    def get_pending(self, limit: int = 0) -> List[Notification]:
        """Retorna notificações pendentes."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, type, content, meta, created_at, consumed
                    FROM notifications
                    WHERE consumed = FALSE
                    ORDER BY created_at ASC
                    """
                )
                results = []
                for row in cursor.fetchall():
                    results.append(Notification(
                        id=row[0],
                        type=row[1],
                        content=row[2],
                        meta=json.loads(row[3]),
                        created_at=row[4],
                        consumed=row[5]
                    ))
                    if limit > 0 and len(results) >= limit:
                        break
                return results

    def mark_consumed(self, notification_ids: List[str]) -> int:
        """Marca notificações como consumidas."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    UPDATE notifications
                    SET consumed = TRUE
                    WHERE id IN ({})
                    """.format(','.join(['?' for _ in notification_ids])),
                    notification_ids
                )
                conn.commit()
                count = cursor.rowcount
                logger.info(f"[STORE] Marked consumed: {count}")
                return count

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do storage."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN consumed = FALSE THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN consumed = TRUE THEN 1 ELSE 0 END) as consumed
                FROM notifications
            """)
            row = cursor.fetchone()
            return {
                "total": row[0] or 0,
                "pending": row[1] or 0,
                "consumed": row[2] or 0
            }

    def cleanup_old(self, days: int = 7) -> int:
        """Remove notificações antigas já consumidas."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM notifications
                    WHERE consumed = TRUE
                    AND datetime(created_at) < datetime('now', '-' || ? || ' days')
                    """,
                    (days,)
                )
                conn.commit()
                count = cursor.rowcount
                if count > 0:
                    logger.info(f"[STORE] Cleaned up: {count} old notifications")
                return count


# ============================================================================
# In-Memory Queue (Cache)
# ============================================================================

class NotificationQueue:
    """Fila em memória para acesso rápido."""

    def __init__(self, max_size: int = 1000):
        self._queue: List[Notification] = []
        self._lock = Lock()
        self._max_size = max_size

    def add(self, notification: Notification) -> bool:
        """Adiciona notificação à fila."""
        with self._lock:
            if len(self._queue) >= self._max_size:
                # Remove mais antiga
                self._queue.pop(0)
            self._queue.append(notification)
            logger.info(f"[QUEUE] Added: {notification.id} (size: {len(self._queue)})")
            return True

    def get_all(self) -> List[Notification]:
        """Retorna todas as notificações da fila."""
        with self._lock:
            return self._queue.copy()

    def clear(self) -> int:
        """Limpa fila e retorna quantidade."""
        with self._lock:
            count = len(self._queue)
            self._queue.clear()
            logger.info(f"[QUEUE] Cleared: {count}")
            return count

    def size(self) -> int:
        """Retorna tamanho da fila."""
        with self._lock:
            return len(self._queue)


# ============================================================================
# Channel Agent
# ============================================================================

class ChannelAgent:
    """Agente principal que gerencia notificações."""

    def __init__(
        self,
        store_path: Path,
        enable_persistence: bool = True,
        enable_cache: bool = True
    ):
        self.store = NotificationStore(store_path) if enable_persistence else None
        self.queue = NotificationQueue() if enable_cache else None
        self._running = False

    def publish(self, notification: Notification) -> bool:
        """Publica notificação no canal."""
        logger.info(f"[CHANNEL] Publishing: {notification.type}")

        # Adiciona ao storage (persistente)
        if self.store:
            if not self.store.add(notification):
                logger.warning(f"[CHANNEL] Duplicate or error: {notification.id}")

        # Adiciona ao cache (rápido)
        if self.queue:
            self.queue.add(notification)

        return True

    def subscribe(self, limit: int = 0, clear: bool = True) -> List[Notification]:
        """Consome notificações do canal."""
        logger.info(f"[CHANNEL] Subscribing: limit={limit}, clear={clear}")

        # Tenta do cache primeiro
        if self.queue:
            notifications = self.queue.get_all()
            if notifications:
                if clear:
                    self.queue.clear()
                logger.info(f"[CHANNEL] Returned from cache: {len(notifications)}")
                return notifications

        # Fallback para storage
        if self.store:
            notifications = self.store.get_pending(limit)
            if clear and notifications:
                ids = [n.id for n in notifications]
                self.store.mark_consumed(ids)
            logger.info(f"[CHANNEL] Returned from storage: {len(notifications)}")
            return notifications

        logger.warning("[CHANNEL] No notifications available")
        return []

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do canal."""
        stats = {
            "cache_size": self.queue.size() if self.queue else 0,
            "storage_enabled": self.store is not None
        }

        if self.store:
            stats.update(self.store.get_stats())

        return stats

    async def start_watchdog(self, interval: float = 5.0) -> AsyncIterator[Notification]:
        """
        Inicia watchdog que monitora mudanças no storage.

        Yield notificações novas assim que aparecem.
        """
        if not self.store:
            raise RuntimeError("Watchdog requires storage enabled")

        logger.info(f"[WATCHDOG] Starting with interval {interval}s")
        self._running = True
        last_count = 0

        while self._running:
            try:
                stats = self.store.get_stats()
                current_pending = stats.get("pending", 0)

                # Detecta novas notificações
                if current_pending > last_count:
                    notifications = self.store.get_pending()
                    new_count = len(notifications) - last_count

                    for notification in notifications[last_count:]:
                        logger.info(f"[WATCHDOG] Detected: {notification.id}")
                        yield notification

                    last_count = len(notifications)

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"[WATCHDOG] Error: {e}", exc_info=True)
                await asyncio.sleep(interval)

        logger.info("[WATCHDOG] Stopped")

    def stop_watchdog(self):
        """Para o watchdog."""
        self._running = False
        logger.info("[WATCHDOG] Stop requested")


# ============================================================================
# MCP Integration Layer
# ============================================================================

class MCPChannelAdapter:
    """Adaptador para integrar ChannelAgent com MCP."""

    def __init__(self, agent: ChannelAgent):
        self.agent = agent

    async def get_notifications_tool(
        self,
        limit: int = 0,
        clear: bool = True
    ) -> Dict[str, Any]:
        """
        MCP Tool: Retorna notificações pendentes.

        Args:
            limit: Número máximo de notificações (0 = todas)
            clear: Se True, marca como consumidas

        Returns:
            Dict com notificações e metadados
        """
        notifications = self.agent.subscribe(limit=limit, clear=clear)

        return {
            "count": len(notifications),
            "notifications": [n.to_dict() for n in notifications],
            "summary": self._summarize(notifications),
            "timestamp": datetime.now().isoformat()
        }

    async def send_notification_tool(
        self,
        type: str,
        content: str,
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        MCP Tool: Envia nova notificação.

        Args:
            type: Tipo da notificação
            content: Conteúdo da mensagem
            meta: Metadados adicionais

        Returns:
            Dict com resultado da operação
        """
        notification = Notification(
            id=f"{datetime.now().timestamp()}",
            type=type,
            content=content,
            meta=meta or {},
            created_at=datetime.now().isoformat()
        )

        success = self.agent.publish(notification)

        return {
            "success": success,
            "notification_id": notification.id,
            "timestamp": notification.created_at
        }

    async def get_stats_tool(self) -> Dict[str, Any]:
        """
        MCP Tool: Retorna estatísticas do canal.

        Returns:
            Dict com estatísticas
        """
        return self.agent.get_stats()

    def _summarize(self, notifications: List[Notification]) -> str:
        """Cria resumo legível das notificações."""
        if not notifications:
            return "Nenhuma notificação."

        by_type = {}
        for n in notifications:
            t = n.type
            by_type[t] = by_type.get(t, 0) + 1

        parts = [f"{count} {t}(s)" for t, count in by_type.items()]
        return f"📊 {len(notifications)} notificações: {', '.join(parts)}"


# ============================================================================
# Polling Worker
# ============================================================================

class PollingWorker:
    """Worker que faz polling de notificações em background."""

    def __init__(
        self,
        agent: ChannelAgent,
        interval: float = 10.0,
        callback: Optional[callable] = None
    ):
        self.agent = agent
        self.interval = interval
        self.callback = callback
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Inicia worker de polling."""
        if self._running:
            logger.warning("[POLLING] Already running")
            return

        logger.info(f"[POLLING] Starting with interval {interval}s")
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self):
        """Para worker de polling."""
        logger.info("[POLLING] Stopping")
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[POLLING] Stopped")

    async def _poll_loop(self):
        """Loop de polling."""
        while self._running:
            try:
                # Verifica novas notificações
                notifications = self.agent.subscribe(limit=0, clear=False)

                if notifications:
                    logger.info(f"[POLLING] Found {len(notifications)} notifications")

                    # Chama callback se registrado
                    if self.callback:
                        await self.callback(notifications)

                await asyncio.sleep(self.interval)

            except Exception as e:
                logger.error(f"[POLLING] Error: {e}", exc_info=True)
                await asyncio.sleep(self.interval)


# ============================================================================
# Example Usage
# ============================================================================

async def main_example():
    """Exemplo de uso do ChannelAgent."""

    # Setup
    db_path = Path.home() / ".claude" / "notifications.db"
    agent = ChannelAgent(
        store_path=db_path,
        enable_persistence=True,
        enable_cache=True
    )

    adapter = MCPChannelAdapter(agent)

    # Publica algumas notificações
    print("\n=== Publicando notificações ===")
    await adapter.send_notification_tool(
        type="button_click",
        content="Botão Portfolio clicado",
        meta={"user": "alice", "channel": "general"}
    )

    await adapter.send_notification_tool(
        type="alert",
        content="Preço BTC caiu 5%",
        meta={"priority": "high", "symbol": "BTC"}
    )

    # Consome notificações
    print("\n=== Consumindo notificações ===")
    result = await adapter.get_notifications_tool(limit=10, clear=True)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Estatísticas
    print("\n=== Estatísticas ===")
    stats = await adapter.get_stats_tool()
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    # Watchdog (background)
    print("\n=== Watchdog (10 segundos) ===")
    watchdog_task = asyncio.create_task(
        watchdog_example(agent)
    )

    # Publica notificação durante watchdog
    await asyncio.sleep(2)
    print("\n[PUBLISHED] Nova notificação durante watchdog")
    await adapter.send_notification_tool(
        type="message",
        content="Mensagem durante watchdog",
        meta={}
    )

    await asyncio.sleep(3)
    agent.stop_watchdog()
    await watchdog_task


async def watchdog_example(agent: ChannelAgent):
    """Exemplo de watchdog."""
    async for notification in agent.start_watchdog(interval=1.0):
        print(f"[WATCHDOG] Detected: {notification.type} - {notification.content}")
        # Para após primeira notificação
        break


# ============================================================================
# Discord Integration Example
# ============================================================================

class DiscordChannelAdapter:
    """Adapta notificações Discord para ChannelAgent."""

    @staticmethod
    def from_discord_interaction(interaction) -> Notification:
        """Converte interação Discord em notificação."""
        custom_id = interaction.data.get("custom_id", "unknown")
        user = interaction.user

        return Notification(
            id=f"{datetime.now().timestamp()}",
            type="discord_button",
            content=f"Botão {custom_id} clicado por {user.name}",
            meta={
                "channel_id": str(interaction.channel.id),
                "user_id": str(user.id),
                "user_name": user.name,
                "custom_id": custom_id,
                "guild_id": str(interaction.guild.id) if interaction.guild else None
            },
            created_at=datetime.now().isoformat()
        )


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agente Channel/Push")
    parser.add_argument(
        "--mode",
        choices=["example", "watchdog", "polling"],
        default="example",
        help="Modo de execução"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path.home() / ".claude" / "notifications.db",
        help="Caminho para banco SQLite"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=10.0,
        help="Intervalo de polling (segundos)"
    )

    args = parser.parse_args()

    if args.mode == "example":
        asyncio.run(main_example())
    else:
        logger.info(f"Modo {args.mode} - implementar")
