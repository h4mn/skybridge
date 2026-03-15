#!/usr/bin/env python
# coding: utf-8
"""
Informações sobre os modelos Whisper para STT.
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "B:/_repositorios/skybridge/.claude/worktrees/prd027-sky-voice/src")


async def show_model_info():
    """Mostra informações sobre os modelos Whisper."""
    from core.sky.voice.stt_service import WhisperAdapter

    # Tamanhos dos modelos Whisper
    MODELOS = {
        "tiny": {"params": "39M", "mem": "1GB", "speed": "32x", "quality": "Baixa"},
        "base": {"params": "74M", "mem": "1GB", "speed": "16x", "quality": "Média"},
        "small": {"params": "244M", "mem": "2GB", "speed": "6x", "quality": "Boa"},
        "medium": {"params": "769M", "mem": "5GB", "speed": "2x", "quality": "Alta"},
        "large": {"params": "1550M", "mem": "10GB", "speed": "1x", "quality": "Muito Alta"},
        "large-v2": {"params": "1550M", "mem": "10GB", "speed": "1x", "quality": "Muito Alta+"},
        "large-v3": {"params": "1550M", "mem": "10GB", "speed": "1x", "quality": "Melhor"},
    }

    print("=" * 70)
    print("WHISPER: Comparação de Modelos para STT")
    print("=" * 70)
    print()
    print("Modelo  | Params | Memória | Velocidade | Qualidade PT-BR")
    print("-------|--------|---------|------------|----------------")

    for model, info in MODELOS.items():
        print(f"{model:7} | {info['params']:6} | {info['mem']:7} | {info['speed']:10} | {info['quality']}")

    print()
    print("=" * 70)
    print("LEGENDA:")
    print("=" * 70)
    print("  Params    - Número de parâmetros do modelo")
    print("  Memória   - Uso de memória RAM aproximado")
    print("  Velocidade- Fator de velocidade (quanto maior, mais rápido)")
    print("  Qualidade - Avaliação qualitativa para Português Brasileiro")
    print()

    print("=" * 70)
    print("RECOMENDAÇÕES PT-BR:")
    print("=" * 70)
    print("  tiny    - Não recomendado (muitas alucinações em PT-BR)")
    print("  base    - Aceitável para uso casual (pode alucinar)")
    print("  small   - Bom equilíbrio qualidade/desempenho")
    print("  medium  - Recomendado para PT-BR (melhor precisão)")
    print("  large   - Melhor qualidade, mas mais lento")
    print()

    print("=" * 70)
    print("TESTE ATUAL: modelo BASE")
    print("=" * 70)
    print("  Vantagens:")
    print("    + Mais rápido (16x vs 2x do medium)")
    print("    + Menor uso de memória (1GB vs 5GB)")
    print("    + Modelo menor (74MB vs 769MB)")
    print()
    print("  Desvantagens:")
    print("    - Pode alucinar em PT-BR")
    print("    - Precisão menor em nomes próprios")
    print("    - Erros em números e palavras pouco comuns")
    print()

    # Mostra modelo atual
    print("=" * 70)
    print("CONFIGURAÇÃO ATUAL:")
    print("=" * 70)

    adapter_base = WhisperAdapter(model_size="base", device="cpu")
    adapter_medium = WhisperAdapter(model_size="medium", device="cpu")

    print(f"  Modelo atual: {adapter_base.model_size}")
    print(f"  Dispositivo: {adapter_base.device}")
    print(f"  Quantização: int8")
    print()

    print("Para trocar modelo, edite stt_service.py:")
    print("  def __init__(self, model_size: str = \"base\", ...):")
    print("                                       ^^^^^")
    print("  Opções: tiny, base, small, medium, large")
    print()


if __name__ == "__main__":
    asyncio.run(show_model_info())
