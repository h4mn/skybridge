#!/usr/bin/env python
# coding: utf-8
"""
Teste TTS com bloco de código.
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "B:/_repositorios/skybridge/.claude/worktrees/prd027-sky-voice/src")


async def test_tts_com_codigo():
    """Testa TTS com texto contendo bloco de código."""
    from core.sky.chat.textual_ui.voice_commands import get_voice_handler

    handler = get_voice_handler()

    # Simula resposta com bloco de código
    texto_com_codigo = """Aqui está uma função Python:

```python
def soma_numeros(a, b):
    return a + b
```

Esta função soma dois números e retorna o resultado.

Você pode usá-la assim:
numero = soma_numeros(5, 3)
print(numero)  # Saída: 8

Espero que isso ajude!"""

    print("=" * 60)
    print("TESTE: TTS com bloco de código")
    print("=" * 60)
    print(f"Texto completo: {len(texto_com_codigo)} chars")
    print()

    # Testa limpeza
    from core.sky.chat.textual_ui.screens.chat import ChatScreen

    # Cria instância dummy para acessar o método
    class DummyChatScreen:
        def _clean_text_for_speech(self, text: str) -> str:
            import re
            text = re.sub(r'`([^`]+)`', r'\1', text)
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            return text.strip()

    dummy = DummyChatScreen()
    texto_limpo = dummy._clean_text_for_speech(texto_com_codigo)

    print(f"Texto após limpeza: {len(texto_limpo)} chars")
    print(f"Contém ```? {'SIM' if '```' in texto_limpo else 'NÃO'}")
    print()

    # Mostra preview
    print(f"Preview limpo:\n{texto_limpo[:200]}...")
    print()

    # Testa TTS
    print("Falando texto...")
    try:
        await handler.handle_tts(texto_limpo)
        print("✓ TTS concluído")
    except Exception as e:
        print(f"✗ Erro: {e}")


if __name__ == "__main__":
    asyncio.run(test_tts_com_codigo())
