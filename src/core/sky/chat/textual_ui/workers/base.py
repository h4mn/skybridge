# coding: utf-8
"""
Worker base para workers assíncronos da UI Textual.

Fornece funcionalidade comum para todos os workers:
- Inicialização com adapter
- Execução assíncrona com yield para event loop
- Tratamento de erros padronizado
"""

import asyncio
from typing import Any, Callable


class BaseWorker:
    """
    Classe base para workers assíncronos.

    Fornece métodos comuns para todos os workers,
    evitando duplicação de código.
    """

    def __init__(self, adapter: Any) -> None:
        """
        Inicializa worker base.

        Args:
            adapter: Adaptador para operações (memory, etc.).
        """
        self.adapter = adapter

    async def _yield_to_event_loop(self) -> None:
        """
        Yield para o event loop para não bloquear a UI.

        Este método deve ser chamado em operações síncronas
        longas para permitir que a UI continue responsiva.
        """
        await asyncio.sleep(0)

    def _is_valid_result(self, result: Any) -> bool:
        """
        Verifica se um resultado é válido.

        Args:
            result: Resultado a validar.

        Returns:
            True se válido, False caso contrário.
        """
        return result is not None

    async def _execute_safe(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Executa função com tratamento de erro padrão.

        Args:
            func: Função a executar.
            *args: Argumentos posicionais.
            **kwargs: Argumentos nomeados.

        Returns:
            Resultado da função, ou None em caso de erro.
        """
        try:
            await self._yield_to_event_loop()
            return func(*args, **kwargs)
        except Exception:
            # Log seria adicionado aqui em produção
            return None


__all__ = ["BaseWorker"]
