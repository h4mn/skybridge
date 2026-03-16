#!/usr/bin/env python
# coding: utf-8
"""
Teste TTS completo com debug detalhado.
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "B:/_repositorios/skybridge/.claude/worktrees/prd027-sky-voice/src")


async def test_tts_completo():
    """Testa TTS com resposta completa simulada."""
    from core.sky.chat.textual_ui.voice_commands import get_voice_handler

    handler = get_voice_handler()

    # Resposta completa simulando AgenticLoop + SkyBubble
    resposta_completa = """Pensando: Vou criar uma função Python.

Usando python...

Resultado: A função foi criada com sucesso.

Claro! Aqui está uma função completa em Python:

```python
def calcular_soma(numero1, numero2):
    \"\"Calcula a soma de dois números.\"\"\"
    resultado = numero1 + numero2
    print(f"A soma de {numero1} e {numero2} é {resultado}")
    return resultado

# Exemplo de uso
calcular_soma(10, 5)
```

Esta função recebe dois parâmetros e retorna a soma.

Explicação detalhada:
1. A função é chamada com dois números
2. Os números são somados
3. O resultado é impresso
4. O valor é retornado

Espero que isso ajude a entender como funciona!"""

    print("=" * 60)
    print("TESTE: TTS com resposta completa (AgenticLoop + SkyBubble)")
    print("=" * 60)
    print(f"Total: {len(resposta_completa)} chars")
    print()

    # Tenta falar
    print("Falando resposta completa...")
    try:
        import time
        start = time.perf_counter()

        await handler.handle_tts(resposta_completa)

        elapsed = time.perf_counter() - start
        print(f"\n✓ SUCESSO! Falou {len(resposta_completa)} chars em {elapsed:.2f}s")

    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_tts_completo())
