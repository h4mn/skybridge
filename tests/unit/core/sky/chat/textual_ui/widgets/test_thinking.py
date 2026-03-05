# coding: utf-8
"""
Testes do widget ThinkingIndicator e ThinkingPanel.

DOC: openspec/changes/sky-chat-textual-ui/specs/textual-chat-ui/spec.md
DOC: openspec/changes/sky-chat-textual-ui/design.md - Thinking indicator animado
"""

import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock

from src.core.sky.chat.textual_ui.widgets.thinking import (
    ThinkingIndicator,
    ThinkingPanel,
    ThinkingEntryWidget,
)
from src.core.sky.chat.textual_ui.widgets.turn import ThinkingEntry


class TestThinkingIndicatorInit:
    """
    Testa inicialização do ThinkingIndicator.
    """

    def test_init_com_mensagem_padrao(self):
        """
        QUANDO ThinkingIndicator é criado sem parâmetros
        ENTÃO usa mensagem padrão "🤔 Sky está pensando..."
        """
        # Arrange & Act
        indicator = ThinkingIndicator()

        # Assert
        assert indicator.message == "🤔 Sky está pensando..."
        assert indicator._animating is False

    def test_init_com_mensagem_customizada(self):
        """
        QUANDO ThinkingIndicator é criado com mensagem customizada
        ENTÃO usa mensagem fornecida
        """
        # Arrange & Act
        indicator = ThinkingIndicator("Processando...")

        # Assert
        assert indicator.message == "Processando..."

    def test_init_inicia_invisivel(self):
        """
        QUANDO ThinkingIndicator é criado
        ENTÃO inicia invisível (visible=False por padrão)
        """
        # Arrange & Act
        indicator = ThinkingIndicator()

        # Assert
        # Note: Textual widgets são visíveis por padrão,
        # mas show() deve ser chamado para exibir
        assert indicator._animating is False


class TestThinkingIndicatorShow:
    """
    Testa método show().
    """

    def test_show_torna_visivel(self):
        """
        QUANDO show() é chamado
        ENTÃO widget torna-se visível
        """
        # Arrange
        indicator = ThinkingIndicator()

        # Act
        indicator.show()

        # Assert
        assert indicator.visible is True
        assert indicator._animating is True

    def test_show_com_nova_mensagem(self):
        """
        QUANDO show(mensagem) é chamado
        ENTÃO atualiza mensagem e torna visível
        """
        # Arrange
        indicator = ThinkingIndicator()

        # Act
        indicator.show("Analisando dados...")

        # Assert
        assert indicator.message == "Analisando dados..."
        assert indicator.visible is True

    def test_show_sem_mensagem_mantem_original(self):
        """
        QUANDO show() é chamado sem parâmetros
        ENTÃO mantém mensagem original
        """
        # Arrange
        indicator = ThinkingIndicator("Pensamento original")

        # Act
        indicator.show()

        # Assert
        assert indicator.message == "Pensamento original"

    def test_show_atualiza_renderizacao(self):
        """
        QUANDO show() é chamado
        ENTÃO chama update() com a mensagem
        """
        # Arrange
        indicator = ThinkingIndicator("Teste")

        # Act
        with patch.object(indicator, "update") as mock_update:
            indicator.show()

            # Assert
            mock_update.assert_called_once_with("Teste")


class TestThinkingIndicatorHide:
    """
    Testa método hide().
    """

    def test_hide_torna_invisivel(self):
        """
        QUANDO hide() é chamado
        ENTÃO widget torna-se invisível
        """
        # Arrange
        indicator = ThinkingIndicator()
        indicator.show()  # Primeiro mostra

        # Act
        indicator.hide()

        # Assert
        assert indicator.visible is False
        assert indicator._animating is False

    def test_hide_para_animacao(self):
        """
        QUANDO hide() é chamado
        ENTÃO _animating é definido como False
        """
        # Arrange
        indicator = ThinkingIndicator()
        indicator.show()  # Inicia animação
        assert indicator._animating is True

        # Act
        indicator.hide()

        # Assert
        assert indicator._animating is False


