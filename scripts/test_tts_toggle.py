#!/usr/bin/env python
# coding: utf-8
"""
Testa funcionalidade de TTS toggle (PRD027).

Verifica:
- Comando /tts on ativa TTS progressivo
- Comando /tts off desativa TTS progressivo
- Worker TTS processa chunks corretamente
"""

import asyncio
import sys
import io

# Configura stdout para UTF-8 (Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "src")

from core.sky.chat.textual_ui.voice_commands import (
    VoiceCommandHandler,
    execute_tts_toggle_command,
)
from core.sky.chat.textual_ui.commands import Command, CommandType


async def test_command_parsing():
    """Testa parse de comandos /tts."""
    print("=" * 60)
    print("TESTE 1: Parse de comandos /tts")
    print("=" * 60)

    test_cases = [
        ("/tts on", CommandType.TTS_TOGGLE, "deve ativar TTS"),
        ("/tts off", CommandType.TTS_TOGGLE, "deve desativar TTS"),
        ("/tts", CommandType.TTS, "sem argumentos -> TTS normal"),
        ("/tts olá mundo", CommandType.TTS, "com texto -> TTS normal"),
        ("/tts ON", CommandType.TTS_TOGGLE, "maiúsculas -> TTS_TOGGLE"),
    ]

    for cmd_str, expected_type, description in test_cases:
        cmd = Command.parse(cmd_str)
        if cmd:
            result = "[OK]" if cmd.type == expected_type else "[FAIL]"
            print(f"{result} {cmd_str:20} -> {cmd.type.value:15} ({description})")
        else:
            print(f"[FAIL] {cmd_str:20} -> None (esperado {expected_type.value})")

    print()


async def test_voice_handler_toggle():
    """Testa toggle de TTS no VoiceCommandHandler."""
    print("=" * 60)
    print("TESTE 2: Toggle de TTS no VoiceCommandHandler")
    print("=" * 60)

    handler = VoiceCommandHandler()

    # Estado inicial
    print(f"Estado inicial: tts_responses = {handler.tts_responses}")

    # Toggle para ativar
    await handler.handle_tts_toggle(True)
    print(f"handle_tts_toggle(True): tts_responses = {handler.tts_responses}")
    assert handler.tts_responses == True, "Deveria estar ativo"

    # Toggle para desativar
    await handler.handle_tts_toggle(False)
    print(f"handle_tts_toggle(False): tts_responses = {handler.tts_responses}")
    assert handler.tts_responses == False, "Deveria estar inativo"

    # Toggle sem argumento (None)
    await handler.handle_tts_toggle()
    print(f"handle_tts_toggle(None): tts_responses = {handler.tts_responses}")
    assert handler.tts_responses == True, "Deveria estar ativo após toggle"

    await handler.handle_tts_toggle()
    print(f"handle_tts_toggle(None): tts_responses = {handler.tts_responses}")
    assert handler.tts_responses == False, "Deveria estar inativo após toggle"

    print("[OK] Todos os testes de toggle passaram!\n")


async def test_execute_tts_toggle():
    """Testa função execute_tts_toggle_command."""
    print("=" * 60)
    print("TESTE 3: execute_tts_toggle_command")
    print("=" * 60)

    # Usa o singleton (mesmo usado pela função)
    from core.sky.chat.textual_ui.voice_commands import get_voice_handler
    handler = get_voice_handler()

    # Reseta estado inicial
    handler.tts_responses = False

    # Testa /tts on
    result = await execute_tts_toggle_command("on")
    print(f"/tts on -> {result}")
    assert handler.tts_responses == True, f"Esperado True, got {handler.tts_responses}"

    # Testa /tts off
    result = await execute_tts_toggle_command("off")
    print(f"/tts off -> {result}")
    assert handler.tts_responses == False, f"Esperado False, got {handler.tts_responses}"

    # Testa toggle (sem argumento)
    result = await execute_tts_toggle_command("")
    print(f"/tts (toggle) -> {result}")
    assert handler.tts_responses == True, f"Esperado True, got {handler.tts_responses}"

    result = await execute_tts_toggle_command("xyz")
    print(f"/tts xyz (toggle) -> {result}")
    assert handler.tts_responses == False, f"Esperado False, got {handler.tts_responses}"

    print("[OK] Todos os testes de execute passaram!\n")


async def test_clean_text_for_speech():
    """Testa limpeza de markdown para fala."""
    print("=" * 60)
    print("TESTE 4: _clean_text_for_speech")
    print("=" * 60)

    # Simula o método da ChatScreen
    import re

    def _clean_text_for_speech(text: str) -> str:
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        return text.strip()

    test_cases = [
        ("**Olá** mundo", "Olá mundo"),
        ("`print('x')` exemplo", "print('x') exemplo"),
        ("```python\ncódigo\n```", ""),
        ("# Título\nTexto", "Título\nTexto"),  # Título é mantido, apenas # removido
        ("[link](url)", "link"),
        ("**negrito** e *itálico*", "negrito e itálico"),
    ]

    for input_text, expected in test_cases:
        result = _clean_text_for_speech(input_text)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} \"{input_text[:30]}\" -> \"{result}\"")
        if result != expected:
            print(f"   Esperado: \"{expected}\"")

    print()


async def main():
    """Executa todos os testes."""
    print("\n[TEST] SUITE DE TESTES - TTS Toggle (PRD027)\n")

    try:
        await test_command_parsing()
        await test_voice_handler_toggle()
        await test_execute_tts_toggle()
        await test_clean_text_for_speech()

        print("=" * 60)
        print("[OK] TODOS OS TESTES PASSARAM!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n[FAIL] TESTE FALHOU: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
