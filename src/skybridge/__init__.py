# -*- coding: utf-8 -*-
"""
Skybridge — Ponte entre intenção humana e execução assistida por IA.

Core package contendo:
- Kernel: SDK estável para apps e plugins
- Core: Bounded Contexts (FileOps, Tasks)
- Platform: Runtime e infraestrutura
- Infra: Implementações concretas
"""

__version__ = "0.1.0"
__kernel_api__ = "1.0.0"

# Fronteiras explícitas:
# - Apps dependem de Kernel + Application layer
# - Plugins dependem apenas do Kernel
# - Contexts não se importam entre si
# - Domain nunca importa Infra

__all__ = ["__version__", "__kernel_api__"]
