# -*- coding: utf-8 -*-
'''
Skybridge Kernel — SDK estável para apps e plugins.

Este módulo fornece:
- Result type para retornos tipados
- Envelope para respostas de API
- Registry para handlers CQRS
'''

from .contracts.result import Result, Status
from .envelope.envelope import Envelope
from .registry.query_registry import QueryRegistry, QueryHandler, get_query_registry

__all__ = [
    'Result',
    'Status',
    'Envelope',
    'QueryRegistry',
    'QueryHandler',
    'get_query_registry',
]
