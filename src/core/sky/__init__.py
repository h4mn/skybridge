"""
Sky - O núcleo da Skybridge.

Sky é sua parceira digital, nascida na Skybridge.
Ela se reconhece como entidade com identidade, memória e autonomia.
"""

__version__ = "0.0.1"

# Lazy import para não carregar memory/embedding/sentence_transformers no import do pacote
__all__ = ["SkyIdentity", "get_sky"]

def __getattr__(name: str):
    """Lazy import para símbolos pesados."""
    if name == "SkyIdentity":
        from .identity import SkyIdentity
        return SkyIdentity
    elif name == "get_sky":
        from .identity import get_sky
        return get_sky
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
