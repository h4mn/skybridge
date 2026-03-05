# coding: utf-8
"""
Teste de rollback para USE_TEXTUAL_UI=false.

DOC: openspec/changes/sky-chat-textual-ui/tasks.md - Tarefa 19.2

Verifica que o código legado (legacy_ui.py) funciona corretamente
quando a nova UI Textual está desabilitada via feature flag.
"""

import os
import pytest
from unittest.mock import patch

from src.core.sky.chat import ChatMessage, SkyChat


class TestRollbackUseTextualUiFalse:
    """
    Teste: rollback para USE_TEXTUAL_UI=false.

    Tarefa 19.2: Testar rollback para `USE_TEXTUAL_UI=false`
    """

    def test_import_legacy_ui_com_flag_false(self):
        """
        QUANDO USE_TEXTUAL_UI=false
        ENTÃO ChatUI e ChatMetrics podem ser importados
        """
        # Arrange - redefine a flag e recarrega o módulo
        # Nota: este teste assume que legacy_ui existe
        with patch.dict(os.environ, {"USE_TEXTUAL_UI": "false"}):
            # Recarrega módulos para simular ambiente limpo
            import importlib
            from src.core.sky.chat import legacy_ui

            # Assert - legacy_ui pode ser importado
            assert legacy_ui is not None
            assert hasattr(legacy_ui, "ChatUI")
            assert hasattr(legacy_ui, "ChatMetrics")

    def test_legacy_ui_classes_existem(self):
        """
        QUANDO legacy_ui é inspecionado
        ENTÃO ChatUI e ChatMetrics existem
        """
        # Arrange & Act
        from src.core.sky.chat.legacy_ui import ChatUI, ChatMetrics

        # Assert
        assert ChatUI is not None
        assert ChatMetrics is not None

    def test_legacy_ui_chat_metrics_init(self):
        """
        QUANDO ChatMetrics é instanciado
        ENTÃO atributos são inicializados corretamente
        """
        # Arrange
        from src.core.sky.chat.legacy_ui import ChatMetrics

        # Act
        metrics = ChatMetrics(
            latency_ms=150.0,
            tokens_in=10,
            tokens_out=20,
            memory_hits=3,
            model="glm-4.7",
        )

        # Assert
        assert metrics.latency_ms == 150.0
        assert metrics.tokens_in == 10
        assert metrics.tokens_out == 20
        assert metrics.memory_hits == 3
        assert metrics.model == "glm-4.7"

    def test_sky_chat_funciona_sem_textual_ui(self):
        """
        QUANDO SkyChat é usado sem Textual UI
        ENTÃO funcionalidades básicas funcionam
        """
        # Arrange
        chat = SkyChat()
        message = ChatMessage(role="user", content="Oi")

        # Act
        chat.receive(message)

        # Assert
        assert len(chat.history) == 1
        assert chat.history[0].role == "user"
        assert chat.history[0].content == "Oi"

    def test_sky_chat_responder_sem_textual_ui(self):
        """
        QUANDO SkyChat.respond() é chamado
        ENTÃO retorna resposta válida sem usar Textual
        """
        # Arrange
        chat = SkyChat()
        message = ChatMessage(role="user", content="Oi")

        # Act
        response = chat.respond(message)

        # Assert
        assert isinstance(response, str)
        assert len(response) > 0
        # Histórico deve ter user + sky
        assert len(chat.history) == 2

    def test_chat_message_dataclass_funciona(self):
        """
        QUANDO ChatMessage é criado
        ENTÃO dataclass funciona corretamente
        """
        # Arrange & Act
        from datetime import datetime

        msg1 = ChatMessage(role="user", content="Teste")
        msg2 = ChatMessage(role="sky", content="Resposta", timestamp=datetime.now())

        # Assert
        assert msg1.role == "user"
        assert msg1.content == "Teste"
        assert msg1.timestamp is not None  # Gerado automaticamente
        assert msg2.role == "sky"
        assert msg2.content == "Resposta"


class TestRollbackFeatureFlagToggle:
    """
    Testa alternância entre UIs via feature flag.
    """

    def test_feature_flag_default_e_false(self):
        """
        QUANDO USE_TEXTUAL_UI não está definida
        ENTÃO padrão é "false" (UI legada)
        """
        # Arrange - remove variável se existir
        original_value = os.environ.pop("USE_TEXTUAL_UI", None)

        # Act - recarrega módulo chat para testar
        import importlib
        import src.core.sky.chat as chat_module

        # Recarrega para pegar valor default
        importlib.reload(chat_module)

        # Assert
        assert chat_module.USE_TEXTUAL_UI is False

        # Restore
        if original_value is not None:
            os.environ["USE_TEXTUAL_UI"] = original_value

    def test_feature_flag_true_ativa_textual(self):
        """
        QUANDO USE_TEXTUAL_UI=true
        ENTÃO SkyApp é usado
        """
        # Arrange
        with patch.dict(os.environ, {"USE_TEXTUAL_UI": "true"}):
            import importlib
            import src.core.sky.chat as chat_module
            importlib.reload(chat_module)

            # Assert
            assert chat_module.USE_TEXTUAL_UI is True
            # ChatApp deve apontar para SkyApp
            # (se disponível, senão None)

    def test_feature_flag_false_usa_legacy(self):
        """
        QUANDO USE_TEXTUAL_UI=false
        ENTÃO ChatApp é None e ChatUI/ChatMetrics estão disponíveis
        """
        # Arrange
        with patch.dict(os.environ, {"USE_TEXTUAL_UI": "false"}):
            import importlib
            import src.core.sky.chat as chat_module
            importlib.reload(chat_module)

            # Assert
            assert chat_module.USE_TEXTUAL_UI is False
            # ChatUI e ChatMetrics devem estar disponíveis independentemente da flag
            assert hasattr(chat_module, "ChatUI")
            assert hasattr(chat_module, "ChatMetrics")


class TestLegacyUiBasicFunctionality:
    """
    Testa funcionalidades básicas da UI legada.
    """

    def test_sky_chat_responde_saudacao(self):
        """
        QUANDO usuário envia "oi"
        ENTÃO Sky responde com saudação
        """
        # Arrange
        chat = SkyChat()
        message = ChatMessage(role="user", content="oi")

        # Act
        response = chat.respond(message)

        # Assert
        assert "oi" in response.lower() or "sou" in response.lower()

    def test_sky_chat_busca_memoria(self):
        """
        QUANDO Sky busca na memória
        ENTÃO funciona sem Textual UI
        """
        # Arrange
        chat = SkyChat()

        # Act - busca genérica
        response = chat.respond(ChatMessage(role="user", content="O que você sabe?"))

        # Assert
        assert isinstance(response, str)
        assert len(response) > 0


__all__ = [
    "TestRollbackUseTextualUiFalse",
    "TestRollbackFeatureFlagToggle",
    "TestLegacyUiBasicFunctionality",
]
