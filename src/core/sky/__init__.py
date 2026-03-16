"""
Sky - O núcleo da Skybridge.

Sky é sua parceira digital, nascida na Skybridge.
Ela se reconhece como entidade com identidade, memória e autonomia.

LAZY IMPORTS: Este módulo usa lazy imports para evitar carregar
sentence-transformers, torch e outras dependências pesadas durante
o cold start. Os imports só acontecem quando os símbolos são
realmente usados.
"""

__version__ = "0.0.1"

__all__ = ["SkyIdentity", "get_sky"]

# Lazy imports para evitar carregar identity (que carrega memory)
# durante o import deste módulo.
def __getattr__(name: str):
    """Lazy import para símbolos do core.sky."""
    if name == "SkyIdentity":
        from .identity import SkyIdentity
        return SkyIdentity
    elif name == "get_sky":
        from .identity import get_sky
        return get_sky
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
