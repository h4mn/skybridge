# coding: utf-8
"""
ContextBar - Barra de progresso do contexto de mensagens.

Exibe barra de progresso indicando quanto da janela de
contexto (20 mensagens) foi usada, com cores dinâmicas.
"""

from textual.widgets import ProgressBar


class ContextBar(ProgressBar):
    """
    Barra de progresso do contexto de mensagens.

    Cores dinâmicas baseadas na porcentagem de uso:
    - 0-50%: Verde (contexto fresco)
    - 51-75%: Amarelo (contexto moderado)
    - 76-90%: Laranja (contexto quente)
    - 91-100%: Vermelho (contexto crítico)
    """

    DEFAULT_CSS = """
    ContextBar.--green {
        color: $success;
    }
    ContextBar.--green > .bar--bar {
        background: $success;
    }
    ContextBar.--yellow {
        color: $warning;
    }
    ContextBar.--yellow > .bar--bar {
        background: $warning;
    }
    ContextBar.--orange {
        color: orange;
    }
    ContextBar.--orange > .bar--bar {
        background: orange;
    }
    ContextBar.--red {
        color: red;
    }
    ContextBar.--red > .bar--bar {
        background: red;
    }
    """

    def __init__(self, total: int = 20, **kwargs) -> None:
        """
        Inicializa ContextBar.

        Args:
            total: Total de mensagens no contexto (padrão: 20).
            **kwargs: Argumentos adicionais para Widget (ex: id, name).
        """
        super().__init__(total=total, show_eta=False, **kwargs)
        self.total = total
        self.update_progress(0)

    def update_progress(self, used: int) -> None:
        """
        Atualiza o progresso e a cor baseado na porcentagem.

        Args:
            used: Quantidade de mensagens usadas.
        """
        self.progress = used
        percentage = (used / self.total) * 100 if self.total > 0 else 0

        # Remove classes de cor antigas
        self.remove_class("--green")
        self.remove_class("--yellow")
        self.remove_class("--orange")
        self.remove_class("--red")

        # Adiciona classe baseada na faixa de porcentagem
        if percentage <= 50:
            self.add_class("--green")
        elif percentage <= 75:
            self.add_class("--yellow")
        elif percentage <= 90:
            self.add_class("--orange")
        else:
            self.add_class("--red")


__all__ = ["ContextBar"]
