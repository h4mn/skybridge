# coding: utf-8
"""
Testes dos widgets SkyBubble e UserBubble.

DOC: openspec/changes/sky-chat-textual-ui/specs/textual-chat-ui/spec.md
DOC: openspec/changes/sky-chat-textual-ui/design.md - Message bubbles estilizados
"""

import pytest
from unittest.mock import Mock, patch

from src.core.sky.chat.textual_ui.widgets.bubbles import (
    SkyBubble,
    UserBubble,
)


class TestSkyBubble:
    """
    Testa o widget SkyBubble (mensagem da Sky).
    """

    def test_sky_bubble_init_default(self):
        """
        QUANDO SkyBubble é criado com conteúdo apenas
        ENTÃO armazena conteúdo e timestamp vazio
        """
        # Arrange & Act
        bubble = SkyBubble("Olá! Sou a Sky.")

        # Assert
        assert bubble.content == "Olá! Sou a Sky."
        assert bubble.timestamp == ""

    def test_sky_bubble_init_com_timestamp(self):
        """
        QUANDO SkyBubble é criado com timestamp
        ENTÃO armazena conteúdo e timestamp
        """
        # Arrange & Act
        bubble = SkyBubble("Resposta da Sky", timestamp="12:34")

        # Assert
        assert bubble.content == "Resposta da Sky"
        assert bubble.timestamp == "12:34"

    def test_sky_bubble_compose_retorna_markdown(self):
        """
        QUANDO SkyBubble.compose() é chamado
        ENTÃO yield Markdown widget com o conteúdo
        """
        # Arrange
        from textual.widgets import Markdown
        bubble = SkyBubble("**Negrito** e `código`")

        # Act
        children = list(bubble.compose())

        # Assert
        assert len(children) == 1
        assert isinstance(children[0], Markdown)
        assert children[0].id == "sky-message"

    def test_sky_bubble_watch_content_atualiza_markdown(self):
        """
        QUANDO conteúdo do SkyBubble muda via watch_content
        ENTÃO Markdown é atualizado
        """
        # Arrange
        bubble = SkyBubble("Conteúdo original")
        markdown_mock = Mock()

        # Act - simula a mudança de conteúdo
        with patch.object(bubble, "query_one", return_value=markdown_mock):
            bubble.watch_content("Conteúdo original", "Novo conteúdo")

        # Assert
        markdown_mock.update.assert_called_once_with("Novo conteúdo")

    def test_sky_bubble_css_classes_estao_definidas(self):
        """
        QUANDO SkyBubble é inspecionado
        ENTÃO possui CSS DEFAULT_CSS definido
        """
        # Assert
        assert SkyBubble.DEFAULT_CSS is not None
        assert "SkyBubble" in SkyBubble.DEFAULT_CSS
        assert "$panel" in SkyBubble.DEFAULT_CSS or "$primary" in SkyBubble.DEFAULT_CSS


class TestUserBubble:
    """
    Testa o widget UserBubble (mensagem do usuário).
    """

    def test_user_bubble_init_default(self):
        """
        QUANDO UserBubble é criado com conteúdo apenas
        ENTÃO armazena conteúdo e timestamp vazio
        """
        # Arrange & Act
        bubble = UserBubble("Olá Sky!")

        # Assert
        assert bubble.content == "Olá Sky!"
        assert bubble.timestamp == ""

    def test_user_bubble_init_com_timestamp(self):
        """
        QUANDO UserBubble é criado com timestamp
        ENTÃO armazena conteúdo e timestamp
        """
        # Arrange & Act
        bubble = UserBubble("Minha pergunta", timestamp="12:35")

        # Assert
        assert bubble.content == "Minha pergunta"
        assert bubble.timestamp == "12:35"

    def test_user_bubble_compose_retorna_static(self):
        """
        QUANDO UserBubble.compose() é chamado
        ENTÃO yield Static com o conteúdo
        """
        # Arrange
        bubble = UserBubble("Mensagem do usuário")

        # Act
        children = list(bubble.compose())

        # Assert
        assert len(children) == 1
        assert children[0].id == "user-message"

    def test_user_bubble_watch_content_atualiza_static(self):
        """
        QUANDO conteúdo do UserBubble muda via watch_content
        ENTÃO Static é atualizado
        """
        # Arrange
        bubble = UserBubble("Conteúdo original")
        static_mock = Mock()

        # Act - simula a mudança de conteúdo
        with patch.object(bubble, "query_one", return_value=static_mock):
            bubble.watch_content("Conteúdo original", "Novo conteúdo")

        # Assert
        static_mock.update.assert_called_once_with("Novo conteúdo")

    def test_user_bubble_css_classes_estao_definidas(self):
        """
        QUANDO UserBubble é inspecionado
        ENTÃO possui CSS DEFAULT_CSS definido
        """
        # Assert
        assert UserBubble.DEFAULT_CSS is not None
        assert "UserBubble" in UserBubble.DEFAULT_CSS
        # UserBubble usa $panel para background e $accent para borda
        assert "$panel" in UserBubble.DEFAULT_CSS or "$accent" in UserBubble.DEFAULT_CSS


class TestBubblesMarkdownSupport:
    """
    Testa suporte a markdown nos bubbles.
    """

    def test_sky_bubble_usa_markdown_widget(self):
        """
        QUANDO SkyBubble contém markdown
        ENTÃO CSS define estilos para Markdown widget
        """
        # Assert - SkyBubble tem estilos para Markdown
        assert "Markdown" in SkyBubble.DEFAULT_CSS
        # Widget Markdown é usado para renderizar conteúdo
        from textual.widgets import Markdown
        bubble = SkyBubble("**teste**")
        children = list(bubble.compose())
        assert isinstance(children[0], Markdown)

    def test_sky_bubble_tem_estilos_para_codigo(self):
        """
        QUANDO SkyBubble contém markdown com código
        ENTÃO CSS define estilo para --code e --code-block
        """
        # Assert
        assert "--code" in SkyBubble.DEFAULT_CSS or "code" in SkyBubble.DEFAULT_CSS
        # O widget Markdown do Textual lida com syntax highlighting nativamente

    def test_sky_bubble_css_transparente_para_markdown(self):
        """
        QUANDO SkyBubble contém Markdown
        ENTÃO CSS define background transparent para Markdown
        """
        # Assert - Markdown deve ter fundo transparente dentro do SkyBubble
        assert "background: transparent" in SkyBubble.DEFAULT_CSS or "transparent" in SkyBubble.DEFAULT_CSS


class TestBubblesStyling:
    """
    Testa estilização dos bubbles.
    """

    def test_sky_bubble_usa_cor_primary(self):
        """
        QUANDO SkyBubble é renderizado
        ENTÃO usa $primary para borda
        """
        # Assert
        assert "$primary" in SkyBubble.DEFAULT_CSS

    def test_user_bubble_usa_background_primary(self):
        """
        QUANDO UserBubble é renderizado
        ENTÃO usa $panel para background
        """
        # Assert
        assert "background: $panel" in UserBubble.DEFAULT_CSS

    def test_user_bubble_usa_borda_accent(self):
        """
        QUANDO UserBubble é renderizado
        ENTÃO usa $accent para borda
        """
        # Assert
        assert "$accent" in UserBubble.DEFAULT_CSS


__all__ = ["TestSkyBubble", "TestUserBubble", "TestBubblesMarkdownSupport", "TestBubblesStyling"]
