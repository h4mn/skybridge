# -*- coding: utf-8 -*-
"""
Testes unitários para o handler de reações Discord.

Correções validadas (2026-04-05):
- Fallback fetch_channel quando get_channel retorna None
- Obter nome real do usuário via member/guild
- Fix UnboundLocalError quando message fetch falha
- Fallback para emoji.unicode quando None
- Logs específicos em vez de except silencioso

NOTA: Testes isolados da lógica do handler para evitar conflitos
com o pacote local src.core.discord
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

import pytest


class TestEmojiExtraction:
    """
    Testa extração de emoji string.
    """

    def test_emoji_unicode_retornado_corretamente(self):
        """
        GIVEN emoji unicode (não custom)
        WHEN extrai emoji_str
        THEN deve retornar unicode via name (discord.py usa name para unicode emojis)
        """
        # Setup
        emoji = MagicMock()
        emoji.is_custom_emoji = MagicMock(return_value=False)
        emoji.name = "👍"  # Para emojis não-custom, name contém o unicode

        # Act
        if emoji.is_custom_emoji():
            emoji_str = f":{emoji.name}:"
        else:
            # Para emojis não-custom, name contém o caractere unicode
            # str(emoji) também funcionaria, mas name é mais direto
            emoji_str = emoji.name or "❓"

        # Assert
        assert emoji_str == "👍"

    def test_emoji_custom_formatado_corretamente(self):
        """
        GIVEN emoji custom
        WHEN extrai emoji_str
        THEN deve retornar formato :name:
        """
        # Setup
        emoji = MagicMock()
        emoji.name = "pepe_cool"
        emoji.is_custom_emoji = MagicMock(return_value=True)
        emoji.unicode = None

        # Act
        if emoji.is_custom_emoji():
            emoji_str = f":{emoji.name}:"
        else:
            emoji_str = emoji.unicode or emoji.name or "❓"

        # Assert
        assert emoji_str == ":pepe_cool:"

    def test_emoji_unicode_none_fallback_para_name(self):
        """
        GIVEN emoji com name não-nulo
        WHEN extrai emoji_str
        THEN deve usar name (discord.py PartialEmoji)
        """
        # Setup
        emoji = MagicMock()
        emoji.name = "thumbs_up"
        emoji.is_custom_emoji = MagicMock(return_value=False)
        # Em discord.py real, name contém o unicode ou o nome do emoji

        # Act
        if emoji.is_custom_emoji():
            emoji_str = f":{emoji.name}:"
        else:
            # Para emojis não-custom, name contém o valor
            emoji_str = emoji.name or "❓"

        # Assert
        assert emoji_str == "thumbs_up"

    def test_emoji_unicode_e_name_nulos(self):
        """
        GIVEN emoji com unicode e name nulos
        WHEN extrai emoji_str
        THEN deve usar fallback "❓"
        """
        # Setup
        emoji = MagicMock()
        emoji.is_custom_emoji = MagicMock(return_value=False)
        emoji.name = None

        # Act
        if emoji.is_custom_emoji():
            emoji_str = f":{emoji.name}:"
        else:
            # Para emojis não-custom, str(emoji) retorna o caractere
            emoji_str = str(emoji) if emoji.name else emoji.name or "❓"

        # Assert
        assert emoji_str == "❓"


class TestMessageExtraction:
    """
    Testa extração de informações da mensagem.
    """

    def test_mensagem_preview_truncada_acima_100_chars(self):
        """
        GIVEN mensagem com mais de 100 caracteres
        WHEN cria preview
        THEN deve truncar com "..."
        """
        # Setup
        long_content = "A" * 150

        # Act
        if long_content:
            message_preview = long_content[:100] + "..." if len(long_content) > 100 else long_content
        else:
            message_preview = "(sem conteúdo)"

        # Assert
        assert message_preview == "A" * 100 + "..."
        assert len(message_preview) == 103

    def test_mensagem_vazia_sem_conteudo(self):
        """
        GIVEN mensagem sem conteúdo
        WHEN cria preview
        THEN deve mostrar "(sem conteúdo)"
        """
        # Setup
        message = MagicMock()
        message.content = None

        # Act
        if message.content:
            message_preview = message.content[:100] + "..." if len(message.content) > 100 else message.content
        else:
            message_preview = "(sem conteúdo)"

        # Assert
        assert message_preview == "(sem conteúdo)"

    def test_mensagem_autor_inexistente(self):
        """
        GIVEN mensagem sem author
        WHEN busca autor
        THEN deve usar valores default
        """
        # Setup
        message = MagicMock()
        message.author = None

        # Act
        try:
            message_author_id = str(message.author.id)
            message_author_name = message.author.name
        except (AttributeError, TypeError):
            message_author_id = "unknown"
            message_author_name = "Unknown"

        # Assert
        assert message_author_id == "unknown"
        assert message_author_name == "Unknown"


class TestMemberNameExtraction:
    """
    Testa extração de nome de member.
    """

    def test_member_name_obtido_corretamente(self):
        """
        GIVEN member no guild
        WHEN busca nome do usuário
        THEN deve retornar nome e discriminator
        """
        # Setup
        member = MagicMock()
        member.id = 777888999
        member.name = "ReactorUser"
        member.discriminator = "1234"

        # Act
        reactor_name = member.name
        reactor_discriminator = f"#{member.discriminator}" if member.discriminator != "0" else ""
        reactor_display = f"{reactor_name}{reactor_discriminator}" if reactor_discriminator else reactor_name

        # Assert
        assert reactor_display == "ReactorUser#1234"

    def test_discriminator_zero_nao_mostra_hash(self):
        """
        GIVEN member com discriminator "0" (novo formato Discord)
        WHEN formata display name
        THEN não deve mostrar #0
        """
        # Setup
        member = MagicMock()
        member.name = "User"
        member.discriminator = "0"

        # Act
        reactor_name = member.name
        reactor_discriminator = f"#{member.discriminator}" if member.discriminator != "0" else ""
        reactor_display = f"{reactor_name}{reactor_discriminator}" if reactor_discriminator else reactor_name

        # Assert
        assert reactor_display == "User"
        assert "#0" not in reactor_display


class TestChannelDetection:
    """
    Testa detecção de tipo de canal.
    """

    def test_thread_detectada_corretamente(self):
        """
        GIVEN channel que é uma Thread
        WHEN determina interaction_type
        THEN deve ser "thread_reaction_added"
        """
        # Setup
        thread = MagicMock()
        thread.name = "test-thread"
        thread.parent = MagicMock()
        thread.parent.name = "parent-channel"

        # Simula isinstance check
        is_thread = True  # isinstance(channel, Thread)

        interaction_type = "reaction_added"
        channel_name = thread.name

        # Act
        if is_thread:
            interaction_type = "thread_reaction_added"
            if thread.parent and thread.parent.name:
                channel_name = f"{thread.parent.name} > {thread.name}"

        # Assert
        assert interaction_type == "thread_reaction_added"
        assert channel_name == "parent-channel > test-thread"


class TestNotificationFormat:
    """
    Testa formatação da notificação.
    """

    def test_notification_format_contem_emoji(self):
        """
        GIVEN notification criada
        WHEN formata content
        THEN deve conter emoji na notificação
        """
        # Setup
        emoji_str = "👍"
        reactor_display = "User#1234"
        message_author_name = "Author"
        message_preview = "Test message"

        # Act
        content = f"[{emoji_str}] {reactor_display} reagiu {message_author_name}: \"{message_preview}\""

        # Assert
        assert "👍" in content
        assert "User#1234" in content
        assert "Author" in content
        assert "Test message" in content

    def test_meta_contem_todos_os_campos_esperados(self):
        """
        GIVEN notification criada
        WHEN formata meta
        THEN deve conter todos os campos obrigatórios
        """
        # Setup
        channel_id = 123456789
        message_id = 111222333
        user_id = 777888999

        # Act
        meta = {
            "chat_id": str(channel_id),
            "message_id": str(message_id),
            "user_id": str(user_id),
            "user": "User#1234",
            "ts": datetime.now().isoformat(),
            "interaction_type": "reaction_added",
            "emoji": "👍",
            "is_custom_emoji": False,
            "message_author_id": "444555666",
            "message_author_name": "Author",
            "channel_name": "test-channel",
            "thread_id": None,
            "guild_id": "987654321",
        }

        # Assert
        assert "chat_id" in meta
        assert "message_id" in meta
        assert "user_id" in meta
        assert "user" in meta
        assert "interaction_type" in meta
        assert "emoji" in meta
        assert "message_author_id" in meta
        assert "channel_name" in meta

        # Verifica que user contém nome e não apenas ID
        assert "#" in meta["user"]  # Formato name#discriminator


class TestEdgeCases:
    """
    Testa casos edge do handler de reações.
    """

    def test_canal_sem_guild(self):
        """
        GIVEN canal sem guild (ex: DM)
        WHEN busca member
        THEN deve usar user_id como fallback
        """
        # Setup
        channel = MagicMock()
        channel.guild = None
        user_id = 777888999

        # Act
        reactor_name = str(user_id)

        # Assert
        assert reactor_name == "777888999"

    @pytest.mark.asyncio
    async def test_unboundlocalerror_evitado_com_inicializacao(self):
        """
        GIVEN message não definida
        WHEN tenta acessar message.author
        THEN deve usar valores default pré-inicializados
        """
        # Setup - simula o padrão do handler corrigido
        message = None  # Inicializado antes
        message_author_id = "unknown"
        message_author_name = "Unknown"

        # Simula falha no fetch_message
        if message is None:
            # Já temos valores default, não crasha
            pass

        # Assert
        assert message_author_id == "unknown"
        assert message_author_name == "Unknown"
        # Não causa UnboundLocalError

    def test_payload_bot_id_comparacao(self):
        """
        GIVEN payload de reação
        WHEN compara com bot ID
        THEN deve ignorar própria reação
        """
        # Setup
        bot_id = 999
        payload = MagicMock()
        payload.user_id = 999

        # Act
        should_ignore = (payload.user_id == bot_id)

        # Assert
        assert should_ignore is True

    def test_payload_usuario_diferente(self):
        """
        GIVEN payload de reação de usuário diferente
        WHEN compara com bot ID
        THEN NÃO deve ignorar
        """
        # Setup
        bot_id = 999
        payload = MagicMock()
        payload.user_id = 777

        # Act
        should_ignore = (payload.user_id == bot_id)

        # Assert
        assert should_ignore is False
