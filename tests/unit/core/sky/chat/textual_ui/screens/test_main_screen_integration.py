# coding: utf-8
"""
Testes de integração do MainScreen com ChatLog 2.0.

Valida que o MainScreen pode ser montado com o novo ChatLog
e que o LogToolbar está presente e funcionando.
"""

import pytest
from textual.app import App

from core.sky.chat.textual_ui.screens.main import MainScreen


class ChatLogTestApp(App):
    """App de teste para validação do MainScreen com ChatLog 2.0."""

    def on_mount(self) -> None:
        self.push_screen(MainScreen(input=""))


@pytest.mark.asyncio
class TestMainScreenChatLog2Integration:
    """Testes de integração do MainScreen com ChatLog 2.0."""

    async def test_mainscreen_mounta_com_chatlog_2_0(self):
        """MainScreen monta sem erros com o novo ChatLog 2.0."""
        async with ChatLogTestApp().run_test() as pilot:
            # App está rodando
            assert pilot.app is not None

    async def test_mainscreen_tem_chatlog_widget(self):
        """MainScreen tem o widget ChatLog 2.0 montado."""
        async with ChatLogTestApp().run_test() as pilot:
            from core.sky.log import ChatLog

            screen = pilot.app.screen
            chatlog = screen.query_one("#chatlog", ChatLog)
            assert chatlog is not None

    async def test_mainscreen_tem_logtoolbar(self):
        """MainScreen tem o widget LogToolbar montado."""
        async with ChatLogTestApp().run_test() as pilot:
            from core.sky.log.widgets.toolbar import LogToolbar

            screen = pilot.app.screen
            toolbar = screen.query_one(LogToolbar)
            assert toolbar is not None

    async def test_mainscreen_log_chatlogger_funciona(self):
        """ChatLogger funciona com o novo ChatLog 2.0."""
        async with ChatLogTestApp().run_test() as pilot:
            from core.sky.log import ChatLog

            screen = pilot.app.screen
            chatlog = screen.query_one("#chatlog", ChatLog)

            # ChatLogger está inicializado no MainScreen
            assert hasattr(screen, '_chat_logger')
            assert screen._chat_logger is not None

            # Escrever um log via ChatLogger funciona
            screen._chat_logger.info("Teste de integração")
            await pilot.pause()

            # Verifica que o entry foi adicionado
            assert len(chatlog._entries) > 0
