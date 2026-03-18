#!/usr/bin/env python
# coding: utf-8
"""
Teste simples do STT com modelo base.
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "B:/_repositorios/skybridge/.claude/worktrees/prd027-sky-voice/src")


async def test_stt_base():
    """Testa STT com modelo base."""
    from core.sky.chat.textual_ui.voice_commands import execute_stt_command

    print("=" * 60)
    print("TESTE STT: Modelo Base")
    print("=" * 60)
    print()
    print("Fale algo agora! (5 segundos)")
    print()

    # Executa comando /stt
    result = await execute_stt_command(5.0)

    print()
    print("=" * 60)
    print("RESULTADO:")
    print("=" * 60)
    print(result)
    print()
    print("Observações:")
    print("  - Se a transcrição estiver incorreta, volte para 'medium'")
    print("  - Se estiver OK, 'base' é mais rápido e leve!")
    print()


if __name__ == "__main__":
    asyncio.run(test_stt_base())
