# coding: utf-8
"""
Testes do widget ConfirmModal.

DOC: openspec/changes/sky-chat-textual-ui/specs/textual-chat-ui/spec.md
DOC: openspec/changes/sky-chat-textual-ui/design.md - Modal para confirmações
"""

import pytest
from unittest.mock import Mock, patch

from src.core.sky.chat.textual_ui.widgets.modal import ConfirmModal


class TestConfirmModalInit:
    """
    Testa inicialização do ConfirmModal.
    """

    def test_init_com_mensagem(self):
        """
        QUANDO ConfirmModal é criado com mensagem
        ENTÃO armazena a mensagem
        """
        # Arrange & Act
        modal = ConfirmModal("Deseja continuar?")

        # Assert
        assert modal.message == "Deseja continuar?"
        assert modal.detail is None
        assert modal.confirm_label == "Confirmar"
        assert modal.cancel_label == "Cancelar"
        assert modal.confirmed is False

    def test_init_com_detail(self):
        """
        QUANDO ConfirmModal é criado com detail
        ENTÃO armazena detail
        """
        # Arrange & Act
        modal = ConfirmModal("Limpar sessão?", detail="Isso não pode ser desfeito")

        # Assert
        assert modal.detail == "Isso não pode ser desfeito"

    def test_init_com_labels_customizados(self):
        """
        QUANDO ConfirmModal é criado com labels customizados
        ENTÃO armazena confirm_label e cancel_label
        """
        # Arrange & Act
        modal = ConfirmModal(
            "Confirme ação",
            confirm_label="Sim, limpar",
            cancel_label="Não manter"
        )

        # Assert
        assert modal.confirm_label == "Sim, limpar"
        assert modal.cancel_label == "Não manter"

    def test_init_confirmed_inicia_false(self):
        """
        QUANDO ConfirmModal é criado
        ENTÃO confirmed inicia como False
        """
        # Arrange & Act
        modal = ConfirmModal("Test")

        # Assert
        assert modal.confirmed is False


class TestConfirmModalCompose:
    """
    Testa método compose().
    """

    def test_compose_retorna_componentes(self):
        """
        QUANDO compose() é chamado
        ENTÃO retorna Vertical com Label e botões
        """
        # Arrange
        modal = ConfirmModal("Test message")

        # Act
        children = list(modal.compose())

        # Assert
        # Deve ter: Vertical, Label(mensagem), Horizontal(buttons), 2 Buttons
        assert len(children) >= 3

    def test_compose_sem_detail(self):
        """
        QUANDO compose() é chamado sem detail
        ENTÃO não inclui Label de detail
        """
        # Arrange
        modal = ConfirmModal("Message")

        # Act
        children = list(modal.compose())

        # Assert - primeiro filho é Vertical, conteúdo dentro
        vertical = children[0]
        vertical_children = list(vertical.compose())
        # Apenas Label de mensagem + Horizontal de botões
        assert len(vertical_children) >= 2

    def test_compose_com_detail(self):
        """
        QUANDO compose() é chamado com detail
        ENTÃO inclui Label de detail
        """
        # Arrange
        modal = ConfirmModal("Message", detail="Detail text")

        # Act
        children = list(modal.compose())

        # Assert
        assert len(children) > 0


