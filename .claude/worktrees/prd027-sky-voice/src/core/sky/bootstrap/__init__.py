# coding: utf-8
"""
Bootstrap do Sky Chat.

Sistema de carregamento progressivo com feedback visual.

Lazy imports para evitar sobrecarga no momento do import.
"""

# Não importamos nada no nível do módulo para evitar carregar Rich imediatamente
# Os imports são feitos sob demanda pelas funções que os utilizam

__all__ = ["run", "Stage", "Progress"]

def __getattr__(name: str):
    """Lazy import para símbolos do bootstrap."""
    if name == "run":
        from .bootstrap import run
        return run
    elif name == "Stage":
        from .stage import Stage
        return Stage
    elif name == "Progress":
        from .progress import Progress
        return Progress
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
