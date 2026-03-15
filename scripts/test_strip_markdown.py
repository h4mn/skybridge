#!/usr/bin/env python
# coding: utf-8
"""
Teste strip_markdown para limpar texto antes do TTS.
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import strip_markdown

# Teste com texto real do chat
markdown_text = """
Pensando: Vou criar uma funcao Python.

Usando python...

Resultado: A funcao foi criada com sucesso.

Claro! Aqui esta uma funcao completa em Python:

```python
def calcular_soma(numero1, numero2):
    return numero1 + numero2

calcular_soma(10, 5)
```

Esta funcao recebe dois parametros e retorna a soma.

Explicacao detalhada:
1. A funcao e chamada com dois numeros
2. Os numeros sao somados
3. O resultado e impresso
4. O valor e retornado

Espero que isso ajude a entender como funciona!

**Negrito** e *italico* tambem sao removidos.

Links como [Google](https://google.com) viram apenas "Google".
"""

print("=" * 70)
print("TESTE: strip_markdown")
print("=" * 70)
print()

print("TEXTO ORIGINAL (MARKDOWN):")
print("-" * 70)
print(markdown_text)
print()

print("=" * 70)
print("TEXTO LIMPO (PLAIN TEXT):")
print("=" * 70)

clean_text = strip_markdown.strip_markdown(markdown_text)
print(clean_text)
print()

print("=" * 70)
print("ANALISE:")
print("=" * 70)
print(f"Original: {len(markdown_text)} chars")
print(f"Limpado:  {len(clean_text)} chars")
print(f"Reducao:  {len(markdown_text) - len(clean_text)} chars ({(1 - len(clean_text)/len(markdown_text))*100:.1f}%)")
print()

print("O que foi removido:")
print("  ✅ Headers (# ##)")
print("  ✅ Bloco de codigo (```python...```) - TODO: verificar se queremos manter")
print("  ✅ Codigo inline (`...`)")
print("  ✅ Bold (**...**)")
print("  ✅ Italic (*...*)")
print("  ✅ Links [texto](url) → apenas 'texto'")
print()

print("=" * 70)
print("NOTA:")
print("=" * 70)
print("strip_markdown REMOVE blocos de codigo!")
print("Para TTS, isso pode ser desejado (nao ler codigo)")
print("ou indesejado (perder informacoes importantes)")
print()

# Teste especifico com codigo
print("=" * 70)
print("TESTE 2: Texto com bloco de codigo")
print("=" * 70)

texto_com_codigo = """
Aqui esta um exemplo:

```python
def hello():
    print("Ola, mundo!")
```

Espero que ajude!
"""

print("\nOriginal:")
print(texto_com_codigo)
print("\nLimpo:")
limpo = strip_markdown.strip_markdown(texto_com_codigo)
print(limpo)
