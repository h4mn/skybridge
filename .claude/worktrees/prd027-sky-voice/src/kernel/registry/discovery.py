# -*- coding: utf-8 -*-
"""
Discovery — Importa pacotes/modulos para registrar handlers via decorators.
"""

from importlib import import_module
import pkgutil
from typing import Iterable


def discover_modules(packages: Iterable[str], include_submodules: bool = True) -> list[str]:
    """Importa pacotes/modulos de forma controlada e retorna o que foi carregado."""
    imported: list[str] = []
    for package in packages:
        if not package:
            continue
        module = import_module(package)
        imported.append(module.__name__)
        if not include_submodules:
            continue
        if hasattr(module, "__path__"):
            for _, name, _ in pkgutil.walk_packages(module.__path__, f"{module.__name__}."):
                import_module(name)
                imported.append(name)
    return imported
