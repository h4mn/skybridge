"""
Camada de Domínio - Paper Trading

Esta camada contém as entidades, value objects, eventos e serviços
que representam o núcleo do negócio de paper trading.

Componentes:
- entities: Entidades com identidade única (Portfolio, Ordem, Posicao)
- value_objects: Objetos imutáveis sem identidade (Preco, Ticker, Quantidade)
- events: Eventos de domínio (OrdemCriada, StopLossAcionado)
- services: Serviços de domínio com regras de negócio puras
"""

from . import entities
from . import value_objects
from . import events
from . import services
from . import strategies

__all__ = ["entities", "value_objects", "events", "services", "strategies"]
