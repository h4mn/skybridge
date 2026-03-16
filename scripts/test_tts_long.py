#!/usr/bin/env python
# coding: utf-8
"""
Teste TTS com texto longo.
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "B:/_repositorios/skybridge/.claude/worktrees/prd027-sky-voice/src")


async def test_tts_longo():
    """Testa TTS com texto longo."""
    from core.sky.chat.textual_ui.voice_commands import get_voice_handler

    handler = get_voice_handler()

    # Texto longo simulando resposta real
    texto_longo = """Claro! Vou explicar detalhadamente como funciona.

Primeiro, precisamos entender que Python é uma linguagem poderosa.

Aqui está um exemplo completo:

```python
def processar_dados(lista):
    resultado = []
    for item in lista:
        resultado.append(item * 2)
    return resultado
```

Esta função processa cada item da lista.

Agora vou explicar cada parte:
1. A função recebe uma lista como parâmetro
2. Cria uma lista vazia para guardar resultados
3. Itera sobre cada item
4. Multiplica por 2 e adiciona ao resultado

Espero que isso ajude a entender!"""

    print("=" * 60)
    print("TESTE: TTS com texto longo e código")
    print("=" * 60)
    print(f"Texto: {len(texto_longo)} chars")
    print()

    # Divide em partes para testar
    partes = texto_longo.split('\n\n')
    print(f"Dividido em {len(partes)} partes")

    for i, parte in enumerate(partes):
        if parte.strip():
            print(f"\nParte {i+1}: {len(parte)} chars")
            try:
                await handler.handle_tts(parte.strip())
                print(f"  ✓ Falou")
            except Exception as e:
                print(f"  ✗ Erro: {e}")


if __name__ == "__main__":
    asyncio.run(test_tts_longo())
