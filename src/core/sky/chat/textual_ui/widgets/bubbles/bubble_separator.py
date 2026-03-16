# coding: utf-8
"""
TurnSeparator - Separador visual entre turnos consecutivos.

Linha pontilhada sutil que delimita onde termina um turno e começa o próximo.
"""

from textual.widgets import Static


class TurnSeparator(Static):
    """
    Separador visual entre turnos consecutivos.

    Linha pontilhada sutil que delimita onde
    termina um turno e começa o próximo.
    """

    DEFAULT_CSS = """
    TurnSeparator {
        height: 1;
        width: 100%;
        color: $text-muted;
        text-align: center;
        margin: 0 2;
        padding: 0;
    }
    """

    def __init__(self) -> None:
        # "╌" × 60 — visível mas não intrusivo
        super().__init__("╌" * 60)


__all__ = ["TurnSeparator"]
