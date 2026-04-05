"""StrategyWorker - avalia condições e sugere ações (stub)."""

import logging
from typing import Any, Callable, Optional

from .base import BaseWorker

logger = logging.getLogger(__name__)

# Tipo para callback de sugestão
SuggestionCallback = Callable[[str, str], None]  # (ticker, action)


class StrategyWorker(BaseWorker):
    """Worker que avalia estratégias e sugere ações.

    Responsabilidades:
    - Avalia condições de mercado
    - Aplica regras de estratégia
    - Sugere ações (comprar/vender/manter)

    Status: STUB - Interface definida, implementação pendente.

    Attributes:
        strategy_name: Nome da estratégia ativa.
        on_suggestion: Callback chamado quando há sugestão.
    """

    def __init__(
        self,
        strategy_name: str = "default",
        on_suggestion: Optional[SuggestionCallback] = None,
        **strategy_params: Any,
    ):
        """Inicializa o StrategyWorker.

        Args:
            strategy_name: Nome da estratégia.
            on_suggestion: Callback para sugestões.
            **strategy_params: Parâmetros específicos da estratégia.
        """
        super().__init__(name=f"strategy_{strategy_name}")
        self._strategy_name = strategy_name
        self._on_suggestion = on_suggestion
        self._params = strategy_params

    @property
    def strategy_name(self) -> str:
        """Nome da estratégia ativa."""
        return self._strategy_name

    async def start(self) -> None:
        """Inicializa o worker."""
        await super().start()
        self._logger.info(
            f"StrategyWorker '{self._strategy_name}' iniciado (STUB)"
        )

    async def _do_tick(self) -> None:
        """Avalia condições e gera sugestões.

        Stub: Apenas loga. Implementação futura:
        - Buscar dados de mercado
        - Aplicar regras da estratégia
        - Gerar sugestões via callback
        """
        self._logger.debug(
            f"StrategyWorker '{self._strategy_name}' tick (stub - sem ação)"
        )

        # Stub: Em produção, avaliaria condições reais
        # conditions = await self._evaluate_conditions()
        # if conditions:
        #     suggestion = self._apply_strategy(conditions)
        #     if suggestion and self._on_suggestion:
        #         self._on_suggestion(suggestion.ticker, suggestion.action)
