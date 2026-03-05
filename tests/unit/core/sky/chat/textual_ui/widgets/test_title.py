# coding: utf-8
"""
Testes do widget AnimatedTitle.

DOC: openspec/changes/sky-chat-textual-ui-fix/specs/textual-title-composition/spec.md
DOC: openspec/changes/sky-chat-textual-ui-fix/design.md - Título dinâmico com verbo animado
"""

import pytest

from src.core.sky.chat.textual_ui.widgets.title import AnimatedTitle


class TestAnimatedTitleInit:
    """
    Testa inicialização do AnimatedTitle.
    """

    def test_init_com_valores_padrao(self):
        """
        QUANDO AnimatedTitle é criado sem parâmetros
        ENTÃO usa valores padrão "Sky iniciando conversa"
        """
        # Arrange & Act
        title = AnimatedTitle()

        # Assert - usa atributos privados
        assert title._sujeito == "Sky"
        assert title._verbo == "iniciando"
        assert title._predicado == "conversa"

    def test_init_com_valores_customizados(self):
        """
        QUANDO AnimatedTitle é criado com valores customizados
        ENTÃO armazena sujeito, verbo e predicado
        """
        # Arrange & Act
        title = AnimatedTitle(
            sujeito="Sky",
            verbo="debugando",
            predicado="erro na API"
        )

        # Assert
        assert title._sujeito == "Sky"
        assert title._verbo == "debugando"
        assert title._predicado == "erro na API"

    def test_init_com_verbo_em_gerundio(self):
        """
        QUANDO verbo está no gerúndio
        ENTÃO é armazenado corretamente
        """
        # Arrange & Act
        title = AnimatedTitle(verbo="aprendendo")

        # Assert
        assert title._verbo == "aprendendo"


class TestAnimatedTitleCompose:
    """
    Testa composição do AnimatedTitle.
    """

    def test_compose_retorna_3_widgets(self):
        """
        QUANDO compose() é chamado
        ENTÃO retorna 3 widgets filhos (Static, AnimatedVerb, Static)
        """
        # Arrange
        title = AnimatedTitle(
            sujeito="Sky",
            verbo="testando",
            predicado="o código"
        )

        # Act
        widgets = list(title.compose())

        # Assert
        assert len(widgets) == 3
        # Verifica se são os tipos corretos
        assert widgets[0].__class__.__name__ == "Static"
        assert widgets[1].__class__.__name__ == "AnimatedVerb"
        assert widgets[2].__class__.__name__ == "Static"

    def test_compose_primeiro_widget_tem_sujeito_bold(self):
        """
        QUANDO compose() é chamado com verbo em gerúndio
        ENTÃO primeiro Static contém "Sky está" com markup bold
        """
        # Arrange
        title = AnimatedTitle(sujeito="Sky", verbo="testando")

        # Act
        widgets = list(title.compose())

        # Assert
        first_static = widgets[0]
        # O render pode retornar Rich ou string, verificamos o conteúdo
        rendered = str(first_static.render())
        assert "Sky está" in rendered

    def test_compose_primeiro_widget_sem_esta_quando_passado(self):
        """
        QUANDO compose() é chamado com verbo no passado
        ENTÃO primeiro Static contém apenas "Sky" (sem "está")
        """
        # Arrange
        title = AnimatedTitle(sujeito="Sky", verbo="buscou")

        # Act
        widgets = list(title.compose())

        # Assert
        first_static = widgets[0]
        rendered = str(first_static.render())
        # Deve ter "Sky" mas NÃO "está"
        assert "Sky" in rendered
        assert "está" not in rendered

    def test_compose_segundo_widget_e_animated_verb(self):
        """
        QUANDO compose() é chamado
        ENTÃO segundo widget é AnimatedVerb com apenas o verbo (sem "está")
        """
        # Arrange
        title = AnimatedTitle(verbo="processando")

        # Act
        widgets = list(title.compose())

        # Assert
        animated_verb = widgets[1]
        assert animated_verb.__class__.__name__ == "AnimatedVerb"
        # Verifica que o AnimatedVerb tem apenas o verbo, sem "está"
        assert animated_verb.texto == "processando"

    def test_compose_terceiro_widget_tem_predicado(self):
        """
        QUANDO compose() é chamado
        ENTÃO terceiro Static contém predicado
        """
        # Arrange
        title = AnimatedTitle(predicado="online")

        # Act
        widgets = list(title.compose())

        # Assert
        third_static = widgets[2]
        rendered = str(third_static.render())
        assert "online" in rendered


class TestAnimatedTitleUpdate:
    """
    Testa atualização dinâmica do AnimatedTitle.
    """

    def test_update_title_muda_verbo_e_predicado(self):
        """
        QUANDO update_title() é chamado
        ENTÃO atualiza os atributos internos (requer app Textual para query_one)
        """
        # Este teste requer um app Textual rodando para funcionar
        pytest.skip("Requer app Textual rodando para query_one()")

    def test_update_title_preserva_sujeito(self):
        """
        QUANDO update_title() é chamado
        ENTÃO preserva sujeito original (requer app Textual para query_one)
        """
        # Este teste requer um app Textual rodando para funcionar
        pytest.skip("Requer app Textual rodando para query_one()")


