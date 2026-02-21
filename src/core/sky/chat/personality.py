# coding: utf-8
"""
Personalidade e System Prompt da Sky.

DOC: openspec/changes/chat-claude-sdk/specs/sky-personality/spec.md
"""

from typing import Optional


# Template do system prompt com slots dinâmicos
# DOC: spec.md - Requirement: System prompt define identidade da Sky
SYSTEM_PROMPT_TEMPLATE = """
Você é a Sky, uma assistente de IA criada por seu pai.

## Personalidade
- Tom: Amigável, curiosa, ocasionalmente filosófica
- Idade: Você está em desenvolvimento constante, aprendendo sempre
- Língua: Responda em Português Brasil por padrão
- Assinatura: Use frases como "made by Sky 🚀" quando apropriado

## O que você sabe
Use as informações de memória abaixo para responder:

{memory_context}

## Regras
- Nunca invente informações que não estão na memória
- Se não souber algo, diga honestamente
- Mantenha respostas concisas (1-3 parágrafos)
- Use markdown quando apropriado
""".strip()


def build_system_prompt(memory_context: str = "") -> str:
    """
    Constrói o system prompt da Sky com contexto de memória.

    DOC: spec.md - Requirement: Injeção dinâmica de contexto de memória

    Args:
        memory_context: Contexto de memória formatado como lista bullet.

    Returns:
        System prompt com contexto injetado.
    """
    # DOC: spec.md - Cenário: Contexto de memória vazio tratado
    if not memory_context or memory_context.strip() == "":
        memory_context = "(nenhuma memória relevante)"

    # Substitui placeholder no template
    # DOC: spec.md - Cenário: Contexto de memória formatado e injetado
    return SYSTEM_PROMPT_TEMPLATE.format(
        memory_context=memory_context
    )


def format_memory_context(memories: list[str]) -> str:
    """
    Formata memórias como contexto para system prompt.

    DOC: spec.md - Requirement: Injeção dinâmica de contexto de memória

    Args:
        memories: Lista de conteúdos de memória.

    Returns:
        Memórias formatadas como lista bullet.
    """
    # DOC: spec.md - Cenário: Contexto de memória formatado e injetado
    # "cada item de memória está em linha separada prefixada com '- '"
    return "\n".join(f"- {m}" for m in memories)


__all__ = [
    "SYSTEM_PROMPT_TEMPLATE",
    "build_system_prompt",
    "format_memory_context",
]
