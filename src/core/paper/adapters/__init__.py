"""
Adapters (Adaptadores) - Paper Trading

Adapters implementam as interfaces (Ports) definidas pelo domínio.
Seguem o princípio de Dependency Inversion do DDD.

Categorias de Adapters:
- brokers/: Implementações de BrokerPort
- data_feeds/: Implementações de DataFeedPort
- persistence/: Implementações de RepositoryPort

Princípio:
- O domínio define a interface (port)
- Adapters implementam a interface
- A aplicação depende da interface, não da implementação
"""

from . import brokers
from . import data_feeds
from . import persistence

__all__ = ["brokers", "data_feeds", "persistence"]
