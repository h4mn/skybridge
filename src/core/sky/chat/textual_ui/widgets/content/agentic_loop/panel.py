# coding: utf-8
"""
AgenticLoopPanel - Painel colapsável que agrupa Steps do loop agentic ReAct.

Comportamento:
- Inicia com ThinkingIndicator visível ("🤔 pensando...")
- Quando primeiro Step é adicionado, remove ThinkingIndicator e mostra Steps
- Expandido durante o processamento
- Auto-colapsa quando a resposta final chega
- Título dinâmico: "⟳ N steps • Xs"

Estados:
1. INIT: ThinkingIndicator visível, nenhum Step ainda
2. ACTIVE: Pelo menos um Step adicionado, ThinkingIndicator removido
3. FROZEN: Cancelado pelo usuário, não adiciona mais Steps
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Collapsible

if TYPE_CHECKING:
    from core.sky.chat.textual_ui.widgets.content.thinking import ThinkingIndicator


class AgenticLoopPanel(Collapsible):
    """
    Painel colapsável que agrupa Steps do loop agentic ReAct.

    Comportamento:
    - Inicia com ThinkingIndicator visível ("🤔 pensando...")
    - Quando primeiro Step é adicionado, remove ThinkingIndicator e mostra Steps
    - Expandido durante o processamento
    - Auto-colapsa quando a resposta final chega
    - Título dinâmico: "⟳ N steps • Xs"

    Estados:
    1. INIT: ThinkingIndicator visível, nenhum Step ainda
    2. ACTIVE: Pelo menos um Step adicionado, ThinkingIndicator removido
    3. FROZEN: Cancelado pelo usuário, não adiciona mais Steps
    """

    DEFAULT_CSS = """
    AgenticLoopPanel {
        margin: 0;
        padding: 1 0 0 0;
        border: none;
        background: $surface;
        height: auto;
    }

    AgenticLoopPanel.collapsed {
        border: none;
    }

    AgenticLoopPanel > CollapsibleTitle {
        text-style: bold;
        color: $primary;
        padding: 0 1;
        background: transparent;
    }

    AgenticLoopPanel.collapsed > CollapsibleTitle {
        color: $text-muted;
        text-style: none;
        background: transparent;
    }

    AgenticLoopPanel #steps-container {
        height: auto;
        overflow-y: auto;
        padding: 0;
    }

    AgenticLoopPanel ThinkingIndicator {
        margin: 0 1 1 1;
    }
    """

    def __init__(self, parent_turn=None) -> None:
        """
        Inicializa o AgenticLoopPanel.

        Args:
            parent_turn: Referência ao Turn pai para disparar scroll.
        """
        super().__init__(title="⟳ 0 steps • 0s", collapsed=False)
        self._steps: list[StepWidget] = []
        self._step_count = 0
        self._start_time: float | None = None
        self._frozen = False  # True quando cancelado (não adiciona mais Steps)
        self._indicator: ThinkingIndicator | None = None  # ThinkingIndicator interno
        self._parent_turn = parent_turn  # Referência para disparar scroll

    def compose(self) -> ComposeResult:
        from core.sky.chat.textual_ui.widgets.content.thinking import ThinkingIndicator

        # ThinkingIndicator visível inicialmente
        self._indicator = ThinkingIndicator()
        yield self._indicator
        yield Container(id="steps-container")

    def _trigger_scroll(self) -> None:
        """Dispara scroll no ChatScroll via Turn pai."""
        if self._parent_turn is not None:
            try:
                self._parent_turn.trigger_scroll()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    async def add_step(self, thought: str | None = None) -> StepWidget:
        """
        Adiciona um StepWidget ao painel.

        No primeiro Step adicionado, remove o ThinkingIndicator.

        Args:
            thought: Texto de pensamento opcional (ThoughtLine).

        Returns:
            O StepWidget criado para referência futura.
        """
        from core.sky.chat.textual_ui.widgets.content.agentic_loop.step import StepWidget

        if self._frozen:
            # Não adiciona mais Steps se foi cancelado
            return None  # type: ignore

        # Primeiro Step: remove ThinkingIndicator
        if self._step_count == 0 and self._indicator is not None:
            try:
                self._indicator.remove()
                self._indicator = None
            except Exception:
                pass

        # Inicia o timer no primeiro Step
        if self._start_time is None:
            self._start_time = time.time()

        step = StepWidget(thought=thought)
        self._steps.append(step)
        self._step_count += 1
        self._update_title()

        try:
            container = self.query_one("#steps-container", Container)
            await container.mount(step)
            container.scroll_end()
            # Dispara scroll no ChatScroll principal
            self._trigger_scroll()
        except Exception:
            pass

        return step

    def get_last_pending_step(self) -> StepWidget | None:
        """
        Retorna o último StepWidget pendente (não resolvido).

        Usado para resolver o Step quando tool_result chega.
        """
        from core.sky.chat.textual_ui.widgets.content.agentic_loop.step import StepWidget

        for step in reversed(self._steps):
            if not step.is_resolved:
                return step
        return None

    def collapse_done(self) -> None:
        """
        Colapsa o painel quando a resposta final chega.

        Atualiza o título com a duração total.
        """
        self._update_title()
        self.collapsed = True

    def freeze(self) -> None:
        """
        Congela o painel quando o turno é cancelado.

        Mantém Steps já criados visíveis, não adiciona mais.
        """
        self._frozen = True
        self._update_title()

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _update_title(self) -> None:
        """Atualiza o título com contador de Steps e duração."""
        n = self._step_count
        duration = self._get_duration()
        try:
            if self._frozen:
                self.title = f"⟳ {n} steps • {duration}s (interrompido)"
            else:
                self.title = f"⟳ {n} steps • {duration}s"
        except Exception:
            pass

    def _get_duration(self) -> float:
        """Retorna a duração em segundos."""
        if self._start_time is None:
            return 0.0
        return round(time.time() - self._start_time, 1)

    @property
    def step_count(self) -> int:
        return self._step_count

    @property
    def is_frozen(self) -> bool:
        return self._frozen


__all__ = ["AgenticLoopPanel"]
