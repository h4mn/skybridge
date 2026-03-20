# coding: utf-8
"""
ChatLog - Widget de log com scroll e cópia.

===============================================================================
DEPRECATED - Este módulo está obsoleto e será removido em versões futuras.

Use o novo subsistema de log em core.sky.log:
    - from core.sky.log import ChatLog, ChatLogConfig (NOVO)
    - from core.sky.log import LogFilter, LogSearch, LogCopier, LogToolbar

O novo ChatLog 2.0 oferece:
    - Ring buffer com limite configurável
    - Virtualização para performance
    - Filtro por nível e escopo
    - Busca reativa com highlight
    - Cópia para clipboard respeitando filtros
    - LogConsumer Protocol para desacoplamento

Este arquivo legado é mantido apenas para compatibilidade durante migração.
===============================================================================

Usa VerticalScroll + Static para wrap de palavra nativo e seleção de texto.
Flicker corrigido via fila de linhas pendentes — flush em batch no próximo tick de UI.

CORREÇÕES:
- dock: bottom + layer: overlay (Textual não suporta position: absolute)
- Cores mais visíveis (cyan, bold red, green, yellow)
- Toggle via display: none/block (Ctrl+L)

NOTA: Devido à limitação do Textual, o ChatLog ainda empurra widgets quando abre.
O dock: bottom é a melhor solução nativa do framework.
"""

from textual.containers import VerticalScroll
from textual.widgets import Static


class ChatLog(VerticalScroll):
    """
    Widget de log com scroll, wrap de palavra e cópia de texto.

    Usa dock: bottom + layer: overlay com toggle via display:none/block.
    NOTA: Textual não suporta position: absolute, então o widget ainda
    empurra outros widgets quando abre (limitação do framework).
    """

    DEFAULT_CSS = """
    ChatLog {
        height: 20;
        width: 100%;
        dock: bottom;
        display: none;
        background: $panel;
        border-top: thick $primary;
        layer: overlay;
    }

    ChatLog.visible {
        display: block;
    }

    ChatLog Static {
        width: 100%;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._visible: bool = False
        self._pending: list[str] = []
        self._flush_scheduled: bool = False
        # Buffer de linhas quando fechado (últimas 100 linhas)
        self._buffer: list[str] = []
        self._max_buffer_size: int = 100

    def write(self, line: str) -> None:
        """Enfileira linha para montagem no próximo tick de UI."""
        # Se visível, enfileira para flush imediato
        if self._visible:
            self._pending.append(line)
            if not self._flush_scheduled:
                self._flush_scheduled = True
                # Agenda flush para depois que o frame atual terminar
                self.call_after_refresh(self._flush)
        else:
            # Se fechado, mantém no buffer (últimas N linhas)
            self._buffer.append(line)
            if len(self._buffer) > self._max_buffer_size:
                self._buffer.pop(0)  # Remove linha mais antiga

    def _flush(self) -> None:
        """Monta todas as linhas pendentes em uma única operação."""
        if not self._pending:
            self._flush_scheduled = False
            return
        lines = self._pending[:]
        self._pending.clear()
        self._flush_scheduled = False
        # Um único mount com múltiplos widgets = um único reflow
        self.mount(*[Static(line, markup=True) for line in lines])
        self.call_after_refresh(self.scroll_end)

    def debug(self, message: str) -> None:
        """Mensagem de debug (amarelo)."""
        self.write(rf"[yellow]\[DEBUG][/] {message}")

    def info(self, message: str) -> None:
        """Mensagem de info (cyan - mais visível)."""
        self.write(rf"[cyan]\[INFO][/] {message}")

    def error(self, message: str) -> None:
        """Mensagem de erro (vermelho bold)."""
        self.write(rf"[bold red]\[ERROR][/] {message}")

    def evento(self, nome: str, dados: str = "") -> None:
        """Mensagem de evento (verde)."""
        self.write(rf"[green]\[EVENTO][/] {nome} {dados}")

    def toggle_class(self, class_name: str) -> None:
        """Toggle de classe CSS."""
        if class_name == "visible":
            self._visible = not self._visible
            if self._visible:
                self.add_class("visible")
                # Ao abrir, mostra linhas acumuladas no buffer
                if self._buffer:
                    self._pending.extend(self._buffer[:])
                    self._buffer.clear()
                    if not self._flush_scheduled:
                        self._flush_scheduled = True
                        self.call_after_refresh(self._flush)
            else:
                self.remove_class("visible")


__all__ = ["ChatLog"]
