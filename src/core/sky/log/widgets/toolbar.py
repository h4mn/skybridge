# coding: utf-8
"""
LogToolbar - Barra de ferramentas do log.

Layout de 2 linhas:
- Linha 1: Input de busca (largura total)
- Linha 2: Filtros de nível + botões copiar/fechar
"""

from textual.containers import Horizontal, Vertical

from core.sky.log.widgets.close import LogClose
from core.sky.log.widgets.copier import LogCopier
from core.sky.log.widgets.filter import LogFilter
from core.sky.log.widgets.search import LogSearch


class LogToolbar(Vertical):
    """Barra de ferramentas do sistema de log."""

    DEFAULT_CSS = """
    LogToolbar {
        height: 6;
        dock: top;
    }

    LogToolbar .buttons-row {
        height: 3;
        width: 1fr;
        layout: horizontal;
        padding: 0 0;
        margin: 0 0;
    }

    LogToolbar .buttons-row LogFilter {
        width: 1fr;
    }

    LogToolbar .buttons-row LogCopier {
        width: 5;
        min_width: 5;
    }

    LogToolbar .buttons-row LogClose {
        width: 5;
        min_width: 5;
    }
    """

    def compose(self):
        """Compora UI da toolbar."""
        # Linha 1: Busca
        yield LogSearch()

        # Linha 2: Filtros + botões
        with Horizontal(classes="buttons-row"):
            yield LogFilter()
            yield LogCopier()
            yield LogClose()


__all__ = ["LogToolbar"]