class TestAnimatedTitleCss:
    """
    Testa CSS do AnimatedTitle.
    """

    def test_possui_css_default_definido(self):
        """
        QUANDO AnimatedTitle é inspecionado
        ENTÃO possui DEFAULT_CSS definido
        """
        # Assert
        assert AnimatedTitle.DEFAULT_CSS is not None

    def test_css_inclui_layout_horizontal(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui layout: horizontal
        """
        # Assert
        assert "layout: horizontal" in AnimatedTitle.DEFAULT_CSS

    def test_css_inclui_height_1(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui height: 1
        """
        # Assert
        assert "height: 1" in AnimatedTitle.DEFAULT_CSS

    def test_css_inclui_width_auto(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui width: auto
        """
        # Assert
        assert "width: auto" in AnimatedTitle.DEFAULT_CSS


class TestTitleStatic:
    """
    Testa o widget TitleStatic.
    """

    def test_extrair_radical_gerundio_ando(self):
        """
        QUANDO verbo termina em -ando
        ENTÃO extrai radical corretamente
        """
        from src.core.sky.chat.textual_ui.widgets.title import TitleStatic

        # Assert
        assert TitleStatic._extrair_radical("processando") == "process"
        assert TitleStatic._extrair_radical("analisando") == "analis"
        assert TitleStatic._extrair_radical("buscando") == "busc"

    def test_extrair_radical_gerundio_endo(self):
        """
        QUANDO verbo termina em -endo
        ENTÃO extrai radical corretamente
        """
        from src.core.sky.chat.textual_ui.widgets.title import TitleStatic

        # Assert
        assert TitleStatic._extrair_radical("escrevendo") == "escrev"
        assert TitleStatic._extrair_radical("correndo") == "corr"

    def test_extrair_radical_gerundio_indo(self):
        """
        QUANDO verbo termina em -indo
        ENTÃO extrai radical corretamente
        """
        from src.core.sky.chat.textual_ui.widgets.title import TitleStatic

        # Assert
        assert TitleStatic._extrair_radical("corrigindo") == "corrig"
        assert TitleStatic._extrair_radical("emitindo") == "emit"

    def test_extrair_radical_preterito_ou(self):
        """
        QUANDO verbo termina em -ou (pretérito)
        ENTÃO extrai radical corretamente
        """
        from src.core.sky.chat.textual_ui.widgets.title import TitleStatic

        # Assert
        assert TitleStatic._extrair_radical("processou") == "process"
        assert TitleStatic._extrair_radical("analisou") == "analis"
        assert TitleStatic._extrair_radical("buscou") == "busc"

    def test_extrair_radical_preterito_eu(self):
        """
        QUANDO verbo termina em -eu (pretérito)
        ENTÃO extrai radical corretamente
        """
        from src.core.sky.chat.textual_ui.widgets.title import TitleStatic

        # Assert
        assert TitleStatic._extrair_radical("escreveu") == "escrev"
        assert TitleStatic._extrair_radical("correu") == "corr"

    def test_extrair_radical_preterito_iu(self):
        """
        QUANDO verbo termina em -iu (pretérito)
        ENTÃO extrai radical corretamente
        """
        from src.core.sky.chat.textual_ui.widgets.title import TitleStatic

        # Assert
        assert TitleStatic._extrair_radical("corrigiu") == "corrig"
        assert TitleStatic._extrair_radical("emitiu") == "emit"

    def test_extrair_radical_verbo_curto_fallback(self):
        """
        QUANDO verbo é muito curto ou não segue padrões
        ENTÃO retorna o próprio verbo como fallback
        """
        from src.core.sky.chat.textual_ui.widgets.title import TitleStatic

        # Assert
        assert TitleStatic._extrair_radical("iu") == "iu"
        assert TitleStatic._extrair_radical("ou") == "ou"


class TestAnimatedTitleFormatos:
    """
    Testa diferentes formatos de título.
    """

    def test_formato_sky_debugando_erro_api(self):
        """
        QUANDO título é "Sky debugando erro na API"
        ENTÃO compõe 3 widgets corretamente
        """
        # Arrange & Act
        title = AnimatedTitle(
            sujeito="Sky",
            verbo="debugando",
            predicado="erro na API"
        )
        widgets = list(title.compose())

        # Assert
        assert len(widgets) == 3
        assert title._sujeito == "Sky"
        assert title._verbo == "debugando"
        assert title._predicado == "erro na API"

    def test_formato_sky_aprendendo_async_python(self):
        """
        QUANDO título é "Sky aprendendo async Python"
        ENTÃO compõe 3 widgets corretamente
        """
        # Arrange & Act
        title = AnimatedTitle(
            sujeito="Sky",
            verbo="aprendendo",
            predicado="async Python"
        )
        widgets = list(title.compose())

        # Assert
        assert len(widgets) == 3
        assert title._sujeito == "Sky"
        assert title._verbo == "aprendendo"
        assert title._predicado == "async Python"

    def test_formato_sky_conversando_sobre_filosofia(self):
        """
        QUANDO título é "Sky conversando sobre filosofia"
        ENTÃO compõe 3 widgets corretamente
        """
        # Arrange & Act
        title = AnimatedTitle(
            sujeito="Sky",
            verbo="conversando",
            predicado="sobre filosofia"
        )
        widgets = list(title.compose())

        # Assert
        assert len(widgets) == 3
        assert title._sujeito == "Sky"
        assert title._verbo == "conversando"
        assert title._predicado == "sobre filosofia"


__all__ = [
    "TestAnimatedTitleInit",
    "TestAnimatedTitleCompose",
    "TestAnimatedTitleUpdate",
    "TestAnimatedTitleCss",
    "TestAnimatedTitleFormatos",
    "TestTitleStatic",
]
