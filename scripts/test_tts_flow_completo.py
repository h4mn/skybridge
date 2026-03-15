#!/usr/bin/env python
# coding: utf-8
"""
Teste que simula o fluxo completo do chat: múltiplos eventos → fila TTS → fala tudo.
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "B:/_repositorios/skybridge/.claude/worktrees/prd027-sky-voice/src")


async def test_tts_flow_completo():
    """Testa o fluxo completo: múltiplos eventos → fila TTS → fala tudo."""
    from core.sky.chat.textual_ui.voice_commands import get_voice_handler

    handler = get_voice_handler()

    # Simula eventos que chegam do AgenticLoop + SkyBubble
    # THOUGHT, TOOL_START, TOOL_RESULT, TEXT
    eventos = [
        "Pensando: Vou criar uma função Python.\n",
        "Usando python...\n",
        "Resultado: A função foi criada com sucesso.\n",
        "Claro! Aqui está uma função completa em Python:\n",
        "```python\ndef calcular_soma(numero1, numero2):\n    \"\"\"Calcula a soma de dois números.\"\"\"\n    resultado = numero1 + numero2\n    print(f\"A soma de {numero1} e {numero2} é {resultado}\")\n    return resultado\n\ncalcular_soma(10, 5)\n```\n",
        "Esta função recebe dois parâmetros e retorna a soma.\n",
        "Explicação detalhada:\n",
        "1. A função é chamada com dois números\n",
        "2. Os números são somados\n",
        "3. O resultado é impresso\n",
        "4. O valor é retornado\n",
        "Espero que isso ajude a entender como funciona!\n",
    ]

    print("=" * 60)
    print("TESTE: Fluxo completo do chat (AgenticLoop + SkyBubble)")
    print("=" * 60)
    print(f"Total de eventos: {len(eventos)}")
    print()

    # Mostra cada evento
    for i, evento in enumerate(eventos):
        preview = evento[:50].replace('\n', '\\n')
        print(f"Evento #{i+1}: {len(evento)} chars - '{preview}...'")

    print()
    print("=" * 60)
    print("Enviando eventos para fila TTS...")
    print("=" * 60)

    # Cria fila TTS como no chat
    tts_queue = asyncio.Queue()

    # Envia todos os eventos para a fila (como o chat faz)
    for evento in eventos:
        await tts_queue.put(evento)

    # Sinaliza fim
    await tts_queue.put(None)

    print(f"Enviados {len(eventos)} eventos + 1 sinal de fim")
    print()

    # Processa fila como o _tts_worker() faz
    print("=" * 60)
    print("Processando fila TTS...")
    print("=" * 60)

    all_content = []
    event_count = 0

    while True:
        event = await tts_queue.get()

        if event is None:
            print(f"Fim. Total capturado: {event_count} eventos")
            break

        event_count += 1
        all_content.append(event)
        preview = event[:30].replace('\n', '\\n')
        print(f"  Evento #{event_count}: +{len(event)} chars = '{preview}...'")

    # Concatena tudo
    full_text = "".join(all_content)

    print()
    print("=" * 60)
    print(f"Texto completo: {len(full_text)} chars")
    print("=" * 60)
    print(full_text)
    print()
    print("=" * 60)
    print("Falando texto completo...")
    print("=" * 60)

    # Tenta falar
    try:
        import time
        start = time.perf_counter()

        await handler.handle_tts(full_text)

        elapsed = time.perf_counter() - start
        print(f"\n✓ SUCESSO! Falou {len(full_text)} chars em {elapsed:.2f}s")

    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_tts_flow_completo())
