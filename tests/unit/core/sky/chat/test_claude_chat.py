# coding: utf-8
"""
Testes do ClaudeChatAdapter.

DOC: openspec/changes/chat-claude-sdk/specs/claude-chat-integration/spec.md
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.core.sky.chat.claude_chat import (
    ClaudeChatAdapter,
)
from src.core.sky.chat import ChatMessage


class TestClaudeChatAdapterInit:
    """
    Testa inicialização do ClaudeChatAdapter.

    DOC: spec.md - Requirement: Fluxo de mensagens através do ClaudeChatAdapter
    """

    def test_init_com_persistent_memory(self):
        """
        DOC: spec.md - Cenário: Adapter recebe mensagem do usuário

        QUANDO adapter é criado com injeção de PersistentMemory
        ENTÃO memória é armazenada
        E histórico é inicializado vazio
        """
        # Arrange
        mock_memory = Mock()

        # Act
        adapter = ClaudeChatAdapter(memory=mock_memory)

        # Assert
        assert adapter._memory == mock_memory
        assert adapter._history == []

    def test_init_sem_argumentos_obrigatorios(self):
        """
        QUANDO adapter é criado sem argumentos
        ENTÃO usa get_memory() como padrão
        """
        # Act - não deve lançar exceção
        from src.core.sky.chat.claude_chat import ClaudeChatAdapter
        adapter = ClaudeChatAdapter()

        # Assert
        assert adapter._memory is not None
        assert adapter._history == []


class TestClaudeChatAdapterReceive:
    """
    Testa o método receive().

    DOC: spec.md - Requirement: Fluxo de mensagens através do ClaudeChatAdapter
    """

    def test_receive_armazena_historico(self):
        """
        DOC: spec.md - Cenário: Adapter recebe mensagem do usuário

        QUANDO usuário envia mensagem via ChatMessage
        ENTÃO mensagem é armazenada no histórico com timestamp
        E role é marcado como "user"
        """
        # Arrange
        adapter = ClaudeChatAdapter()
        message = ChatMessage(role="user", content="Olá Sky")

        # Act
        adapter.receive(message)

        # Assert
        assert len(adapter._history) == 1
        assert adapter._history[0].role == "user"
        assert adapter._history[0].content == "Olá Sky"
        assert adapter._history[0].timestamp is not None

    def test_receive_preserva_conteudo_exato(self):
        """
        DOC: spec.md - Cenário: Mensagem do usuário adicionada ao histórico

        QUANDO usuário envia mensagem
        ENTÃO conteúdo é preservado exatamente como enviado
        """
        # Arrange
        adapter = ClaudeChatAdapter()
        original_content = "Texto com caMinho Figo e !@#$%"

        # Act
        adapter.receive(ChatMessage(role="user", content=original_content))

        # Assert
        assert adapter._history[0].content == original_content


class TestClaudeChatAdapterRespond:
    """
    Testa o método respond().

    DOC: spec.md - Requirement: Fluxo de mensagens através do ClaudeChatAdapter

    NOTA: respond() é assíncrono desde a refatoração para Claude Agent SDK.
    """

    @pytest.mark.asyncio
    @patch('src.core.sky.chat.claude_chat.ClaudeChatAdapter._call_claude_sdk')
    @patch('src.core.sky.chat.claude_chat.ClaudeChatAdapter._retrieve_memory')
    async def test_respond_gera_resposta(self, mock_retrieve, mock_call_sdk):
        """
        DOC: spec.md - Cenário: Adapter gera resposta

        QUANDO respond(message) é chamado
        ENTÃO adapter recupera memória relevante via RAG
        E adapter constrói system prompt
        E adapter chama Claude Agent SDK
        E adapter retorna resposta gerada
        E adapter armazena resposta no histórico
        """
        # Arrange
        adapter = ClaudeChatAdapter()
        message = ChatMessage(role="user", content="Quem é você?")

        mock_retrieve.return_value = []  # Nenhuma memória
        mock_call_sdk.return_value = "Sou a Sky, uma assistente de IA."

        # Act
        response = await adapter.respond(message)

        # Assert
        assert response == "Sou a Sky, uma assistente de IA."
        assert len(adapter._history) == 2  # user + sky
        assert adapter._history[1].role == "sky"
        assert adapter._history[1].content == response

    @pytest.mark.asyncio
    @patch('src.core.sky.chat.claude_chat.ClaudeChatAdapter._call_claude_sdk')
    @patch('src.core.sky.chat.claude_chat.ClaudeChatAdapter._retrieve_memory')
    async def test_respond_sem_message_recebe_primeiro(self, mock_retrieve, mock_call_sdk):
        """
        QUANDO respond() é chamado sem mensagem
        ENTÃO usa última mensagem do histórico se disponível
        """
        # Arrange
        adapter = ClaudeChatAdapter()
        message = ChatMessage(role="user", content="Oi")
        adapter.receive(message)

        mock_retrieve.return_value = []
        mock_call_sdk.return_value = "Olá!"

        # Act
        response = await adapter.respond()

        # Assert
        assert response == "Olá!"

    @pytest.mark.asyncio
    async def test_respond_sem_historico_retorna_vazio(self):
        """
        QUANDO respond() é chamado sem mensagem e sem histórico
        ENTÃO retorna string vazia ou mensagem padrão
        """
        # Arrange
        adapter = ClaudeChatAdapter()

        # Act
        response = await adapter.respond()

        # Assert
        # Comportamento esperado: retorna string vazia ou mensagem de erro
        assert response == "" or "nenhuma mensagem" in response.lower()


class TestRetrieveMemory:
    """
    Testa o método _retrieve_memory().

    DOC: spec.md - Requirement: Integração de memória com contexto Claude
    """

    def test_retrieve_memory_chama_memory_search(self):
        """
        DOC: spec.md - Cenário: Memória recuperada e injetada

        QUANDO usuário faz uma pergunta
        ENTÃO sistema busca memória RAG com a query do usuário
        E top 5 memórias mais relevantes são recuperadas
        """
        # Arrange
        mock_memory = Mock()
        mock_memory.search.return_value = [
            {"content": "Sky é uma IA", "similarity": 0.9},
            {"content": "Sky foi criada pelo pai", "similarity": 0.85},
        ]
        adapter = ClaudeChatAdapter(memory=mock_memory)

        # Act
        results = adapter._retrieve_memory("Quem é você?")

        # Assert
        mock_memory.search.assert_called_once_with("Quem é você?", top_k=5)
        assert len(results) == 2
        assert results[0]["content"] == "Sky é uma IA"

    def test_retrieve_memory_retorna_vazio_se_nada_encontrado(self):
        """
        DOC: spec.md - Cenário: Nenhuma memória relevante encontrada

        QUANDO nenhuma memória atinge o threshold
        ENTÃO retorna lista vazia
        """
        # Arrange
        mock_memory = Mock()
        mock_memory.search.return_value = []
        adapter = ClaudeChatAdapter(memory=mock_memory)

        # Act
        results = adapter._retrieve_memory("Query aleatória")

        # Assert
        assert results == []


class TestFallbackParaLegacy:
    """
    Testa o fallback para SkyChat em caso de erro.

    DOC: spec.md - Requirement: Falha do SDK com fallback para legacy
    """

    @pytest.mark.asyncio
    @patch('core.sky.chat.SkyChat')
    async def test_fallback_para_sky_chat_em_erro(self, mock_sky_chat):
        """
        DOC: spec.md - Cenário: Falha do SDK com fallback para legacy

        QUANDO Claude Agent SDK falha (erro de API, timeout, etc.)
        ENTÃO sistema automaticamente volta para respostas legacy
        E erro é registrado para observabilidade
        """
        # Arrange
        mock_memory = Mock()
        adapter = ClaudeChatAdapter(memory=mock_memory)

        # Simular erro no SDK
        async def _mock_call_sdk_error(*args, **kwargs):
            raise Exception("API Error")

        # Mock do _retrieve_memory para não falhar
        mock_memory.search.return_value = []

        with patch.object(adapter, '_call_claude_sdk', side_effect=_mock_call_sdk_error):
            mock_legacy_chat = Mock()
            mock_legacy_chat.respond.return_value = "Resposta legacy"
            mock_sky_chat.return_value = mock_legacy_chat

            message = ChatMessage(role="user", content="Oi")

            # Act
            response = await adapter.respond(message)

            # Assert
            # Fallback deve retornar resposta do legacy
            assert response == "Resposta legacy"


class TestSessionContext:
    """
    Testa o contexto de sessão.

    DOC: openspec/changes/chat-claude-sdk/specs/chat-session-context/spec.md
    """

    def test_historico_mantido_durante_sessao(self):
        """
        DOC: spec.md - Cenário: Histórico de mensagens mantido durante sessão

        QUANDO múltiplas mensagens são trocadas
        ENTÃO histórico preserva todas as mensagens
        """
        # Arrange
        adapter = ClaudeChatAdapter()

        # Act
        adapter.receive(ChatMessage(role="user", content="Msg 1"))
        adapter.receive(ChatMessage(role="user", content="Msg 2"))
        adapter.receive(ChatMessage(role="user", content="Msg 3"))

        # Assert
        assert len(adapter._history) == 3
        assert adapter._history[0].content == "Msg 1"
        assert adapter._history[1].content == "Msg 2"
        assert adapter._history[2].content == "Msg 3"

    def test_limite_historico_20_mensagens(self):
        """
        DOC: spec.md - Cenário: Histórico limitado às últimas N mensagens

        QUANDO histórico excede 20 mensagens (10 turnos)
        ENTÃO mensagens mais antigas são mantidas no histórico
        E apenas últimas 20 mensagens são enviadas para Claude (no contexto)
        """
        # Arrange
        adapter = ClaudeChatAdapter()

        # Act - adicionar 25 mensagens
        for i in range(25):
            adapter.receive(ChatMessage(role="user", content=f"Msg {i}"))

        # Assert - histórico mantém todas as mensagens
        # mas o contexto para Claude deve ser limitado
        assert len(adapter._history) == 25

        # O contexto retornado por get_history_limitado deve ter no máximo 20
        # Nota: Este método será usado ao chamar Claude SDK
        contexto_limitado = adapter.get_history_limitado()
        assert len(contexto_limitado) <= 20
        # Deve ser as últimas 20 mensagens
        assert contexto_limitado[0].content == "Msg 5"  # 25 - 20 = 5 (primeira do contexto)
        assert contexto_limitado[-1].content == "Msg 24"  # última

    def test_clear_history_limpa_historico(self):
        """
        DOC: spec.md - Cenário: Comando /new limpa histórico

        QUANDO comando /new é executado (clear_history)
        ENTÃO histórico é completamente limpo
        E novo histórico pode ser construído
        """
        # Arrange
        adapter = ClaudeChatAdapter()
        adapter.receive(ChatMessage(role="user", content="Msg 1"))
        adapter.receive(ChatMessage(role="user", content="Msg 2"))
        adapter.receive(ChatMessage(role="user", content="Msg 3"))

        # Act
        adapter.clear_history()

        # Assert
        assert len(adapter._history) == 0
        assert adapter.get_history() == []

    def test_clear_history_permite_novas_mensagens(self):
        """
        QUANDO histórico é limpo e novas mensagens são adicionadas
        ENTÃO novo histórico é construído normalmente
        """
        # Arrange
        adapter = ClaudeChatAdapter()
        adapter.receive(ChatMessage(role="user", content="Antiga 1"))
        adapter.receive(ChatMessage(role="user", content="Antiga 2"))

        # Act
        adapter.clear_history()
        adapter.receive(ChatMessage(role="user", content="Nova 1"))
        adapter.receive(ChatMessage(role="user", content="Nova 2"))

        # Assert
        assert len(adapter._history) == 2
        assert adapter._history[0].content == "Nova 1"
        assert adapter._history[1].content == "Nova 2"
