#!/usr/bin/env python3
"""
Benchmark STT - Medição de desempenho do Whisper

Este script mede detalhadamente o tempo gasto em cada etapa:
- Captura de áudio
- Carregamento do modelo
- Transcrição (Whisper)
- Total

Usage:
    python scripts/benchmark_stt.py [--duration SECONDS] [--model SIZE]
"""

import asyncio
import os
import sys
import time
import psutil
from dataclasses import dataclass
from typing import Optional

# Adiciona src ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from core.sky.voice.audio_capture import SoundDeviceCapture
from core.sky.voice.stt_service import WhisperAdapter, TranscriptionConfig


@dataclass
class BenchmarkResult:
    """Resultado do benchmark."""

    # Tempos em segundos
    capture_time: float
    model_load_time: float
    transcription_time: float
    total_time: float

    # Dados de áudio
    audio_duration: float
    audio_size_bytes: int

    # Memória
    memory_before_mb: float
    memory_after_mb: float
    memory_used_mb: float

    # Resultado
    text: str
    language: str
    confidence: float

    @property
    def realtime_factor(self) -> float:
        """Fator de tempo real (RTF).

        RTF = tempo_transcricao / duracao_audio
        RTF < 1.0 = mais rápido que o tempo real
        RTF = 1.0 = tempo real
        RTF > 1.0 = mais lento que o tempo real
        """
        if self.audio_duration == 0:
            return 0.0
        return self.transcription_time / self.audio_duration

    def format_time(self, seconds: float) -> str:
        """Formata tempo para exibição."""
        if seconds < 0.001:
            return f"{seconds * 1000000:.1f}µs"
        elif seconds < 1:
            return f"{seconds * 1000:.1f}ms"
        else:
            return f"{seconds:.2f}s"


