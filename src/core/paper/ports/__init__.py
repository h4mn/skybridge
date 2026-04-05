"""
Ports (Portas) - Paper Trading

Ports definem as interfaces/contratos onde o domínio.
A infraestrutura externa. Seguem o princípio de Dependency inversion.

Portas disponíveis:
- broker_port: Interface para execução de ordens
- data_feed_port: Interface para feeds de dados de mercado
- repository_port: Interface para persistência de dados
- paper_state_port: Interface para gestão unificada do estado

Princípio:
- O domínio define a interface (port)
- Adapters implementam a interface (não da implementação)
"""

from .broker_port import BrokerPort
from .data_feed_port import DataFeedPort
from .repository_port import RepositoryPort, PortfolioRepositoryPort
from .paper_state_port import PaperStatePort, PaperStateData

__all__ = [
    "BrokerPort",
    "DataFeedPort",
    "RepositoryPort",
    "PortfolioRepositoryPort",
    "PaperStatePort",
    "PaperStateData",
]
