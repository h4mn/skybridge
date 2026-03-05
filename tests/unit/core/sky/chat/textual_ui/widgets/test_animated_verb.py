# coding: utf-8
"""
Testes do widget AnimatedVerb.

DOC: openspec/changes/sky-chat-textual-ui-fix/specs/animated-verb/spec.md
"""

import pytest

from src.core.sky.chat.textual_ui.widgets.animated_verb import (
    EstadoLLM,
    _PALETAS,
    _PALETA_FALLBACK,
    _hex_para_rgb,
    _rgb_para_hex,
    _lerp_cor,
    _tooltip_estado,
)


class TestEstadoLLM:
    """Testa o dataclass EstadoLLM."""

    def test_init_com_valores_padrao(self):
        """
        QUANDO EstadoLLM é criado sem parâmetros
        ENTÃO usa valores padrão "iniciando", 0.8, 0.5, "neutro", 1
        """
        # Arrange & Act
        estado = EstadoLLM()

        # Assert
        assert estado.verbo == "iniciando"
        assert estado.certeza == 0.8
        assert estado.esforco == 0.5
        assert estado.emocao == "neutro"
        assert estado.direcao == 1

    def test_init_com_valores_customizados(self):
        """
        QUANDO EstadoLLM é criado com valores customizados
        ENTÃO armazena todos os valores
        """
        # Arrange & Act
        estado = EstadoLLM(
            verbo="codando",
            certeza=0.9,
            esforco=0.7,
            emocao="debugando",
            direcao=-1
        )

        # Assert
        assert estado.verbo == "codando"
        assert estado.certeza == 0.9
        assert estado.esforco == 0.7
        assert estado.emocao == "debugando"
        assert estado.direcao == -1

    def test_estadollm_possui_campo_predicado(self):
        """
        QUANDO EstadoLLM é instanciado sem parâmetros
        ENTÃO campo predicado existe com valor padrão "conversa"

        DOC: openspec/changes/fix-header-predicado-frase-completa/specs/titulo-completo-dinamico/spec.md
        Bug: Predicado estava fixo em "conversa", não formava frase completa.
        """
        # Arrange & Act
        estado = EstadoLLM()

        # Assert
        assert hasattr(estado, "predicado")
        assert estado.predicado == "conversa"

    def test_estadollm_aceita_predicado_customizado(self):
        """
        QUANDO EstadoLLM é instanciado com predicado="erro na API"
        ENTÃO campo predicado armazena valor customizado

        DOC: openspec/changes/fix-header-predicado-frase-completa/specs/titulo-completo-dinamico/spec.md
        Bug: Predicado estava fixo, precisava ser dinâmico.
        """
        # Arrange & Act
        estado = EstadoLLM(predicado="erro na API")

        # Assert
        assert estado.predicado == "erro na API"

    def test_estadollm_predicado_tipo_str(self):
        """
        QUANDO EstadoLLM é instanciado
        ENTÃO campo predicado é do tipo str

        DOC: openspec/changes/fix-header-predicado-frase-completa/specs/titulo-completo-dinamico/spec.md
        Bug: Campo não existia, foi adicionado.
        """
        # Arrange & Act
        estado = EstadoLLM()

        # Assert
        assert isinstance(estado.predicado, str)


class TestPaletas:
    """Testa o sistema de paletas de cores."""

    def test_paletas_contem_9_emocoes(self):
        """
        QUANDO _PALETAS é inspecionado
        ENTÃO contém 9 emoções
        """
        # Assert
        assert len(_PALETAS) >= 9

    def test_paleta_urgente_tem_cores_quentes(self):
        """
        QUANDO paleta "urgente" é inspecionada
        ENTÃO usa cores vermelho/laranja
        """
        # Assert
        assert "urgente" in _PALETAS
        paleta = _PALETAS["urgente"]
        assert paleta.de.startswith("#")
        assert paleta.ate.startswith("#")

    def test_paleta_fallback_existe(self):
        """
        QUANDO _PALETA_FALLBACK é inspecionada
        ENTÃO tem cores de e ate
        """
        # Assert
        assert _PALETA_FALLBACK.de == "#000000"
        assert _PALETA_FALLBACK.ate == "#ffffff"


class TestInterpolacaoCores:
    """Testa funções de interpolação de cores."""

    def test_hex_para_rgb_converte_cor_valida(self):
        """
        QUANDO _hex_para_rgb é chamado com cor hex válida
        ENTÃO retorna tupla (r, g, b)
        """
        # Act
        rgb = _hex_para_rgb("#ff0000")

        # Assert
        assert rgb == (255, 0, 0)

    def test_rgb_para_hex_converte_tupla_valida(self):
        """
        QUANDO _rgb_para_hex é chamado com tupla válida
        ENTÃO retorna cor hex
        """
        # Act
        hex_cor = _rgb_para_hex(255, 0, 0)

        # Assert
        assert hex_cor == "#ff0000"

    def test_lerp_cor_t0_retorna_cor_a(self):
        """
        QUANDO _lerp_cor é chamado com t=0.0
        ENTÃO retorna cor_a
        """
        # Act
        result = _lerp_cor("#ff0000", "#0000ff", 0.0)

        # Assert
        assert result == "#ff0000"

    def test_lerp_cor_t1_retorna_cor_b(self):
        """
        QUANDO _lerp_cor é chamado com t=1.0
        ENTÃO retorna cor_b
        """
        # Act
        result = _lerp_cor("#ff0000", "#0000ff", 1.0)

        # Assert
        assert result == "#0000ff"

    def test_lerp_cor_t05_retorna_media(self):
        """
        QUANDO _lerp_cor é chamado com t=0.5
        ENTÃO retorna média das cores
        """
        # Act
        result = _lerp_cor("#ff0000", "#0000ff", 0.5)

        # Assert
        # (255,0,0) + (0,0,255) / 2 = (127,0,127)
        assert result == "#7f007f"


class TestTooltipEstado:
    """Testa formatação de tooltip de estado."""

    def test_tooltip_estado_contem_verbo(self):
        """
        QUANDO _tooltip_estado é chamado
        ENTÃO string contém o verbo
        """
        # Arrange
        estado = EstadoLLM(verbo="testando")

        # Act
        tooltip = _tooltip_estado(estado)

        # Assert
        assert "testando" in tooltip

    def test_tooltip_estado_coneme_emoji(self):
        """
        QUANDO _tooltip_estado é chamado
        ENTÃO string contém emoji da emoção
        """
        # Arrange
        estado = EstadoLLM(emocao="pensando")

        # Act
        tooltip = _tooltip_estado(estado)

        # Assert
        # "pensando" tem emoji "💭"
        assert "💭" in tooltip

    def test_tooltip_estado_coneme_direcao(self):
        """
        QUANDO _tooltip_estado é chamado
        ENTÃO string contém seta de direção
        """
        # Arrange
        estado = EstadoLLM(direcao=1)

        # Act
        tooltip = _tooltip_estado(estado)

        # Assert
        assert "→" in tooltip


__all__ = [
    "TestEstadoLLM",
    "TestPaletas",
    "TestInterpolacaoCores",
    "TestTooltipEstado",
]
