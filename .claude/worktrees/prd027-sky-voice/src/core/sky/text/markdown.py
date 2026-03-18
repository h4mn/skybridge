"""
Limpeza de Markdown para TTS e outros usos.

Baseado em strip_markdown (75 linhas), internalizado para:
- Controle total sobre parâmetros
- Evitar dependência externa
- Manutenção local
"""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class MarkdownCleanupConfig:
    """Configuração para limpeza de markdown.

    Attributes:
        remove_code_blocks: Remove blocos de código (```...```)
        remove_code_inline: Remove código inline (`...`)
        remove_bold: Remove bold (**...**)
        remove_italic: Remove italic (*...*)
        remove_headers: Remove headers (# ## ###)
        remove_links: Remove links mas mantém texto
        remove_strikethrough: Remove strikethrough (~~...~~)
        keep_code_content: Se True, remove blocos mas mantém conteúdo do código
    """
    remove_code_blocks: bool = True
    remove_code_inline: bool = True
    remove_bold: bool = True
    remove_italic: bool = True
    remove_headers: bool = True
    remove_links: bool = True
    remove_strikethrough: bool = True
    keep_code_content: bool = False


def strip_markdown(
    text: str,
    config: Optional[MarkdownCleanupConfig] = None
) -> str:
    """Remove formatação markdown do texto.

    Args:
        text: Texto com formatação markdown
        config: Configuração de limpeza (padrão: remove tudo)

    Returns:
        Texto sem formatação markdown

    Examples:
        >>> strip_markdown("**Bold** e *italic*")
        'Bold e italic'

        >>> strip_markdown("```python\\ncódigo```")
        'código'  # se keep_code_content=True
        ''       # se keep_code_content=False
    """
    if config is None:
        config = MarkdownCleanupConfig()

    # Ordem importa! Processa do mais específico para o menos específico

    # 1. Blocos de código (```...```)
    if config.remove_code_blocks:
        if config.keep_code_content:
            # Remove ``` mas mantém conteúdo
            text = re.sub(r'```[\w]*\n', '', text)  # Remove ```
            text = re.sub(r'```', '', text)  # Remove ``` de fechamento
        else:
            # Remove bloco inteiro incluindo conteúdo
            text = re.sub(r'```[\w]*\n.*?```', '', text, flags=re.DOTALL)

    # 2. Cabeçalhos
    if config.remove_headers:
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

    # 3. Bold e italic (antes de código inline para evitar conflitos)
    if config.remove_bold:
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__

    if config.remove_italic:
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
        text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_

    # 4. Código inline
    if config.remove_code_inline:
        text = re.sub(r'`([^`]+)`', r'\1', text)

    # 5. Links
    if config.remove_links:
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # 6. Strikethrough
    if config.remove_strikethrough:
        text = re.sub(r'~~([^~]+)~~', r'\1', text)

    # 7. Imagens
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)

    # 8. Listas (remove marcadores mas mantém texto)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # 9. Blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

    # 10. Horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # 11. Limpa linhas vazias extras
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def strip_for_tts(text: str, remove_code_blocks: bool = True) -> str:
    """Remove formatação markdown especificamente para TTS.

    Esta é uma função de conveniência com configuração otimizada
    para conversão de texto para fala.

    Args:
        text: Texto com formatação markdown
        remove_code_blocks: Se True, remove blocos de código completamente

    Returns:
        Texto limpo para TTS

    Examples:
        >>> strip_for_tts("**Negrito** e código: \\`x\\`")
        'Negrito e código: x'

        >>> strip_for_tts("```python\\nprint(1)\\n```")
        ''  # remove bloco inteiro
    """
    config = MarkdownCleanupConfig(
        remove_code_blocks=remove_code_blocks,
        remove_code_inline=True,
        remove_bold=True,
        remove_italic=True,
        remove_headers=True,
        remove_links=True,
        remove_strikethrough=True,
        keep_code_content=False,  # Remove bloco inteiro
    )
    return strip_markdown(text, config)


def detect_code_block_heuristic(text: str) -> list[tuple[int, int]]:
    """Detecta blocos de código usando heurística.

    Útil para identificar seções que podem ser removidas do TTS.

    Args:
        text: Texto para analisar

    Returns:
        Lista de tuplas (linha_inicio, linha_fim) para cada bloco detectado

    Examples:
        >>> detect_code_block_heuristic("Texto\\npython\\ndef x():")
        [(1, 2)]
    """
    lines = text.split('\n')
    blocks = []
    in_block = False
    start_line = 0

    code_indicators = [
        'python', 'javascript', 'bash', 'java', 'cpp', 'c',
        'def ', 'class ', 'function ', 'const ', 'let ', 'var ',
        'import ', 'from ', 'package ', '#!/bin/', '#include',
    ]

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detecta início de bloco
        if not in_block and any(stripped.startswith(ind) for ind in code_indicators):
            in_block = True
            start_line = i
            continue

        # Detecta fim de bloco (volta a texto normal)
        if in_block:
            # Termina se encontrar linha de texto que não parece código
            if stripped and not any(
                stripped.startswith(ind) or
                stripped in ['...', '"""', "'''"] or
                re.match(r'^[\s\]\[\)\}\{]*$', stripped)
                for ind in code_indicators
            ):
                in_block = False
                blocks.append((start_line, i - 1))

    # Se ainda está em bloco no final
    if in_block:
        blocks.append((start_line, len(lines) - 1))

    return blocks


def remove_code_blocks(text: str) -> str:
    """Remove blocos de código detectados por heurística.

    Args:
        text: Texto com possíveis blocos de código

    Returns:
        Texto sem os blocos de código
    """
    blocks = detect_code_block_heuristic(text)
    if not blocks:
        return text

    lines = text.split('\n')

    # Remove linhas dos blocos (em ordem reversa para não mudar índices)
    for start, end in reversed(blocks):
        del lines[start:end + 1]

    return '\n'.join(lines).strip()
