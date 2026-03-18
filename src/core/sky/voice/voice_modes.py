# -*- coding: utf-8 -*-
"""
Voice Modes - Modos de voz e hesitações para TTS.

Define VoiceMode enum e dicionário de hesitações Kokoro-friendly
para modo thinking.
"""

import random
from enum import Enum
from typing import Literal


class VoiceMode(Enum):
    """Modos de voz disponíveis."""

    NORMAL = "normal"      # Velocidade normal, sem hesitações
    THINKING = "thinking"  # Mais lento, com hesitações naturais


# =============================================================================
# HESITAÇÕES KOKORO-FRIENDLY
# =============================================================================
# NOTA: Evitar "hmm", "uh", "hnn" - Kokoro soletra.
# Usar palavras reais: "hum", "é", "bom", etc.

HESITATIONS = {
    # Hesitações de início (antes de começar a pensar)
    "starters": [
        "deixa eu pensar...",
        "bom...",
        "então...",
        "vejamos...",
        "olha...",
        "hum...",
        "interessante...",
        "assim...",
        "bem...",
        "é...",
        "perai...",
        "deixa ver...",
    ],

    # Reações pós-tool (após receber resultado de ferramenta)
    "post_tool": {
        # Resultado positivo/útil
        "positive": [
            "ah, interessante...",
            "ótimo...",
            "perfeito...",
            "legal...",
            "bacana...",
            "beleza...",
            "show...",
            "que bom...",
        ],

        # Resultado surpreendente
        "surprise": [
            "nossa...",
            "olha só...",
            "caramba...",
            "puxa vida...",
            "uau...",
        ],

        # Resultado esperado/confirmação
        "expected": [
            "como esperado...",
            "certo...",
            "ok...",
            "entendi...",
            "faz sentido...",
            "exatamente...",
        ],

        # Resultado que gera dúvida
        "doubt": [
            "mas pera...",
            "interessante, mas...",
            "ok, mas...",
            "espera um pouco...",
        ],

        # Precisa processar mais
        "processing": [
            "deixa eu processar isso...",
            "analisando...",
            "processando...",
            "avaliando...",
        ],
    },

    # Pausas (usadas para delay, não faladas)
    "pauses": [
        "...",
        "......",
    ],

    # Transições (conectando ideias)
    "transitions": [
        "e então...",
        "ou seja...",
        "por outro lado...",
        "agora...",
        "na verdade...",
        "além disso...",
        "sendo assim...",
    ],

    # Confirmações internas
    "confirmations": [
        "certo...",
        "ok...",
        "entendi...",
        "ah, sim...",
        "exato...",
        "claro...",
    ],

    # Raciocínio/dúvidas
    "reasoning": [
        "será que...",
        "talvez...",
        "pode ser que...",
        "me parece que...",
        "se eu considerar...",
    ],
}


def get_reaction(
    context: Literal["start", "post_tool", "pause", "transition"],
    tool_result_type: Literal["positive", "surprise", "expected", "doubt", "processing"] = "positive",
    intensity: float = 0.5,
) -> str:
    """
    Retorna uma reação/hesitação baseada no contexto.

    Args:
        context: Onde a reação será inserida
        tool_result_type: Tipo de resultado (só usado se context="post_tool")
        intensity: Probabilidade de retornar uma reação (0.0-1.0)

    Returns:
        Reação ou string vazia se intensity não atingir threshold
    """
    if random.random() > intensity:
        return ""

    if context == "start":
        return random.choice(HESITATIONS["starters"])

    elif context == "post_tool":
        reactions = HESITATIONS["post_tool"].get(
            tool_result_type,
            HESITATIONS["post_tool"]["positive"]
        )
        return random.choice(reactions)

    elif context == "pause":
        return random.choice(HESITATIONS["pauses"])

    elif context == "transition":
        return random.choice(HESITATIONS["transitions"])

    return ""


def add_hesitations(text: str, intensity: float = 0.3) -> str:
    """
    Adiciona hesitações naturais ao texto para modo thinking.

    Args:
        text: Texto original
        intensity: 0.0-1.0 (quanto maior, mais hesitações)

    Returns:
        Texto com hesitações inseridas
    """
    if intensity <= 0:
        return text

    words = text.split()
    result = []

    # Chance de hesitação no início
    if random.random() < intensity:
        result.append(random.choice(HESITATIONS["starters"]))

    for i, word in enumerate(words):
        result.append(word)

        # Após pontuação, pode ter hesitação
        if word.endswith((".", ",", ":", ";")):
            if random.random() < intensity * 0.5:
                transition = random.choice(HESITATIONS["transitions"])
                result.append(transition)

        # A cada ~5-10 palavras, pode ter transição
        if i > 0 and i % random.randint(5, 10) == 0:
            if random.random() < intensity * 0.3:
                transition = random.choice(HESITATIONS["transitions"])
                result.append(transition)

    return " ".join(result)


__all__ = [
    "VoiceMode",
    "HESITATIONS",
    "get_reaction",
    "add_hesitations",
]
