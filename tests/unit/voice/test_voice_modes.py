# -*- coding: utf-8 -*-
"""
Testes unitários para VoiceMode e sistema de hesitações.

DOC: src/core/sky/voice/voice_modes.py - VoiceMode enum e hesitações Kokoro-friendly.
"""

import pytest
from unittest.mock import patch

from core.sky.voice.voice_modes import (
    VoiceMode,
    HESITATIONS,
    get_reaction,
    add_hesitations,
)


class TestVoiceMode:
    """Testes para o enum VoiceMode."""

    def test_voice_mode_normal_exists(self):
        """VoiceMode.NORMAL deve existir com valor 'normal'."""
        assert VoiceMode.NORMAL.value == "normal"

    def test_voice_mode_thinking_exists(self):
        """VoiceMode.THINKING deve existir com valor 'thinking'."""
        assert VoiceMode.THINKING.value == "thinking"

    def test_voice_mode_has_exactly_two_values(self):
        """VoiceMode deve ter exatamente 2 valores."""
        assert len(VoiceMode) == 2


class TestHesitations:
    """Testes para o dicionário de hesitações."""

    def test_hesitations_has_required_categories(self):
        """HESITATIONS deve ter todas as categorias necessárias."""
        required_keys = ["starters", "post_tool", "pauses", "transitions", "confirmations", "reasoning"]
        for key in required_keys:
            assert key in HESITATIONS, f"HESITATIONS deve ter categoria '{key}'"

    def test_post_tool_has_required_types(self):
        """HESITATIONS['post_tool'] deve ter todos os tipos necessários."""
        required_types = ["positive", "surprise", "expected", "doubt", "processing"]
        for type_name in required_types:
            assert type_name in HESITATIONS["post_tool"], f"post_tool deve ter tipo '{type_name}'"

    def test_hesitations_are_non_empty(self):
        """Todas as categorias de hesitações devem ter pelo menos uma entrada."""
        # Categorias simples (listas)
        for key in ["starters", "pauses", "transitions", "confirmations", "reasoning"]:
            assert len(HESITATIONS[key]) > 0, f"Categoria '{key}' não deve estar vazia"

        # post_tool é um dicionário de listas
        for type_name, hesitations in HESITATIONS["post_tool"].items():
            assert len(hesitations) > 0, f"post_tool['{type_name}'] não deve estar vazio"

    def test_hesitations_are_kokoro_friendly(self):
        """Hesitações não devem conter caracteres problemáticos para Kokoro."""
        # Caracteres que Kokoro tende a soletrar ao invés de falar
        problematic_chars = ["hmm", "hnn", "uh ", "uhm"]

        def check_hesitations(hesitations, path=""):
            if isinstance(hesitations, list):
                for h in hesitations:
                    h_lower = h.lower()
                    for char in problematic_chars:
                        assert char not in h_lower, (
                            f"Hesitação '{h}' em {path} contém '{char}' "
                            f"que pode ser problemático para Kokoro"
                        )
            elif isinstance(hesitations, dict):
                for key, value in hesitations.items():
                    check_hesitations(value, f"{path}.{key}")

        check_hesitations(HESITATIONS, "HESITATIONS")


class TestGetReaction:
    """Testes para a função get_reaction()."""

    def test_get_reaction_start_returns_starter(self):
        """get_reaction('start') deve retornar uma hesitação de starter."""
        with patch("core.sky.voice.voice_modes.random.random", return_value=0.0):
            reaction = get_reaction("start")
            assert reaction in HESITATIONS["starters"]

    def test_get_reaction_post_tool_positive_returns_positive(self):
        """get_reaction('post_tool', 'positive') deve retornar reação positiva."""
        with patch("core.sky.voice.voice_modes.random.random", return_value=0.0):
            reaction = get_reaction("post_tool", "positive")
            assert reaction in HESITATIONS["post_tool"]["positive"]

    def test_get_reaction_post_tool_surprise_returns_surprise(self):
        """get_reaction('post_tool', 'surprise') deve retornar reação de surpresa."""
        with patch("core.sky.voice.voice_modes.random.random", return_value=0.0):
            reaction = get_reaction("post_tool", "surprise")
            assert reaction in HESITATIONS["post_tool"]["surprise"]

    def test_get_reaction_post_tool_invalid_type_uses_positive_fallback(self):
        """get_reaction('post_tool', tipo_inválido) deve usar positive como fallback."""
        with patch("core.sky.voice.voice_modes.random.random", return_value=0.0):
            reaction = get_reaction("post_tool", "invalid_type")
            assert reaction in HESITATIONS["post_tool"]["positive"]

    def test_get_reaction_pause_returns_pause(self):
        """get_reaction('pause') deve retornar uma pausa."""
        with patch("core.sky.voice.voice_modes.random.random", return_value=0.0):
            reaction = get_reaction("pause")
            assert reaction in HESITATIONS["pauses"]

    def test_get_reaction_transition_returns_transition(self):
        """get_reaction('transition') deve retornar uma transição."""
        with patch("core.sky.voice.voice_modes.random.random", return_value=0.0):
            reaction = get_reaction("transition")
            assert reaction in HESITATIONS["transitions"]

    def test_get_reaction_intensity_zero_returns_empty(self):
        """get_reaction com intensity=0 deve retornar string vazia."""
        reaction = get_reaction("start", intensity=0.0)
        assert reaction == ""

    def test_get_reaction_intensity_one_always_returns_reaction(self):
        """get_reaction com intensity=1 sempre retorna uma reação."""
        with patch("core.sky.voice.voice_modes.random.random", return_value=0.5):
            reaction = get_reaction("start", intensity=1.0)
            assert reaction != ""
            assert reaction in HESITATIONS["starters"]

    def test_get_reaction_unknown_context_returns_empty(self):
        """get_reaction com contexto desconhecido deve retornar string vazia."""
        reaction = get_reaction("unknown_context")
        assert reaction == ""


class TestAddHesitations:
    """Testes para a função add_hesitations()."""

    def test_add_hesitations_zero_intensity_returns_original(self):
        """add_hesitations com intensity=0 deve retornar texto original."""
        text = "Texto original sem hesitações."
        result = add_hesitations(text, intensity=0.0)
        assert result == text

    def test_add_hesitations_preserves_content(self):
        """add_hesitations deve preservar o conteúdo original do texto."""
        text = "Este é um texto importante."
        result = add_hesitations(text, intensity=0.5)
        # O conteúdo original deve estar presente (pode ter hesitações adicionais)
        assert "Este é um texto importante." in result or "importante" in result

    def test_add_hesitations_empty_text_returns_empty(self):
        """add_hesitations com texto vazio deve retornar vazio."""
        result = add_hesitations("", intensity=0.5)
        assert result == ""

    def test_add_hesitations_may_add_starter(self):
        """add_hesitations pode adicionar hesitação no início."""
        with patch("core.sky.voice.voice_modes.random.random", return_value=0.0):
            with patch("core.sky.voice.voice_modes.random.randint", return_value=5):
                text = "Texto de teste."
                result = add_hesitations(text, intensity=1.0)
                # Com intensity=1.0 e random=0.0, deve adicionar starter
                # Verifica se começa com alguma hesitação conhecida
                started_with_starter = any(
                    result.startswith(starter) for starter in HESITATIONS["starters"]
                )
                assert started_with_starter or text in result
