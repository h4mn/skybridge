# -*- coding: utf-8 -*-
"""
Demo Engine — Sistema centralizado de demonstrações.

O Demo Engine fornece uma interface unificada para executar
demonstrações de todas as funcionalidades do Skybridge.

Uso:
    from runtime.demo.engine import get_demo_engine

    engine = get_demo_engine()
    await engine.run_demo("trello-flow")
"""

# Importar cenários para registrar automaticamente
from runtime.demo.scenarios import *  # noqa: F401, F403

from runtime.demo.engine import DemoEngine, get_demo_engine
from runtime.demo.registry import DemoRegistry, DemoCategory
from runtime.demo.base import BaseDemo, DemoContext, DemoResult

__all__ = [
    "DemoEngine",
    "get_demo_engine",
    "DemoRegistry",
    "DemoCategory",
    "BaseDemo",
    "DemoContext",
    "DemoResult",
]
