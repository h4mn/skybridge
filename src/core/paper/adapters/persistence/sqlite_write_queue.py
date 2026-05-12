# -*- coding: utf-8 -*-
"""
WriteQueue — Single Writer para SQLite.

Todo write (broker, tracker, workers) passa pela WriteQueue.
Nenhum componente grava direto no SQLite.

Flush periódico (flush_interval ms) ou por batch size (max_batch).
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Operation types ──


@dataclass
class SaveOrder:
    """Insere ordem na tabela orders."""
    data: Dict[str, Any] = field(default_factory=dict)
    table: str = "orders"


@dataclass
class UpdatePosition:
    """Upsert posição na tabela positions."""
    ticker: str = ""
    strategy_name: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    table: str = "positions"


@dataclass
class SavePnl:
    """Insere PnL na tabela closed_pnl."""
    data: Dict[str, Any] = field(default_factory=dict)
    table: str = "closed_pnl"


@dataclass
class SaveSignal:
    """Insere sinal na tabela signals."""
    data: Dict[str, Any] = field(default_factory=dict)
    table: str = "signals"


@dataclass
class SaveTick:
    """Insere tick raw na tabela ticks_raw."""
    data: Dict[str, Any] = field(default_factory=dict)
    table: str = "ticks_raw"


@dataclass
class SaveOhlcv:
    """Insere candle OHLCV na tabela ohlcv."""
    data: Dict[str, Any] = field(default_factory=dict)
    table: str = "ohlcv"


@dataclass
class SaveStrategyPosition:
    """Upsert posição do PositionTracker na tabela strategy_positions."""
    ticker: str = ""
    strategy_name: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    table: str = "strategy_positions"


@dataclass
class CloseStrategyPosition:
    """Fecha posição do PositionTracker (status=closed, closed_at)."""
    ticker: str = ""
    strategy_name: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    table: str = "strategy_positions"


# Union type para type hints
WriteOperation = (SaveOrder | UpdatePosition | SavePnl | SaveSignal | SaveTick | SaveOhlcv | SaveStrategyPosition | CloseStrategyPosition)


class WriteQueue:
    """
    Single writer queue para SQLite.

    asyncio.Queue + flush loop:
    - Workers enfileiram operações
    - Flush drena fila em 1 transação
    - Flush por tempo ou batch size
    """

    def __init__(
        self,
        state,
        flush_interval: float = 0.5,
        max_batch: int = 50,
    ):
        self._state = state
        self._queue: asyncio.Queue = asyncio.Queue()
        self._flush_interval = flush_interval
        self._max_batch = max_batch
        self._closed = False
        self._flush_task: Optional[asyncio.Task] = None

    async def start(self):
        """Inicia flush loop."""
        self._flush_task = asyncio.create_task(self._flush_loop())

    async def enqueue(self, op) -> None:
        """Enfileira operação de escrita."""
        await self._queue.put(op)

        # Flush agressivo: max_batch atingido OU muitos ticks acumulados
        if self._queue.qsize() >= self._max_batch:
            await self.flush()
        elif isinstance(op, SaveTick) and self._queue.qsize() > 20:
            await self.flush()

    def enqueue_nowait(self, op) -> None:
        """Enfileira operação síncrona (para uso em código não-async)."""
        self._queue.put_nowait(op)

    async def flush(self) -> None:
        """Drena fila e executa operações em batch."""
        ops = []
        while not self._queue.empty():
            try:
                op = self._queue.get_nowait()
                ops.append(op)
            except asyncio.QueueEmpty:
                break

        if not ops:
            return

        try:
            self._execute_batch(ops)
            logger.debug(f"Flush: {len(ops)} ops committed")
        except Exception as e:
            logger.error(f"Flush failed: {e}")
            for op in ops:
                await self._queue.put(op)

    def _execute_batch(self, ops) -> None:
        """Executa batch de operações em 1 transação."""
        conn = self._state._conn

        try:
            for op in ops:
                if isinstance(op, SaveOrder):
                    self._state._insert_order(op.data)
                elif isinstance(op, UpdatePosition):
                    self._state._upsert_position(op.ticker, op.strategy_name, op.data)
                elif isinstance(op, SavePnl):
                    self._state._insert_pnl(op.data)
                elif isinstance(op, SaveSignal):
                    self._state._insert_signal(op.data)
                elif isinstance(op, SaveTick):
                    self._state._insert_tick(op.data)
                elif isinstance(op, SaveOhlcv):
                    self._state._insert_ohlcv(op.data)
                elif isinstance(op, SaveStrategyPosition):
                    self._state._upsert_strategy_position(op.ticker, op.strategy_name, op.data)
                elif isinstance(op, CloseStrategyPosition):
                    self._state._close_strategy_position(op.ticker, op.strategy_name, op.data)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    async def _flush_loop(self) -> None:
        """Flush periódico."""
        while not self._closed:
            await asyncio.sleep(self._flush_interval)
            if not self._queue.empty():
                await self.flush()

    async def close(self) -> None:
        """Para flush loop e drena fila."""
        self._closed = True
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        # Flush final
        await self.flush()
