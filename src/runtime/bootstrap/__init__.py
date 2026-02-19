# -*- coding: utf-8 -*-
"""
Bootstrap — Inicialização da aplicação.

Módulos:
- BaseApp: Template Method Pattern para execução de servidor
- SkybridgeApp: Aplicação FastAPI principal
"""

from .base_app import BaseApp
from .app import SkybridgeApp

__all__ = ["BaseApp", "SkybridgeApp"]
