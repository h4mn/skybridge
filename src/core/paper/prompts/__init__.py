# -*- coding: utf-8 -*-
"""
Prompts - Paper Trading

Instruções modulares para uso do sistema de paper trading.

Módulos:
- paper_trading_guide: Guia geral de uso
- operations_reference: Referência de operações e APIs
- troubleshooting: Guia de resolução de problemas

Uso:
    Os arquivos .md podem ser usados como:
    - Contexto para LLMs (RAG)
    - Documentação inline
    - Prompts de sistema para agentes
"""
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

PROMPTS = {
    "guide": PROMPTS_DIR / "paper_trading_guide.md",
    "operations": PROMPTS_DIR / "operations_reference.md",
    "troubleshooting": PROMPTS_DIR / "troubleshooting.md",
}


def load_prompt(name: str) -> str:
    """Carrega conteúdo de um prompt pelo nome.

    Args:
        name: Nome do prompt ("guide", "operations", "troubleshooting")

    Returns:
        Conteúdo do arquivo markdown

    Raises:
        KeyError: Se nome não existir
        FileNotFoundError: Se arquivo não encontrado
    """
    if name not in PROMPTS:
        raise KeyError(f"Prompt '{name}' não encontrado. Disponíveis: {list(PROMPTS.keys())}")

    return PROMPTS[name].read_text(encoding="utf-8")


def load_all_prompts() -> dict[str, str]:
    """Carrega todos os prompts disponíveis.

    Returns:
        Dicionário nome -> conteúdo
    """
    return {name: load_prompt(name) for name in PROMPTS}


__all__ = ["PROMPTS", "PROMPTS_DIR", "load_prompt", "load_all_prompts"]