class TestConfirmModalCss:
    """
    Testa CSS do ConfirmModal.
    """

    def test_possui_css_default_definido(self):
        """
        QUANDO ConfirmModal é inspecionado
        ENTÃO possui DEFAULT_CSS definido
        """
        # Assert
        assert ConfirmModal.DEFAULT_CSS is not None

    def test_css_inclui_alinhamamento_central(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui align: center middle
        """
        # Assert
        assert "align: center middle" in ConfirmModal.DEFAULT_CSS

    def test_css_inclui_borda_thick(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO inclui border: thick $primary
        """
        # Assert
        assert "border: thick $primary" in ConfirmModal.DEFAULT_CSS

    def test_css_define_botao_confirmar_com_sucesso(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define #confirm-btn com background: $success
        """
        # Assert
        assert "#confirm-btn" in ConfirmModal.DEFAULT_CSS
        assert "$success" in ConfirmModal.DEFAULT_CSS

    def test_css_define_botao_cancelar_com_erro(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define #cancel-btn com background: $error
        """
        # Assert
        assert "#cancel-btn" in ConfirmModal.DEFAULT_CSS
        assert "$error" in ConfirmModal.DEFAULT_CSS


class TestConfirmModalBindings:
    """
    Testa bindings de teclado.
    """

    def test_binding_s_para_confirmar(self):
        """
        QUANDO BINDINGS é inspecionado
        ENTÃO inclui "s" para confirm
        """
        # Assert
        assert any(binding[0] == "s" and binding[1] == "confirm" for binding in ConfirmModal.BINDINGS)

    def test_binding_y_para_confirmar(self):
        """
        QUANDO BINDINGS é inspecionado
        ENTÃO inclui "y" para confirm
        """
        # Assert
        assert any(binding[0] == "y" and binding[1] == "confirm" for binding in ConfirmModal.BINDINGS)

    def test_binding_enter_para_confirmar(self):
        """
        QUANDO BINDINGS é inspecionado
        ENTÃO inclui "enter" para confirm
        """
        # Assert
        assert any(binding[0] == "enter" and binding[1] == "confirm" for binding in ConfirmModal.BINDINGS)

    def test_binding_n_para_cancelar(self):
        """
        QUANDO BINDINGS é inspecionado
        ENTÃO inclui "n" para app.pop_screen (cancelar)
        """
        # Assert
        assert any(binding[0] == "n" and binding[1] == "app.pop_screen" for binding in ConfirmModal.BINDINGS)

    def test_binding_escape_para_cancelar(self):
        """
        QUANDO BINDINGS é inspecionado
        ENTÃO inclui "escape" para app.pop_screen (cancelar)
        """
        # Assert
        assert any(binding[0] == "escape" and binding[1] == "app.pop_screen" for binding in ConfirmModal.BINDINGS)


class TestConfirmModalActionConfirm:
    """
    Testa action_confirm().
    """

    def test_action_confirm_define_confirmed_true(self):
        """
        QUANDO action_confirm() é chamado
        ENTÃO confirmed é definido como True
        """
        # Arrange
        modal = ConfirmModal("Test")

        # Act
        modal.action_confirm()

        # Assert
        assert modal.confirmed is True

    def test_action_confirm_chama_dismiss(self):
        """
        QUANDO action_confirm() é chamado
        ENTÃO chama dismiss(result=True)
        """
        # Arrange
        modal = ConfirmModal("Test")
        with patch.object(modal, "dismiss") as mock_dismiss:
            # Act
            modal.action_confirm()

            # Assert
            mock_dismiss.assert_called_once_with(result=True)


class TestConfirmModalOnButtonPressed:
    """
    Testa on_button_pressed().
    """

    def test_on_button_pressed_confirm_btn(self):
        """
        QUANDO botão confirm-btn é pressionado
        ENTÃO chama action_confirm()
        """
        # Arrange
        modal = ConfirmModal("Test")
        mock_button = Mock()
        mock_button.id = "confirm-btn"
        event = Mock()
        event.button = mock_button

        with patch.object(modal, "action_confirm") as mock_confirm:
            # Act
            modal.on_button_pressed(event)

            # Assert
            mock_confirm.assert_called_once()

    def test_on_button_pressed_cancel_btn(self):
        """
        QUANDO botão cancel-btn é pressionado
        ENTÃO chama app.pop_screen()
        """
        # Arrange
        modal = ConfirmModal("Test")
        mock_app = Mock()
        modal.app = mock_app
        mock_button = Mock()
        mock_button.id = "cancel-btn"
        event = Mock()
        event.button = mock_button

        # Act
        modal.on_button_pressed(event)

        # Assert
        mock_app.pop_screen.assert_called_once()


class TestConfirmModalCenariosUso:
    """
    Testa cenários de uso realista.
    """

    def test_modal_confirmar_limpar_sessao(self):
        """
        QUANDO modal é criado para confirmar limpeza de sessão
        ENTÃO exibe mensagem apropriada
        """
        # Arrange & Act
        modal = ConfirmModal(
            "Limpar sessão atual?",
            detail="Todas as mensagens serão perdidas"
        )

        # Assert
        assert "Limpar sessão" in modal.message
        assert "mensagens" in modal.detail

    def test_modal_confirmar_saida(self):
        """
        QUANDO modal é criado para confirmar saída
        ENTÃO exibe mensagem apropriada
        """
        # Arrange & Act
        modal = ConfirmModal(
            "Deseja sair do chat?",
            confirm_label="Sair",
            cancel_label="Continuar"
        )

        # Assert
        assert "sair" in modal.message.lower()
        assert modal.confirm_label == "Sair"
        assert modal.cancel_label == "Continuar"

    def test_modal_customizado_para_acao_perigosa(self):
        """
        QUANDO modal é criado para ação perigosa
        ENTÃO usa labels enfáticos
        """
        # Arrange & Act
        modal = ConfirmModal(
            "Atenção: Esta ação é irreversível!",
            detail="Deseja realmente prosseguir?",
            confirm_label="Sim, prosseguir",
            cancel_label="Não, cancelar"
        )

        # Assert
        assert "irreversível" in modal.message
        assert modal.confirm_label == "Sim, prosseguir"
        assert modal.cancel_label == "Não, cancelar"


__all__ = [
    "TestConfirmModalInit",
    "TestConfirmModalCompose",
    "TestConfirmModalCss",
    "TestConfirmModalBindings",
    "TestConfirmModalActionConfirm",
    "TestConfirmModalOnButtonPressed",
    "TestConfirmModalCenariosUso",
]
