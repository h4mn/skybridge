#!/usr/bin/env python3
"""
Benchmark Kokoro TTS - Identificar gargalos de performance

Mede:
1. Tempo de importação
2. Tempo de carregamento do modelo
3. Tempo de síntese (1ª vez vs. 2ª vez)
4. Tempo com texto curto vs. longo
"""

import sys
import time
import os

# Adiciona src ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def benchmark_import():
    """Mede tempo de importação do kokoro."""
    start = time.perf_counter()
    from kokoro import KPipeline
    import_time = time.perf_counter() - start
    return import_time


def benchmark_model_load(lang_code='p'):
    """Mede tempo de carregamento do modelo."""
    start = time.perf_counter()
    from kokoro import KPipeline
    pipeline = KPipeline(lang_code=lang_code)
    load_time = time.perf_counter() - start
    return pipeline, load_time


def benchmark_synthesis(pipeline, text, voice='af_heart', repeat=3):
    """Mede tempo de síntese."""
    times = []
    for i in range(repeat):
        start = time.perf_counter()
        generator = pipeline(text, voice=voice, speed=1.0, split_pattern=r'\n+')
        audio_array = None
        for gs, ps, audio in generator:
            audio_array = audio
        synth_time = time.perf_counter() - start
        times.append(synth_time)

    return times


def main():
    """Executa benchmark completo."""
    print("=" * 60)
    print(" " * 15 + "Kokoro TTS Benchmark")
    print("=" * 60)
    print()

    # 1. Benchmark de importação
    print("1. Importação do kokoro...")
    import_time = benchmark_import()
    print(f"   Tempo: {import_time*1000:.1f}ms")
    print()

    # 2. Benchmark de carregamento do modelo
    print("2. Carregamento do modelo (primeira vez)...")
    pipeline, load_time = benchmark_model_load()
    print(f"   Tempo: {load_time*1000:.1f}ms ({load_time:.2f}s)")
    print()

    # 3. Benchmark de síntese - texto curto
    text_short = "Olá Sky."
    print(f"3. Síntese - texto curto ('{text_short}')...")
    times_short = benchmark_synthesis(pipeline, text_short, repeat=3)
    print(f"   1ª vez: {times_short[0]*1000:.1f}ms")
    print(f"   2ª vez: {times_short[1]*1000:.1f}ms")
    print(f"   3ª vez: {times_short[2]*1000:.1f}ms")
    print(f"   Média: {sum(times_short)/len(times_short)*1000:.1f}ms")
    print()

    # 4. Benchmark de síntese - texto médio
    text_medium = "Olá! Eu sou a Sky, sua assistente virtual."
    print(f"4. Síntese - texto médio ('{text_medium}')...")
    times_medium = benchmark_synthesis(pipeline, text_medium, repeat=3)
    print(f"   1ª vez: {times_medium[0]*1000:.1f}ms")
    print(f"   2ª vez: {times_medium[1]*1000:.1f}ms")
    print(f"   3ª vez: {times_medium[2]*1000:.1f}ms")
    print(f"   Média: {sum(times_medium)/len(times_medium)*1000:.1f}ms")
    print()

    # 5. Benchmark de síntese - texto longo
    text_long = """Olá! Eu sou a Sky, sua assistente virtual. Como posso ajudar você hoje?
    Estou aqui para responder suas perguntas e ajudar com diversas tarefas."""
    print(f"5. Síntese - texto longo ({len(text_long)} chars)...")
    times_long = benchmark_synthesis(pipeline, text_long, repeat=3)
    print(f"   1ª vez: {times_long[0]*1000:.1f}ms")
    print(f"   2ª vez: {times_long[1]*1000:.1f}ms")
    print(f"   3ª vez: {times_long[2]*1000:.1f}ms")
    print(f"   Média: {sum(times_long)/len(times_long)*1000:.1f}ms")
    print()

    # Resumo
    print("=" * 60)
    print(" " * 20 + "RESUMO")
    print("=" * 60)
    print(f"  Importação:      {import_time*1000:.1f}ms")
    print(f"  Carregamento:    {load_time*1000:.1f}ms")
    print(f"  Síntese curta:   {sum(times_short)/len(times_short)*1000:.1f}ms")
    print(f"  Síntese média:   {sum(times_medium)/len(times_medium)*1000:.1f}ms")
    print(f"  Síntese longa:   {sum(times_long)/len(times_long)*1000:.1f}ms")
    print()

    # Análise
    total_cold_start = import_time + load_time + times_medium[0]
    total_warm_start = times_medium[0]

    print(f"  Cold start (total): {total_cold_start*1000:.1f}ms")
    print(f"  Warm start (só síntese): {total_warm_start*1000:.1f}ms")
    print(f"  Ganho com modelo carregado: {(1 - total_warm_start/total_cold_start)*100:.1f}%")
    print()
    print("  CONCLUSÃO:")
    if load_time > total_warm_start * 2:
        print("  ⚠️  Carregamento do modelo é o gargalo principal!")
        print("     SOLUÇÃO: Manter modelo em memória (servidor persistente)")
    elif total_warm_start > 5000:
        print("  ⚠️  Síntese é lenta mesmo com modelo carregado")
        print("     SOLUÇÃO: Usar GPU ou modelo mais rápido")
    else:
        print("  ✓ Performance aceitável")
    print("=" * 60)


if __name__ == "__main__":
    main()
