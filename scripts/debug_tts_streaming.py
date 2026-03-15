#!/usr/bin/env python
# coding: utf-8
"""
Debug TTS streaming - mostra o que está sendo enviado.
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "B:/_repositorios/skybridge/.claude/worktrees/prd027-sky-voice/src")


async def test_streaming_debug():
    """Testa streaming com logs detalhados."""
    from core.sky.chat.claude_chat import ClaudeChatAdapter, ChatMessage

    chat = ClaudeChatAdapter()
    message = ChatMessage(role='user', content='Escreva uma função Python que soma dois números e explique cada linha.')

    print("=" * 60)
    print("TESTE: Streaming com resposta contendo código")
    print("=" * 60)

    chunk_count = 0
    all_content = []

    async for event in chat.stream_response(message):
        chunk_count += 1
        print(f"\n[Chunk {chunk_count}] Type: {event.type.name}")
        print(f"Content: {event.content[:100]}...")

        if event.type.name == 'TEXT':
            all_content.append(event.content)
            print(f"  ✓ Texto acumulado: {len(''.join(all_content))} chars")

    full_text = ''.join(all_content)
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {chunk_count} chunks, {len(full_text)} caracteres")
    print(f"Texto completo:\n{full_text[:500]}...")
    print(f"\nContém ```? {'SIM' if '```' in full_text else 'NÃO'}")


if __name__ == "__main__":
    asyncio.run(test_streaming_debug())
