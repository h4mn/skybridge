#!/usr/bin/env python
# coding: utf-8
"""
Teste do módulo core.sky.text para limpeza de markdown.
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "B:/_repositorios/skybridge/.claude/worktrees/prd027-sky-voice/src")

from core.sky.text import strip_for_tts, strip_markdown, MarkdownCleanupConfig
from core.sky.text.markdown import detect_code_block_heuristic, remove_code_blocks

# Teste 1: strip_for_tts (padrão para TTS)
print("=" * 70)
print("TESTE 1: strip_for_tts (padrão TTS)")
print("=" * 70)

texto_chat = """
Pensando: Vou criar uma função Python.

Usando python...

**Resultado**: A função foi criada com sucesso!

Claro! Aqui está uma função:

```python
def calcular_soma(numero1, numero2):
    return numero1 + numero2
```

Esta é *simples* e `eficiente`.

Espero que ajude!
"""

print("\nENTRADA:")
print(texto_chat)
print("\nSAÍDA:")
limpo = strip_for_tts(texto_chat)
print(limpo)
print()

# Teste 2: Com configuração customizada (mantém código)
print("=" * 70)
print("TESTE 2: strip_markdown com config customizada")
print("=" * 70)

config = MarkdownCleanupConfig(
    remove_code_blocks=False,  # MANTÉM blocos
    keep_code_content=True,    # Mantém conteúdo
    remove_bold=False,         # MANTÉM bold
)

texto2 = "**Título** e código:\n```python\nx = 1\n```"
print(f"\nENTRADA: {texto2}")

limpo2 = strip_markdown(texto2, config)
print(f"SAÍDA: {limpo2}")
print()

# Teste 3: Detectar blocos de código
print("=" * 70)
print("TESTE 3: detect_code_block_heuristic")
print("=" * 70)

texto3 = """
Introdução ao Python

python
def hello():
    print("Oi")

Espero que ajude!
"""

print(f"\nTEXTO:\n{texto3}")

blocos = detect_code_block_heuristic(texto3)
print(f"\nBLOCOS DETECTADOS: {blocos}")

from core.sky.text.markdown import remove_code_blocks
sem_codigo = remove_code_blocks(texto3)
print(f"\nSEM CÓDIGO:\n{sem_codigo}")
print()

# Teste 4: Comparação strip_markdown vs strip_for_tts
print("=" * 70)
print("TESTE 4: Comparação")
print("=" * 70)

texto4 = """
# Título

**Texto** em *negrito* e `código`.

[Link](https://exemplo.com)
"""

print(f"\nENTRADA:\n{texto4}")

print("\n--- strip_for_tts (tudo removido) ---")
print(strip_for_tts(texto4))

print("\n--- strip_markdown (custom: mantém bold) ---")
config_custom = MarkdownCleanupConfig(
    remove_bold=False,
    remove_italic=False,
)
print(strip_markdown(texto4, config_custom))

print()
print("=" * 70)
print("✓ Todos os testes concluídos!")
print("=" * 70)
