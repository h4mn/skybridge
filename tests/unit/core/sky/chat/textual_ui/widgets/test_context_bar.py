# coding: utf-8
"""
Testes do widget ContextBar.

DOC: openspec/changes/sky-chat-textual-ui/specs/textual-chat-ui/spec.md
DOC: openspec/changes/sky-chat-textual-ui/design.md - Barra de contexto com cores dinâmicas
"""

import pytest

from src.core.sky.chat.textual_ui.widgets.context_bar import ContextBar


class TestContextBarInit:
    """
    Testa inicialização do ContextBar.
    """

    def test_init_com_total_default(self):
        """
        QUANDO ContextBar é criado sem parâmetros
        ENTÃO usa total=20 (janela de contexto padrão)
        """
        # Arrange & Act
        bar = ContextBar()

        # Assert
        assert bar.total == 20
        assert bar.progress == 0

    def test_init_com_total_customizado(self):
        """
        QUANDO ContextBar é criado com total customizado
        ENTÃO usa total fornecido
        """
        # Arrange & Act
        bar = ContextBar(total=50)

        # Assert
        assert bar.total == 50

    def test_init_inicia_com_zero_progresso(self):
        """
        QUANDO ContextBar é criado
        ENTÃO progresso inicia em 0
        """
        # Arrange & Act
        bar = ContextBar()

        # Assert
        assert bar.progress == 0


class TestContextBarUpdateProgress:
    """
    Testa atualização de progresso e cores.
    """

    def test_update_progress_zero_porcento_classe_green(self):
        """
        QUANDO update_progress(0) é chamado (0%)
        ENTÃO aplica classe --green
        """
        # Arrange
        bar = ContextBar(total=20)

        # Act
        bar.update_progress(0)

        # Assert
        assert bar.has_class("--green")
        assert not bar.has_class("--yellow")
        assert not bar.has_class("--orange")
        assert not bar.has_class("--red")

    def test_update_progress_verde_ate_50_porcento(self):
        """
        QUANDO update_progress(10) é chamado com total=20 (50%)
        ENTÃO aplica classe --green
        """
        # Arrange
        bar = ContextBar(total=20)

        # Act
        bar.update_progress(10)

        # Assert
        assert bar.progress == 10
        assert bar.has_class("--green")

    def test_update_progress_amarelo_51_75_porcento(self):
        """
        QUANDO update_progress(13) é chamado com total=20 (65%)
        ENTÃO aplica classe --yellow
        """
        # Arrange
        bar = ContextBar(total=20)

        # Act
        bar.update_progress(13)

        # Assert
        assert bar.progress == 13
        assert bar.has_class("--yellow")
        assert not bar.has_class("--green")

    def test_update_progress_laranja_76_90_porcento(self):
        """
        QUANDO update_progress(17) é chamado com total=20 (85%)
        ENTÃO aplica classe --orange
        """
        # Arrange
        bar = ContextBar(total=20)

        # Act
        bar.update_progress(17)

        # Assert
        assert bar.progress == 17
        assert bar.has_class("--orange")
        assert not bar.has_class("--yellow")

    def test_update_progress_vermelho_acima_90_porcento(self):
        """
        QUANDO update_progress(19) é chamado com total=20 (95%)
        ENTÃO aplica classe --red
        """
        # Arrange
        bar = ContextBar(total=20)

        # Act
        bar.update_progress(19)

        # Assert
        assert bar.progress == 19
        assert bar.has_class("--red")
        assert not bar.has_class("--orange")

    def test_update_progress_100_porcento_classe_red(self):
        """
        QUANDO update_progress(20) é chamado com total=20 (100%)
        ENTÃO aplica classe --red
        """
        # Arrange
        bar = ContextBar(total=20)

        # Act
        bar.update_progress(20)

        # Assert
        assert bar.progress == 20
        assert bar.has_class("--red")

    def test_update_progress_remove_classes_antigas(self):
        """
        QUANDO update_progress muda de faixa
        ENTÃO remove classes de cor antigas
        """
        # Arrange
        bar = ContextBar(total=20)
        bar.update_progress(5)  # green
        assert bar.has_class("--green")

        # Act - muda para yellow
        bar.update_progress(15)

        # Assert
        assert not bar.has_class("--green")
        assert bar.has_class("--yellow")

    def test_update_progress_total_zero(self):
        """
        QUANDO total=0
        ENTÃO não gera divisão por zero
        """
        # Arrange & Act
        bar = ContextBar(total=0)
        bar.update_progress(0)

        # Assert - não deve lançar exceção
        assert bar.progress == 0


