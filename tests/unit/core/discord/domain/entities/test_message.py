# -*- coding: utf-8 -*-
"""
Testes unitários para Message Entity.

DOC: openspec/changes/discord-ddd-migration/specs/discord-domain/spec.md
- Message é Aggregate Root
- Message tem deadline de edição de 24h
- Message pode ter reações e anexos
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.core.discord.domain.entities import Message, Attachment, Reaction, MessageEditError
from src.core.discord.domain.value_objects import ChannelId, MessageId, UserId, MessageContent


class TestMessage:
    """
    Testa Message Aggregate Root.

    Especificação: Domain Layer - Entities
    """

    @pytest.fixture
    def message(self):
        """Cria mensagem padrão para testes."""
        return Message.create(
            message_id="123456789",
            channel_id="987654321",
            author_id="111111111",
            content="Mensagem de teste",
        )

    def test_create_factory_method_cria_mensagem_valida(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Criação via factory method

        WHEN Message.create() é chamado com dados válidos
        THEN SHALL retornar Message com VOs corretos
        """
        message = Message.create(
            message_id="123456789",
            channel_id="987654321",
            author_id="111111111",
            content="Mensagem de teste",
        )

        # Assert - VOs criados
        assert isinstance(message.id, MessageId)
        assert isinstance(message.channel_id, ChannelId)
        assert isinstance(message.author_id, UserId)
        assert isinstance(message.content, MessageContent)

        # Assert - valores
        assert str(message.id) == "123456789"
        assert str(message.channel_id) == "987654321"
        assert str(message.author_id) == "111111111"
        assert str(message.content) == "Mensagem de teste"

    def test_create_mensagem_marca_timestamp(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Timestamp de criação

        WHEN Message é criada
        THEN SHALL created_at ser datetime recente
        """
        before = datetime.now()
        message = Message.create("123", "456", "789", "Teste")
        after = datetime.now()

        assert before <= message.created_at <= after

    def test_edit_conteudo_nas_primeiras_24h(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Edição dentro do prazo

        WHEN message.edit() é chamado nas primeiras 24h
        THEN SHALL atualizar conteúdo e edited_at
        """
        message = Message.create("123", "456", "789", "Original")

        # Act - edita conteúdo
        new_content = MessageContent("Editado")
        message.edit(new_content)

        # Assert
        assert str(message.content) == "Editado"
        assert message.edited_at is not None
        assert message.is_edited() is True

    def test_edit_apos_24h_lanca_excecao(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Edição após prazo

        WHEN message.edit() é chamado após 24h
        THEN SHALL lançar MessageEditError
        """
        # Cria mensagem com 25h de idade
        old_timestamp = datetime.now() - timedelta(hours=25)
        message = Message(
            id=MessageId("123"),
            channel_id=ChannelId("456"),
            author_id=UserId("789"),
            content=MessageContent("Velha"),
            created_at=old_timestamp,
        )

        # Act & Assert - edição expirada
        with pytest.raises(MessageEditError, match="expirou"):
            message.edit(MessageContent("Tentativa falha"))

    def test_edit_conteudo_vazio_lanca_excecao(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Edição com conteúdo vazio

        WHEN MessageContent é vazio
        THEN SHALL MessageContent lançar ValueError
        """
        message = Message.create("123", "456", "789", "Original")

        with pytest.raises(ValueError):
            message.edit(MessageContent(""))  # Vazio

    def test_add_reaction_incrementa_count_se_existir(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Reação duplicada

        WHEN add_reaction() é chamado com emoji já existente
        THEN SHALL incrementar count
        """
        message = Message.create("123", "456", "789", "Teste")

        # Act - primeira reação
        message.add_reaction("👍")
        assert len(message.reactions) == 1
        assert message.reactions[0].count == 1

        # Act - mesma reação novamente
        message.add_reaction("👍")
        assert len(message.reactions) == 1
        assert message.reactions[0].count == 2

    def test_add_reaction_nova_cria_entry(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Nova reação

        WHEN add_reaction() é chamado com emoji novo
        THEN SHALL criar nova Reaction
        """
        message = Message.create("123", "456", "789", "Teste")

        message.add_reaction("👍")
        message.add_reaction("❤️")

        assert len(message.reactions) == 2
        assert message.reactions[0].emoji == "👍"
        assert message.reactions[1].emoji == "❤️"

    def test_has_attachment_retorna_true_com_anexos(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Verificação de anexos

        WHEN message tem attachments
        THEN SHALL has_attachment() retornar True
        """
        message = Message.create("123", "456", "789", "Teste")
        message.attachments.append(
            Attachment(
                id="att1",
                filename="imagem.png",
                content_type="image/png",
                size_bytes=1024,
                url="http://example.com/imagem.png",
            )
        )

        assert message.has_attachment() is True

    def test_has_attachment_retorna_false_sem_anexos(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Mensagem sem anexos

        WHEN message não tem attachments
        THEN SHALL has_attachment() retornar False
        """
        message = Message.create("123", "456", "789", "Teste")

        assert message.has_attachment() is False

    def test_age_hours_retorna_idade_em_horas(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Idade da mensagem

        WHEN age_hours() é chamado
        THEN SHALL retornar horas desde criação
        """
        message = Message.create("123", "456", "789", "Teste")

        # Mensagem recém-criada
        assert message.age_hours() < 1  # Menos de 1 hora


class TestAttachment:
    """
    Testa Attachment Value Object.

    Especificação: Domain Layer - Entities (Attachment)
    """

    def test_size_kb_converte_bytes_para_kb(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Conversão de tamanho

        WHEN attachment.size_kb() é chamado
        THEN SHALL retornar tamanho em KB
        """
        attachment = Attachment(
            id="att1",
            filename="arquivo.pdf",
            content_type="application/pdf",
            size_bytes=2048,
            url="http://example.com/arquivo.pdf",
        )

        assert attachment.size_kb() == 2  # 2048 bytes = 2 KB

    def test_is_image_retorna_true_para_imagem(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Detecção de imagem

        WHEN attachment content_type começa com "image/"
        THEN SHALL is_image() retornar True
        """
        attachment = Attachment(
            id="att1",
            filename="foto.png",
            content_type="image/png",
            size_bytes=1024,
            url="http://example.com/foto.png",
        )

        assert attachment.is_image() is True

    def test_is_image_retorna_false_para_nao_imagem(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Não é imagem

        WHEN attachment content_type não é "image/"
        THEN SHALL is_image() retornar False
        """
        attachment = Attachment(
            id="att1",
            filename="arquivo.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            url="http://example.com/arquivo.pdf",
        )

        assert attachment.is_image() is False

    def test_is_image_retorna_false_sem_content_type(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Content type None

        WHEN attachment content_type é None
        THEN SHALL is_image() retornar False
        """
        attachment = Attachment(
            id="att1",
            filename="desconhecido",
            content_type=None,
            size_bytes=1024,
            url="http://example.com/desconhecido",
        )

        assert attachment.is_image() is False


class TestReaction:
    """
    Testa Reaction Value Object.

    Especificação: Domain Layer - Entities (Reaction)
    """

    def test_reaction_criada_com_count_1(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Criação de reação

        WHEN Reaction é criada
        THEN SHALL count ser 1 (padrão)
        """
        reaction = Reaction(emoji="👍")

        assert reaction.emoji == "👍"
        assert reaction.count == 1

    def test_reaction_count_pode_ser_incrementado(self):
        """
        DOC: specs/discord-domain/spec.md
        Scenario: Incremento de count

        WHEN reaction.count é modificado
        THEN SHALL refletir novo valor
        """
        reaction = Reaction(emoji="👍", count=1)
        reaction.count += 1

        assert reaction.count == 2
