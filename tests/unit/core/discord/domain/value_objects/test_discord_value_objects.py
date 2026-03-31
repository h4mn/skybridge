# -*- coding: utf-8 -*-
"""
Testes unitários para Discord Value Objects.

DOC: openspec/changes/discord-ddd-migration/specs/discord-domain/spec.md
- ChannelId: ID numérico de canal
- MessageId: ID numérico de mensagem
- UserId: ID numérico de usuário
- MessageContent: conteúdo com validação e chunking
- AccessPolicy: política de acesso
"""

from __future__ import annotations

import pytest

from src.core.discord.domain.value_objects import (
    ChannelId,
    MessageId,
    UserId,
    MessageContent,
    MessageTooLongError,
)


class TestChannelId:
    """Testa ChannelId Value Object."""

    def test_create_channel_id_valido(self):
        """WHEN criado com ID numérico válido, THEN SHALL criar instância."""
        channel_id = ChannelId("123456789")
        assert str(channel_id) == "123456789"

    def test_create_channel_id_vazio_lanca_excecao(self):
        """WHEN criado com string vazia, THEN SHALL lançar ValueError."""
        with pytest.raises(ValueError, match="não pode ser vazio"):
            ChannelId("")

    def test_create_channel_id_nao_numerico_lanca_excecao(self):
        """WHEN criado com ID não numérico, THEN SHALL lançar ValueError."""
        with pytest.raises(ValueError, match="inválido.*numérico"):
            ChannelId("abc123")

    def test_from_int_cria_a_partir_de_inteiro(self):
        """WHEN from_int() é chamado, THEN SHALL converter int para str."""
        channel_id = ChannelId.from_int(123456789)
        assert str(channel_id) == "123456789"

    def test_to_int_converte_para_inteiro(self):
        """WHEN to_int() é chamado, THEN SHALL converter str para int."""
        channel_id = ChannelId("123456789")
        assert channel_id.to_int() == 123456789


class TestMessageId:
    """Testa MessageId Value Object."""

    def test_create_message_id_valido(self):
        """WHEN criado com ID numérico válido, THEN SHALL criar instância."""
        message_id = MessageId("987654321")
        assert str(message_id) == "987654321"

    def test_create_message_id_vazio_lanca_excecao(self):
        """WHEN criado com string vazia, THEN SHALL lançar ValueError."""
        with pytest.raises(ValueError, match="não pode ser vazio"):
            MessageId("")

    def test_create_message_id_nao_numerico_lanca_excecao(self):
        """WHEN criado com ID não numérico, THEN SHALL lançar ValueError."""
        with pytest.raises(ValueError, match="inválido.*numérico"):
            MessageId("xyz789")

    def test_from_int_cria_a_partir_de_inteiro(self):
        """WHEN from_int() é chamado, THEN SHALL converter int para str."""
        message_id = MessageId.from_int(987654321)
        assert str(message_id) == "987654321"

    def test_to_int_converte_para_inteiro(self):
        """WHEN to_int() é chamado, THEN SHALL converter str para int."""
        message_id = MessageId("987654321")
        assert message_id.to_int() == 987654321


class TestUserId:
    """Testa UserId Value Object."""

    def test_create_user_id_valido(self):
        """WHEN criado com ID numérico válido, THEN SHALL criar instância."""
        user_id = UserId("111111111")
        assert str(user_id) == "111111111"

    def test_create_user_id_vazio_lanca_excecao(self):
        """WHEN criado com string vazia, THEN SHALL lançar ValueError."""
        with pytest.raises(ValueError, match="não pode ser vazio"):
            UserId("")

    def test_create_user_id_nao_numerico_lanca_excecao(self):
        """WHEN criado com ID não numérico, THEN SHALL lançar ValueError."""
        with pytest.raises(ValueError, match="inválido.*numérico"):
            UserId("user123")

    def test_from_int_cria_a_partir_de_inteiro(self):
        """WHEN from_int() é chamado, THEN SHALL converter int para str."""
        user_id = UserId.from_int(111111111)
        assert str(user_id) == "111111111"

    def test_to_int_converte_para_inteiro(self):
        """WHEN to_int() é chamado, THEN SHALL converter str para int."""
        user_id = UserId("111111111")
        assert user_id.to_int() == 111111111


class TestMessageContent:
    """Testa MessageContent Value Object."""

    def test_create_conteudo_valido(self):
        """WHEN criado com conteúdo válido, THEN SHALL criar instância."""
        content = MessageContent("Mensagem de teste")
        assert str(content) == "Mensagem de teste"
        assert len(content) == 17

    def test_create_conteudo_vazio_lanca_excecao(self):
        """WHEN criado com conteúdo vazio, THEN SHALL lançar ValueError."""
        with pytest.raises(ValueError, match="não pode ser vazio"):
            MessageContent("")

    def test_create_conteudo_apenas_espacos_lanca_excecao(self):
        """WHEN criado com apenas espaços, THEN SHALL lançar ValueError."""
        with pytest.raises(ValueError, match="não pode ser vazio"):
            MessageContent("   ")

    def test_create_conteudo_muito_longo_lanca_excecao(self):
        """WHEN conteúdo excede 20000 caracteres, THEN SHALL lançar MessageTooLongError."""
        longo = "x" * 20001
        with pytest.raises(MessageTooLongError, match="excede limite máximo"):
            MessageContent(longo)

    def test_needs_chunking_retorna_true_conteudo_longo(self):
        """WHEN conteúdo tem > 2000 caracteres, THEN SHALL precisar de chunking."""
        longo = "x" * 2001
        content = MessageContent(longo)
        assert content.needs_chunking() is True

    def test_needs_chunking_retorna_false_conteudo_curto(self):
        """WHEN conteúdo tem ≤ 2000 caracteres, THEN SHALL não precisar de chunking."""
        curto = "x" * 1000
        content = MessageContent(curto)
        assert content.needs_chunking() is False

    def test_chunk_conteudo_curto_retorna_mesma_instancia(self):
        """WHEN chunk() é chamado em conteúdo curto, THEN SHALL retornar [self]."""
        curto = "x" * 1000
        content = MessageContent(curto)
        chunks = content.chunk()
        assert len(chunks) == 1
        assert chunks[0] is content

    def test_chunk_conteudo_longo_divide_em_partes(self):
        """WHEN chunk() é chamado em conteúdo longo, THEN SHALL dividir corretamente."""
        longo = "x" * 2001
        content = MessageContent(longo)
        chunks = content.chunk()
        assert len(chunks) == 2
        assert len(chunks[0]) == 2000
        assert len(chunks[1]) == 1

    def test_from_text_factory_method(self):
        """WHEN from_text() é chamado, THEN SHALL criar MessageContent."""
        content = MessageContent.from_text("Teste")
        assert str(content) == "Teste"