def print_header(title: str) -> None:
    """Imprime cabeçalho formatado."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title: str) -> None:
    """Imprime seção formatada."""
    print(f"\n  {title}")
    print("  " + "-" * 56)


async def run_benchmark(
    duration: float = 5.0,
    model_size: str = "base",
    device: str = "cpu",
) -> BenchmarkResult:
    """Executa benchmark completo."""

    print_header("🚀 STT BENCHMARK - WHISPER")

    print(f"\n  Configuração:")
    print(f"    Duração da gravação: {duration}s")
    print(f"    Modelo Whisper: {model_size}")
    print(f"    Device: {device}")
    print(f"    Processador: {psutil.cpu_count()} cores")
    print(f"    Memória disponível: {psutil.virtual_memory().total / (1024**3):.1f} GB")

    # Memória antes
    process = psutil.Process()
    memory_before = process.memory_info().rss / (1024 * 1024)  # MB

    print_section("1. CAPTURA DE ÁUDIO")

    capture = SoundDeviceCapture(sample_rate=16000, channels=1)

    print("  >>> Fale algo agora! <<<")
    for i in range(3, 0, -1):
        print(f"     Iniciando em {i}...", end="\r")
        await asyncio.sleep(1)

    print("\n  ** GRAVANDO **")

    capture_start = time.perf_counter()
    await capture.start_recording()

    # Medição precisa da duração
    recording_start = time.perf_counter()
    elapsed = 0.0
    while elapsed < duration:
        await asyncio.sleep(0.05)
        elapsed = time.perf_counter() - recording_start
        remaining = duration - elapsed
        print(f"  Gravando... {remaining:.1f}s restantes", end="\r")

    print()

    capture_end = time.perf_counter()
    audio = await capture.stop_recording()

    capture_time = capture_end - capture_start
    actual_duration = audio.duration

    print(f"\n  ✓ Captura concluída")
    print(f"    Tempo de captura: {capture_time:.2f}s")
    print(f"    Duração do áudio: {actual_duration:.2f}s")
    print(f"    Tamanho: {len(audio.samples):,} bytes ({len(audio.samples) / 1024:.1f} KB)")

    print_section("2. CARREGAMENTO DO MODELO")

    model_load_start = time.perf_counter()
    stt = WhisperAdapter(model_size=model_size, device=device)

    # Força carregamento do modelo
    stt._load_model()
    model_load_end = time.perf_counter()

    model_load_time = model_load_end - model_load_start

    print(f"  ✓ Modelo carregado")
    print(f"    Tempo de carregamento: {model_load_time:.2f}s")

    # Memória após carregar modelo
    memory_after_model = process.memory_info().rss / (1024 * 1024)  # MB
    memory_for_model = memory_after_model - memory_before

    print(f"    Memória do modelo: {memory_for_model:.1f} MB")

    print_section("3. TRANSCRIÇÃO (WHISPER)")

    transcription_start = time.perf_counter()

    result = await stt.transcribe(
        audio,
        config=TranscriptionConfig(language="pt", detect_language=False),
    )

    transcription_end = time.perf_counter()
    transcription_time = transcription_end - transcription_start

    print(f"  ✓ Transcrição concluída")
    print(f"    Tempo de transcrição: {transcription_time:.2f}s")
    print(f"    Resultado: \"{result.text}\"")
    print(f"    Idioma: {result.language}")
    print(f"    Confiança: {result.confidence:.1%}")

    # Memória final
    memory_after = process.memory_info().rss / (1024 * 1024)  # MB
    memory_used = memory_after - memory_before

    print_section("4. RESUMO DE DESEMPENHO")

    total_time = transcription_end - capture_start

    print(f"\n  ⏱️  TEMPOS")
    print(f"     Captura de áudio:    {capture_time:.3f}s ({capture_time/total_time*100:.1f}%)")
    print(f"     Carregamento modelo: {model_load_time:.3f}s ({model_load_time/total_time*100:.1f}%)")
    print(f"     Transcrição:         {transcription_time:.3f}s ({transcription_time/total_time*100:.1f}%)")
    print(f"     ────────────────────────────────────")
    print(f"     TOTAL:               {total_time:.3f}s")

    rtf = transcription_time / actual_duration if actual_duration > 0 else 0
    print(f"\n  📊 MÉTRICAS")
    print(f"     Fator RTF:           {rtf:.2f}x")
    print(f"     (RTF < 1.0 = mais rápido que tempo real)")

    if rtf < 0.1:
        speed_rating = "🚀 EXCELENTE (< 0.1x)"
    elif rtf < 0.5:
        speed_rating = "✅ MUITO BOM (< 0.5x)"
    elif rtf < 1.0:
        speed_rating = "✓ BOM (< 1.0x)"
    elif rtf < 2.0:
        speed_rating = "~ ACEITÁVEL (< 2.0x)"
    else:
        speed_rating = "⚠ LENTO (> 2.0x)"

    print(f"     Avaliação:           {speed_rating}")

    print(f"\n  💾 MEMÓRIA")
    print(f"     Antes:               {memory_before:.1f} MB")
    print(f"     Depois:              {memory_after:.1f} MB")
    print(f"     Usada:               {memory_used:.1f} MB")
    print(f"     Modelo:              {memory_for_model:.1f} MB")

    print("\n" + "=" * 60)

    return BenchmarkResult(
        capture_time=capture_time,
        model_load_time=model_load_time,
        transcription_time=transcription_time,
        total_time=total_time,
        audio_duration=actual_duration,
        audio_size_bytes=len(audio.samples),
        memory_before_mb=memory_before,
        memory_after_mb=memory_after,
        memory_used_mb=memory_used,
        text=result.text,
        language=result.language,
        confidence=result.confidence,
    )


async def main():
    """Função principal."""

    import argparse

    parser = argparse.ArgumentParser(description="Benchmark STT - Whisper")
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Duração da gravação em segundos (padrão: 5.0)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Tamanho do modelo Whisper (padrão: base)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="Dispositivo de execução (padrão: cpu)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Número de execuções do benchmark (padrão: 1)",
    )

    args = parser.parse_args()

    results = []

    for run in range(args.runs):
        if args.runs > 1:
            print(f"\n\n  === EXECUÇÃO {run + 1}/{args.runs} ===\n")

        result = await run_benchmark(
            duration=args.duration,
            model_size=args.model,
            device=args.device,
        )
        results.append(result)

        # Pausa entre runs
        if run < args.runs - 1:
            print(f"\n  ⏸️  Pausa de 3 segundos antes da próxima execução...")
            await asyncio.sleep(3)

    # Múltiplas runs: mostra estatísticas agregadas
    if len(results) > 1:
        print_header("📈 ESTATÍSTICAS AGREGADAS")

        avg_transcription = sum(r.transcription_time for r in results) / len(results)
        min_transcription = min(r.transcription_time for r in results)
        max_transcription = max(r.transcription_time for r in results)

        avg_rtf = sum(r.realtime_factor for r in results) / len(results)

        print(f"\n  Tempo de transcrição:")
        print(f"     Média: {avg_transcription:.3f}s")
        print(f"     Mín:   {min_transcription:.3f}s")
        print(f"     Máx:   {max_transcription:.3f}s")

        print(f"\n  Fator RTF:")
        print(f"     Média: {avg_rtf:.2f}x")

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Benchmark interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n  ❌ Erro: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