class TestContextBarLimites:
    """
    Testa limites de borda das faixas de porcentagem.
    """

    def test_borda_50_porcento_exato_classe_green(self):
        """
        QUANDO progresso é exatamente 50%
        ENTÃO classe é --green
        """
        # Arrange
        bar = ContextBar(total=20)

        # Act
        bar.update_progress(10)  # exato 50%

        # Assert
        assert bar.has_class("--green")

    def test_borda_51_porcento_classe_yellow(self):
        """
        QUANDO progresso é 51%
        ENTÃO classe é --yellow
        """
        # Arrange
        bar = ContextBar(total=100)

        # Act
        bar.update_progress(51)

        # Assert
        assert bar.has_class("--yellow")

    def test_borda_75_porcento_exato_classe_yellow(self):
        """
        QUANDO progresso é exatamente 75%
        ENTÃO classe é --yellow
        """
        # Arrange
        bar = ContextBar(total=100)

        # Act
        bar.update_progress(75)

        # Assert
        assert bar.has_class("--yellow")

    def test_borda_76_porcento_classe_orange(self):
        """
        QUANDO progresso é 76%
        ENTÃO classe é --orange
        """
        # Arrange
        bar = ContextBar(total=100)

        # Act
        bar.update_progress(76)

        # Assert
        assert bar.has_class("--orange")

    def test_borda_90_porcento_exato_classe_orange(self):
        """
        QUANDO progresso é exatamente 90%
        ENTÃO classe é --orange
        """
        # Arrange
        bar = ContextBar(total=100)

        # Act
        bar.update_progress(90)

        # Assert
        assert bar.has_class("--orange")

    def test_borda_91_porcento_classe_red(self):
        """
        QUANDO progresso é 91%
        ENTÃO classe é --red
        """
        # Arrange
        bar = ContextBar(total=100)

        # Act
        bar.update_progress(91)

        # Assert
        assert bar.has_class("--red")


class TestContextBarCss:
    """
    Testa CSS do ContextBar.
    """

    def test_possui_css_default_definido(self):
        """
        QUANDO ContextBar é inspecionado
        ENTÃO possui DEFAULT_CSS definido
        """
        # Assert
        assert ContextBar.DEFAULT_CSS is not None

    def test_css_define_classe_green(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define classe .--green com $success
        """
        # Assert
        assert "ContextBar.--green" in ContextBar.DEFAULT_CSS
        assert "$success" in ContextBar.DEFAULT_CSS

    def test_css_define_classe_yellow(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define classe .--yellow com $warning
        """
        # Assert
        assert "ContextBar.--yellow" in ContextBar.DEFAULT_CSS
        assert "$warning" in ContextBar.DEFAULT_CSS

    def test_css_define_classe_orange(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define classe .--orange com orange
        """
        # Assert
        assert "ContextBar.--orange" in ContextBar.DEFAULT_CSS
        assert "orange" in ContextBar.DEFAULT_CSS.lower()

    def test_css_define_classe_red(self):
        """
        QUANDO DEFAULT_CSS é inspecionado
        ENTÃO define classe .--red com red
        """
        # Assert
        assert "ContextBar.--red" in ContextBar.DEFAULT_CSS
        assert "red" in ContextBar.DEFAULT_CSS.lower()


class TestContextBarCenariosUso:
    """
    Testa cenários de uso realista.
    """

    def test_contexto_fresco_5_mensagens(self):
        """
        QUANDO 5 de 20 mensagens foram usadas (25%)
        ENTÃO exibe verde (contexto fresco)
        """
        # Arrange
        bar = ContextBar(total=20)

        # Act
        bar.update_progress(5)

        # Assert
        assert bar.has_class("--green")

    def test_contexto_moderado_12_mensagens(self):
        """
        QUANDO 12 de 20 mensagens foram usadas (60%)
        ENTÃO exibe amarelo (contexto moderado)
        """
        # Arrange
        bar = ContextBar(total=20)

        # Act
        bar.update_progress(12)

        # Assert
        assert bar.has_class("--yellow")

    def test_contexto_quente_16_mensagens(self):
        """
        QUANDO 16 de 20 mensagens foram usadas (80%)
        ENTÃO exibe laranja (contexto quente)
        """
        # Arrange
        bar = ContextBar(total=20)

        # Act
        bar.update_progress(16)

        # Assert
        assert bar.has_class("--orange")

    def test_contexto_critico_19_mensagens(self):
        """
        QUANDO 19 de 20 mensagens foram usadas (95%)
        ENTÃO exibe vermelho (contexto crítico)
        """
        # Arrange
        bar = ContextBar(total=20)

        # Act
        bar.update_progress(19)

        # Assert
        assert bar.has_class("--red")


__all__ = [
    "TestContextBarInit",
    "TestContextBarUpdateProgress",
    "TestContextBarLimites",
    "TestContextBarCss",
    "TestContextBarCenariosUso",
]
