#!/usr/bin/env python
# coding: utf-8
"""
Benchmark STT: compara qualidade vs desempenho dos modelos base e medium.
"""

import asyncio
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "B:/_repositorios/skybridge/.claude/worktrees/prd027-sky-voice/src")


async def benchmark_stt():
    """Compara modelos base e medium."""
    from core.sky.voice.stt_service import WhisperAdapter
    from core.sky.voice.audio_capture import SoundDeviceCapture

    # Texto esperado (frase de teste)
    TEXTO_ESPERADO = "Sky, teste de transcrição com números um dois três."

    print("=" * 70)
    print("BENCHMARK STT: Base vs Medium (qualidade vs desempenho)")
    print("=" * 70)
    print(f"Texto esperado: \"{TEXTO_ESPERADO}\"")
    print(f"Duração gravação: 5 segundos")
    print()

    resultados = []

    for model_size in ["base", "medium"]:
        print("-" * 70)
        print(f"TESTANDO MODELO: {model_size.upper()}")
        print("-" * 70)

        # Cria adapter com modelo específico
        stt = WhisperAdapter(model_size=model_size, device="cpu")

        # Captura áudio
        print(f"\n[{model_size.upper()}] Gravando 5 segundos... Fale agora!")
        print(f"[{model_size.upper()}] Texto: \"{TEXTO_ESPERADO}\"")

        captura = SoundDeviceCapture()
        await captura.start_recording()
        import time
        time.sleep(5)  # Grava por 5 segundos
        audio_data = await captura.stop_recording()

        print(f"[{model_size.upper()}] Áudio capturado: {audio_data.duration:.2f}s")

        # Transcreve e mede tempo
        print(f"[{model_size.upper()}] Transcrevendo...")

        start = time.perf_counter()
        resultado = await stt.transcribe(audio_data, language="pt")
        elapsed = time.perf_counter() - start

        # Calcula métricas
        transcricao = resultado.text or ""
        confianca = resultado.confidence or 0.0

        # Compara com texto esperado
        # Usa SequenceMatcher para similaridade
        from difflib import SequenceMatcher
        similaridade = SequenceMatcher(None, TEXTO_ESPERADO.lower(), transcricao.lower()).ratio()

        # RTF (Real-Time Factor) = tempo_transcricao / duracao_audio
        rtf = elapsed / audio_data.duration if audio_data.duration > 0 else 0

        print(f"\n[{model_size.upper()}] RESULTADOS:")
        print(f"  Transcrição: \"{transcricao}\"")
        print(f"  Confiança: {confianca:.1%}")
        print(f"  Tempo transcrição: {elapsed:.2f}s")
        print(f"  RTF (Real-Time Factor): {rtf:.2f}x")
        print(f"  Similaridade com esperado: {similaridade:.1%}")

        # Armazena resultado
        resultados.append({
            "modelo": model_size,
            "transcricao": transcricao,
            "confianca": confianca,
            "tempo": elapsed,
            "rtf": rtf,
            "similaridade": similaridade,
        })

        print()

    # Relatório comparativo
    print("=" * 70)
    print("RELATÓRIO COMPARATIVO")
    print("=" * 70)
    print()

    for r in resultados:
        m = r["modelo"].upper()
        print(f"{m}:")
        print(f"  Transcrição: \"{r['transcricao']}\"")
        print(f"  Confiança: {r['confianca']:.1%}")
        print(f"  Tempo: {r['tempo']:.2f}s")
        print(f"  RTF: {r['rtf']:.2f}x")
        print(f"  Similaridade: {r['similaridade']:.1%}")
        print()

    # Verifica qual é melhor em cada métrica
    if len(resultados) == 2:
        base = resultados[0]
        medium = resultados[1]

        print("COMPARAÇÃO:")
        print(f"  Desempenho (tempo): {'base' if base['tempo'] < medium['tempo'] else 'medium'} é {medium['tempo']/base['tempo']:.1f}x mais rápido")
        print(f"  Qualidade (similaridade): {'base' if base['similaridade'] > medium['similaridade'] else 'medium'} é melhor")
        print(f"  Confiança: {'base' if base['confianca'] > medium['confianca'] else 'medium'} é melhor")
        print()

    print("=" * 70)
    print("Conclusão:")
    if len(resultados) == 2:
        if medium['similaridade'] > base['similaridade']:
            print("✅ MEDIUM tem melhor qualidade, mas é mais lento")
            if medium['rtf'] < 0.5:
                print("   RTF < 0.5x ainda é aceitável para uso interativo")
        else:
            print("✅ BASE tem qualidade similar e é mais rápido")
            print("   RECOMENDAÇÃO: Usar base para melhor desempenho")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(benchmark_stt())
