"""Value Object Ticker - Representa um ativo negociado."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Ticker:
    """Ticker de um ativo.
    
    Value Object imutável que representa o símbolo de um ativo.
    """
    simbolo: str
    
    def __post_init__(self):
        # Normaliza para maiúsculas
        object.__setattr__(self, 'simbolo', self.simbolo.upper().strip())
    
    def __str__(self) -> str:
        return self.simbolo