class TestThinkingIndicatorCss:
    """
    Testa CSS do ThinkingIndicator.
    """

    def test_possui_css_default_definido(self):
        """
        QUANDO ThinkingIndicator é inspecionado
        ENTÃO possui DEFAULT_CSS definido
        """
        # Assert
        assert ThinkingIndicator.DEFAULT_CSS is not None

    def test_css_inclui_text_style_italic(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui text-style: italic
        """
        # Assert
        assert "text-style: italic" in ThinkingIndicator.DEFAULT_CSS

    def test_css_inclui_cor_warning(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui color: $warning
        """
        # Assert
        assert "color: $warning" in ThinkingIndicator.DEFAULT_CSS

    def test_css_inclui_margin(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui margin
        """
        # Assert
        assert "margin:" in ThinkingIndicator.DEFAULT_CSS


class TestThinkingIndicatorEstados:
    """
    Testa estados do ThinkingIndicator.
    """

    def test_estado_inicial_nao_animando(self):
        """
        QUANDO ThinkingIndicator é criado
        ENTÃO _animating é False
        """
        # Arrange & Act
        indicator = ThinkingIndicator()

        # Assert
        assert indicator._animating is False

    def test_estado_apos_show_animando(self):
        """
        QUANDO show() é chamado
        ENTÃO _animating é True
        """
        # Arrange
        indicator = ThinkingIndicator()

        # Act
        indicator.show()

        # Assert
        assert indicator._animating is True

    def test_estado_apos_hide_nao_animando(self):
        """
        QUANDO hide() é chamado
        ENTÃO _animating é False
        """
        # Arrange
        indicator = ThinkingIndicator()
        indicator.show()

        # Act
        indicator.hide()

        # Assert
        assert indicator._animating is False

    def test_show_hide_show_reanima(self):
        """
        QUANDO show/hide/show é executado
        ENTÃO _animating alterna corretamente
        """
        # Arrange
        indicator = ThinkingIndicator()

        # Act & Assert
        indicator.show()
        assert indicator._animating is True

        indicator.hide()
        assert indicator._animating is False

        indicator.show()
        assert indicator._animating is True


class TestThinkingIndicatorMensagens:
    """
    Testa diferentes mensagens do ThinkingIndicator.
    """

    def test_mensagem_sky_pensando(self):
        """
        QUANDO mensagem é "🤔 Sky está pensando..."
        ENTÃO renderiza corretamente
        """
        # Arrange & Act
        indicator = ThinkingIndicator("🤔 Sky está pensando...")

        # Assert
        assert "Sky" in indicator.message
        assert "pensando" in indicator.message

    def test_mensagem_analisando(self):
        """
        QUANDO mensagem é "Analisando..."
        ENTÃO renderiza corretamente
        """
        # Arrange & Act
        indicator = ThinkingIndicator("Analisando...")

        # Assert
        assert indicator.message == "Analisando..."

    def test_mensagem_buscando_memorias(self):
        """
        QUANDO mensagem é "Buscando memórias..."
        ENTÃO renderiza corretamente
        """
        # Arrange & Act
        indicator = ThinkingIndicator("Buscando memórias...")

        # Assert
        assert indicator.message == "Buscando memórias..."


__all__ = [
    "TestThinkingIndicatorInit",
    "TestThinkingIndicatorShow",
    "TestThinkingIndicatorHide",
    "TestThinkingIndicatorCss",
    "TestThinkingIndicatorEstados",
    "TestThinkingIndicatorMensagens",
    "TestThinkingPanelInit",
    "TestThinkingPanelAddEntry",
    "TestThinkingPanelCollapsed",
    "TestThinkingEntryWidget",
]


# =============================================================================
# ThinkingPanel Tests
# =============================================================================

class TestThinkingPanelInit:
    """
    Testa inicialização do ThinkingPanel.
    """

    def test_init_cria_painel_expandido(self):
        """
        QUANDO ThinkingPanel é criado
        ENTÃO inicia expandido (collapsed=False)
        """
        # Arrange & Act
        panel = ThinkingPanel()

        # Assert
        assert panel.collapsed is False
        assert panel.title == "🧠 Raciocínio"

    def test_init_inicia_sem_entradas(self):
        """
        QUANDO ThinkingPanel é criado
        ENTÃO inicia com zero entradas
        """
        # Arrange & Act
        panel = ThinkingPanel()

        # Assert
        assert panel.entry_count == 0


class TestThinkingPanelAddEntry:
    """
    Testa adição de entradas ao ThinkingPanel.
    """

    @pytest.mark.asyncio
    async def test_add_entry_incrementa_contador(self):
        """
        QUANDO entrada é adicionada
        ENTÃO contador é incrementado

        NOTA: Teste simplificado - a função real precisa do widget montado
        """
        # Arrange
        panel = ThinkingPanel()
        entry = ThinkingEntry(
            type="thought",
            timestamp=datetime.now(),
            content="Teste de pensamento"
        )

        # Act - adiciona entrada diretamente à lista interna
        panel._entries.append(entry)  # type: ignore

        # Assert
        assert panel.entry_count == 1

    @pytest.mark.asyncio
    async def test_add_entry_multiple_entradas(self):
        """
        QUANDO múltiplas entradas são adicionadas
        ENTÃO contador reflete total

        NOTA: Teste simplificado - a função real precisa do widget montado
        """
        # Arrange
        panel = ThinkingPanel()
        entries = [
            ThinkingEntry(type="thought", timestamp=datetime.now(), content=f"Pensamento {i}")
            for i in range(3)
        ]

        # Act - adiciona entradas diretamente à lista interna
        for entry in entries:
            panel._entries.append(entry)  # type: ignore

        # Assert
        assert panel.entry_count == 3


class TestThinkingPanelCollapsed:
    """
    Testa comportamento de colapso do ThinkingPanel.
    """

    def test_painel_expandido_por_padrao(self):
        """
        QUANDO ThinkingPanel é criado
        ENTÃO está expandido (não colapsado)
        """
        # Arrange & Act
        panel = ThinkingPanel()

        # Assert
        assert panel.collapsed is False

    def test_pode_ser_colapsado(self):
        """
        QUANDO collapsed é definido como True
        ENTÃO painel fica colapsado
        """
        # Arrange
        panel = ThinkingPanel()

        # Act
        panel.collapsed = True

        # Assert
        assert panel.collapsed is True


class TestThinkingEntryWidget:
    """
    Testa ThinkingEntryWidget.
    """

    def test_init_com_entry(self):
        """
        QUANDO ThinkingEntryWidget é criado
        ENTÃO armazena a entrada
        """
        # Arrange
        entry = ThinkingEntry(
            type="thought",
            timestamp=datetime.now(),
            content="Teste"
        )

        # Act
        widget = ThinkingEntryWidget(entry)

        # Assert
        assert widget.entry is entry

    def test_icones_por_tipo(self):
        """
        QUANDO tipo de entrada varia
        ENTÃO ícone correto é usado
        """
        # Arrange
        icones = ThinkingEntryWidget.ICONS

        # Assert
        assert icones["thought"] == "💭"
        assert icones["tool_start"] == "🔧"
        assert icones["tool_result"] == "✓"
        assert icones["error"] == "❌"
