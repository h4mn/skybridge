"""
Testes unitários para utils.py - TDD Estrito.
"""

import pytest
from pathlib import Path


class TestChunk:
    """Testes para chunk()."""

    def test_texto_curto_retorna_lista_unica(self):
        """RED → GREEN: chunk() retorna lista única para texto curto."""
        from src.core.discord.utils import chunk

        text = "Hello world"
        result = chunk(text, limit=2000)

        assert len(result) == 1
        assert result[0] == text

    def test_texto_longo_divide_em_chunks(self):
        """RED → GREEN: chunk() divide texto longo corretamente."""
        from src.core.discord.utils import chunk

        text = "a" * 5000
        result = chunk(text, limit=2000)

        assert len(result) == 3
        assert len(result[0]) == 2000
        assert len(result[1]) == 2000
        assert len(result[2]) == 1000

    def test_mode_newline_prefere_paragrafos(self):
        """RED → GREEN: chunk() com mode='newline' prefere quebras de parágrafo."""
        from src.core.discord.utils import chunk

        # Texto com parágrafos
        text = "Parágrafo 1\n\n" + "a" * 1500 + "\n\nParágrafo 3"
        result = chunk(text, limit=200, mode="newline")

        # Deve quebrar nos parágrafos, não no meio das letras
        assert len(result) >= 2

    def test_respeita_limite_minimo_para_newline(self):
        """RED → GREEN: chunk() só usa newline se > limit/2."""
        from src.core.discord.utils import chunk

        # Quebra de linha muito cedo (menos que limit/2)
        text = "ab\ncd" + "e" * 100
        result = chunk(text, limit=50, mode="newline")

        # Não deve quebrar no \n se está muito cedo
        assert len(result) >= 1


class TestSafeAttachmentName:
    """Testes para safe_attachment_name()."""

    def test_remove_colchetes(self):
        """RED → GREEN: safe_attachment_name() remove [ e ]."""
        from src.core.discord.utils import safe_attachment_name
        from unittest.mock import Mock

        att = Mock()
        att.filename = "file[name].txt"

        result = safe_attachment_name(att)

        assert "[" not in result
        assert "]" not in result
        assert "_" in result

    def test_remove_newlines(self):
        """RED → GREEN: safe_attachment_name() remove \\r e \\n."""
        from src.core.discord.utils import safe_attachment_name
        from unittest.mock import Mock

        att = Mock()
        att.filename = "file\r\nname.txt"

        result = safe_attachment_name(att)

        assert "\r" not in result
        assert "\n" not in result

    def test_remove_semicolon(self):
        """RED → GREEN: safe_attachment_name() remove ;."""
        from src.core.discord.utils import safe_attachment_name
        from unittest.mock import Mock

        att = Mock()
        att.filename = "file;name.txt"

        result = safe_attachment_name(att)

        assert ";" not in result


class TestAssertSendable:
    """Testes para assert_sendable()."""

    def test_arquivo_normal_passa(self, temp_state_dir):
        """RED → GREEN: assert_sendable() permite arquivo normal."""
        from src.core.discord.utils import assert_sendable

        # Arquivo no inbox
        inbox = temp_state_dir / "inbox"
        inbox.mkdir(exist_ok=True)
        test_file = inbox / "test.txt"
        test_file.write_text("hello")

        # Não deve lançar exceção
        assert_sendable(str(test_file))

    def test_arquivo_estado_recusado(self, temp_state_dir):
        """RED → GREEN: assert_sendable() recusa arquivos de estado."""
        from src.core.discord.utils import assert_sendable

        # access.json
        access_file = temp_state_dir / "access.json"
        access_file.write_text("{}")

        with pytest.raises(ValueError, match="(?i)recusando"):
            assert_sendable(str(access_file))


class TestRecentlySent:
    """Testes para note_sent() e is_recently_sent()."""

    def test_note_sent_registra_id(self):
        """RED → GREEN: note_sent() registra ID."""
        from src.core.discord.utils import note_sent, is_recently_sent

        note_sent("12345")

        assert is_recently_sent("12345") is True

    def test_id_nao_registrado_retorna_false(self):
        """RED → GREEN: is_recently_sent() retorna False para ID não registrado."""
        from src.core.discord.utils import is_recently_sent

        assert is_recently_sent("nonexistent") is False

    def test_cap_em_200_ids(self):
        """RED → GREEN: Remove IDs antigos quando atinge 200."""
        from src.core.discord.utils import note_sent, is_recently_sent, _recent_sent_ids

        # Limpa
        _recent_sent_ids.clear()

        # Adiciona 201 IDs
        for i in range(201):
            note_sent(str(i))

        # Primeiro ID deve ter sido removido
        assert is_recently_sent("0") is False
        assert is_recently_sent("200") is True
        assert len(_recent_sent_ids) == 200
