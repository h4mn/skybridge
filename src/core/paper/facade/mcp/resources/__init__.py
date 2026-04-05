# -*- coding: utf-8 -*-
"""
MCP Resources - Paper Trading

Recursos MCP (Model Context Protocol) para consulta de dados via LLM.

Resources disponíveis:
- PortfolioResource: Estado do portfolio
- PromptsResource: Instruções modulares (guide, operations, troubleshooting, all)
"""

from .portfolio_resource import PortfolioResource
from .prompts_resource import PromptsResource, create_prompt_resources

__all__ = ["PortfolioResource", "PromptsResource", "create_prompt_resources"]
