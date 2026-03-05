# coding: utf-8
"""
MemorySaveWorker - Worker assíncrono para salvar memórias.

Salva novas memórias aprendidas durante conversa
em background sem bloquear a UI Textual.
"""

from core.sky.chat.textual_ui.workers.base import BaseWorker


class MemorySaveWorker(BaseWorker):
    """
    Worker assíncrono para salvar memórias.

    Executa salvamento de memórias aprendidas em background,
    permitindo que a UI continue responsiva.
    """

    def __init__(self, memory_adapter):
        """
        Inicializa MemorySaveWorker.

        Args:
            memory_adapter: Adaptador de memória (PersistentMemory).
        """
        super().__init__(memory_adapter)
        self.memory_adapter = memory_adapter

    async def save(self, content: str) -> bool:
        """
        Salva nova memória.

        Args:
            content: Conteúdo a salvar.

        Returns:
            True se salvou com sucesso, False caso contrário.
        """
        # Yield para event loop (não bloquear UI)
        await self._yield_to_event_loop()

        try:
            self.memory_adapter.learn(content)
            return True
        except Exception:
            return False


__all__ = ["MemorySaveWorker"]
