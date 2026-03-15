#!/usr/bin/env python
# coding: utf-8
"""
Teste de integração do comando /tts on|off.

Verifica se o comando é processado corretamente sem erros.
"""

import asyncio
import sys
import io

# Configura stdout para UTF-8 (Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "src")


async def test_worker_integration():
    """Testa integração do worker TTS toggle."""
    print("=" * 60)
    print("TESTE: Worker TTS Toggle Integration")
    print("=" * 60)

    # Importa após configurar path
    from core.sky.chat.textual_ui.commands import Command, CommandType
    from core.sky.chat.textual_ui.voice_commands import execute_tts_toggle_command

    # Testa parse
    cmd = Command.parse('/tts on')
    print(f"Parse /tts on: {cmd.type.value}")
    assert cmd.type == CommandType.TTS_TOGGLE

    # Testa execução async
    result = await execute_tts_toggle_command('on')
    print(f"Resultado: {result[:50]}...")

    print("\n[OK] Integração funcionando!")


if __name__ == "__main__":
    asyncio.run(test_worker_integration())
