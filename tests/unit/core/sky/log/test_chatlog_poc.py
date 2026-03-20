# coding: utf-8
"""
Testes Textual para ChatLog 2.0 POC.

Usa app.run_test() do Textual para testar sem abrir terminal.
"""

import pytest

from core.sky.log.poc import ChatLogPOC
from core.sky.log.chatlog import ChatLog
from core.sky.log.widgets.filter import LogFilter
from core.sky.log.widgets.search import LogSearch
from core.sky.log.widgets.close import LogClose
from core.sky.log.widgets.copier import LogCopier


@pytest.mark.asyncio
class TestChatLogPOC:
    """Testes da app ChatLogPOC."""

    async def test_app_mounta_sem_erros(self):
        """App monta sem erros."""
        async with ChatLogPOC().run_test() as pilot:
            # App está rodando
            assert pilot.app is not None
            assert pilot.app.title == "ChatLog 2.0 - POC"

    async def test_chatlog_aceita_logs_via_write_log(self):
        """ChatLog aceita logs via write_log."""
        async with ChatLogPOC().run_test() as pilot:
            await pilot.pause()

            chatlog = pilot.app.query_one("#chatlog", ChatLog)

            # Escreve um log diretamente
            from core.sky.log.entry import LogEntry
            import logging
            from datetime import datetime

            chatlog.write_log(
                LogEntry(
                    level=logging.INFO,
                    message="Teste de integração",
                    timestamp=datetime.now(),
                    scope="test"
                )
            )

            await pilot.pause()

            # Deve ter pelo menos 1 entry
            assert len(chatlog._entries) > 0

    async def test_filtro_info_mostra_apenas_info_ou_maior(self):
        """Filtro INFO mostra apenas logs INFO ou maior."""
        async with ChatLogPOC().run_test() as pilot:
            await pilot.pause()

            chatlog = pilot.app.query_one("#chatlog", ChatLog)

            # Adiciona logs de diferentes níveis
            from core.sky.log.entry import LogEntry
            import logging
            from datetime import datetime

            chatlog.write_log(LogEntry(level=logging.DEBUG, message="debug", timestamp=datetime.now(), scope="test"))
            chatlog.write_log(LogEntry(level=logging.INFO, message="info", timestamp=datetime.now(), scope="test"))
            chatlog.write_log(LogEntry(level=logging.ERROR, message="error", timestamp=datetime.now(), scope="test"))

            await pilot.pause()

            total_antes = len(chatlog._get_visible_entries())

            # Clica no botão INFO (level-20)
            await pilot.click("#level-20")
            await pilot.pause()

            # Deve ter menos entries visíveis (INFO+ apenas, sem DEBUG)
            total_depois = len(chatlog._get_visible_entries())
            assert total_depois < total_antes
            # DEBUG não deve aparecer
            visiveis = chatlog._get_visible_entries()
            assert not any(e.message == "debug" for e in visiveis)

    async def test_busca_filtra_entries(self):
        """Busca filtra entries por termo."""
        async with ChatLogPOC().run_test() as pilot:
            await pilot.pause()

            chatlog = pilot.app.query_one("#chatlog", ChatLog)

            # Adiciona logs para buscar
            from core.sky.log.entry import LogEntry
            import logging
            from datetime import datetime

            chatlog.write_log(LogEntry(level=logging.INFO, message="API request", timestamp=datetime.now(), scope="test"))
            chatlog.write_log(LogEntry(level=logging.INFO, message="Database query", timestamp=datetime.now(), scope="test"))
            await pilot.pause()

            # Digita no search
            await pilot.click("#search-input")
            await pilot.press("a", "p", "i")  # digita "api"
            await pilot.pause(delay=0.5)

            # Deve ter apenas entries com "api" (case insensitive)
            visiveis = chatlog._get_visible_entries()
            assert all("api" in e.message.lower() for e in visiveis)

    async def test_botao_x_limpa_filtro(self):
        """Botão X limpa filtros e busca."""
        async with ChatLogPOC().run_test() as pilot:
            await pilot.pause()

            chatlog = pilot.app.query_one("#chatlog", ChatLog)

            # Aplica filtro ERROR (level-40)
            await pilot.click("#level-40")
            await pilot.pause()
            assert chatlog._min_level == 40  # ERROR

            # Verifica se o botão X existe
            from core.sky.log.widgets.close import LogClose
            close_btn = pilot.app.query_one(LogClose)
            print(f"[TEST] Botão X encontrado: {close_btn}, label={close_btn.label}")

            # Tenta clicar diretamente no widget
            close_btn.on_press()
            await pilot.pause()

            # Filtro deve estar limpo
            print(f"[TEST] Após on_press, _min_level={chatlog._min_level}")
            assert chatlog._min_level == 0  # NOTSET
            assert chatlog._search_term == ""

    async def test_tecla_escape_limpa_tudo(self):
        """ESC limpa filtros e busca."""
        async with ChatLogPOC().run_test() as pilot:
            await pilot.pause()

            chatlog = pilot.app.query_one("#chatlog", ChatLog)

            # Aplica filtro WARNING (level-30)
            await pilot.click("#level-30")

            # Digita no search
            await pilot.click("#search-input")
            await pilot.press("t", "i", "m", "e", "o", "u", "t")
            await pilot.pause(delay=0.5)

            assert chatlog._min_level == 30  # WARNING aplicado
            assert chatlog._search_term == "timeout"

            # Pressiona ESC
            await pilot.press("escape")
            await pilot.pause()

            # Tudo limpo
            assert chatlog._min_level == 0
            assert chatlog._search_term == ""

    async def test_botao_copia_entries_visiveis(self):
        """Botão Copia entries visíveis para clipboard."""
        async with ChatLogPOC().run_test() as pilot:
            await pilot.pause()

            # Mock clipboard
            from unittest.mock import patch
            with patch("core.sky.log.clipboard.copy_to_clipboard", return_value=True) as mock_copy:
                await pilot.click("#copy-button")
                await pilot.pause()

                # Foi chamado com texto não vazio
                mock_copy.assert_called_once()
                texto_copiado = mock_copy.call_args[0][0]
                assert len(texto_copiado) > 0
                assert "INFO" in texto_copiado or "DEBUG" in texto_copiado

    async def test_logclose_muda_para_r_com_filtro(self):
        """LogClose mostra 'R' quando há filtro ativo."""
        async with ChatLogPOC().run_test() as pilot:
            await pilot.pause()

            close_btn = pilot.app.query_one(LogClose)

            # Sem filtro = X
            assert close_btn.label == "X"

            # Com filtro ERROR = R
            await pilot.click("#level-40")
            await pilot.pause()

            assert close_btn.label == "R"

            # Limpar filtro volta para X
            await pilot.click("#close-button")
            await pilot.pause()

            assert close_btn.label == "X"

    async def test_search_indica_matches(self):
        """Search mostra indicador de matches."""
        async with ChatLogPOC().run_test() as pilot:
            await pilot.pause()

            # Adiciona logs para buscar
            from core.sky.log.entry import LogEntry
            import logging
            from datetime import datetime

            chatlog = pilot.app.query_one("#chatlog", ChatLog)
            chatlog.write_log(LogEntry(level=logging.INFO, message="API request 1", timestamp=datetime.now(), scope="test"))
            chatlog.write_log(LogEntry(level=logging.INFO, message="API request 2", timestamp=datetime.now(), scope="test"))
            chatlog.write_log(LogEntry(level=logging.INFO, message="Database query", timestamp=datetime.now(), scope="test"))
            await pilot.pause()

            search = pilot.app.query_one(LogSearch)

            # Busca algo que existe
            await pilot.click("#search-input")
            await pilot.press("a", "p", "i")
            await pilot.pause(delay=0.5)

            # Deve ter indicado matches
            assert search._match_count > 0

    async def test_logclose_muda_para_r_com_busca(self):
        """LogClose mostra 'R' quando há busca ativa."""
        async with ChatLogPOC().run_test() as pilot:
            await pilot.pause()

            close_btn = pilot.app.query_one(LogClose)

            # Sem busca = X
            assert close_btn.label == "X"

            # Com busca = R
            await pilot.click("#search-input")
            await pilot.press("t", "e", "s", "t")
            await pilot.pause(delay=0.5)

            assert close_btn.label == "R"
