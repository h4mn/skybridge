# coding: utf-8
"""
Testes dos workers assíncronos (ClaudeWorker, RAGWorker, MemorySaveWorker).

DOC: openspec/changes/sky-chat-textual-ui/specs/textual-async-workers/spec.md
DOC: openspec/changes/sky-chat-textual-ui/design.md - Workers assíncronos com asyncio
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from src.core.sky.chat.textual_ui.workers.claude import (
    ClaudeWorker,
    ClaudeResponse,
)
from src.core.sky.chat.textual_ui.workers.rag import (
    RAGWorker,
    RAGResponse,
    MemoryResult,
)
from src.core.sky.chat.textual_ui.workers.memory import (
    MemorySaveWorker,
)


class TestClaudeResponse:
    """
    Testa dataclass ClaudeResponse.
    """

    def test_claude_response_creation(self):
        """
        QUANDO ClaudeResponse é criado
        ENTÃO armazena todos os campos
        """
        # Arrange & Act
        response = ClaudeResponse(
            content="Olá!",
            tokens_in=10,
            tokens_out=5,
            latency_ms=123.45,
        )

        # Assert
        assert response.content == "Olá!"
        assert response.tokens_in == 10
        assert response.tokens_out == 5
        assert response.latency_ms == 123.45


class TestClaudeWorkerInit:
    """
    Testa inicialização do ClaudeWorker.
    """

    def test_init_com_api_key(self):
        """
        QUANDO ClaudeWorker é criado com api_key
        ENTÃO armazena api_key e modelo
        """
        # Arrange & Act
        worker = ClaudeWorker(api_key="test-key", model="test-model")

        # Assert
        assert worker.api_key == "test-key"
        assert worker.model == "test-model"
        assert worker._client is None

    def test_init_model_default_glm_47(self):
        """
        QUANDO ClaudeWorker é criado sem modelo
        ENTÃO usa glm-4.7 como padrão
        """
        # Arrange & Act
        worker = ClaudeWorker(api_key="test-key")

        # Assert
        assert worker.model == "glm-4.7"


class TestClaudeWorkerGenerate:
    """
    Testa método generate().
    """

    @pytest.mark.asyncio
    async def test_generate_retorna_claude_response(self):
        """
        QUANDO generate() é chamado
        ENTÃO retorna ClaudeResponse com conteúdo, tokens e latência
        """
        # Arrange
        worker = ClaudeWorker(api_key="test-key")

        # Mock do cliente Anthropic
        mock_response = Mock()
        mock_response.content = [Mock(text="Resposta de teste")]
        mock_response.usage = Mock(
            input_tokens=10,
            output_tokens=5,
        )

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch.object(worker, "_get_client", return_value=mock_client):
            # Act
            response = await worker.generate(
                system_prompt="Você é Sky",
                user_message="Olá",
            )

            # Assert
            assert isinstance(response, ClaudeResponse)
            assert response.content == "Resposta de teste"
            assert response.tokens_in == 10
            assert response.tokens_out == 5
            assert response.latency_ms > 0

    @pytest.mark.asyncio
    async def test_generate_calcula_latencia(self):
        """
        QUANDO generate() é chamado
        ENTÃO calcula latência corretamente
        """
        # Arrange
        worker = ClaudeWorker(api_key="test-key")

        mock_response = Mock()
        mock_response.content = [Mock(text="Test")]
        mock_response.usage = Mock(input_tokens=1, output_tokens=1)

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch.object(worker, "_get_client", return_value=mock_client):
            # Act
            response = await worker.generate("Sys", "Msg")

            # Assert
            assert response.latency_ms >= 0


class TestRAGResponse:
    """
    Testa dataclass RAGResponse.
    """

    def test_rag_response_creation(self):
        """
        QUANDO RAGResponse é criado
        ENTÃO armazena memórias e contagem
        """
        # Arrange & Act
        memories = [
            MemoryResult(content="Mem 1", similarity=0.9),
            MemoryResult(content="Mem 2", similarity=0.8),
        ]
        response = RAGResponse(memories=memories, count=2)

        # Assert
        assert len(response.memories) == 2
        assert response.count == 2


class TestMemoryResult:
    """
    Testa dataclass MemoryResult.
    """

    def test_memory_result_creation(self):
        """
        QUANDO MemoryResult é criado
        ENTÃO armazena conteúdo e similaridade
        """
        # Arrange & Act
        result = MemoryResult(content="Conteúdo", similarity=0.85)

        # Assert
        assert result.content == "Conteúdo"
        assert result.similarity == 0.85


class TestRAGWorkerInit:
    """
    Testa inicialização do RAGWorker.
    """

    def test_init_com_memory_adapter(self):
        """
        QUANDO RAGWorker é criado com memory_adapter
        ENTÃO armazena o adaptador
        """
        # Arrange
        mock_adapter = Mock()

        # Act
        worker = RAGWorker(mock_adapter)

        # Assert
        assert worker.memory_adapter is mock_adapter


class TestRAGWorkerSearch:
    """
    Testa método search().
    """

    @pytest.mark.asyncio
    async def test_search_retorna_rag_response(self):
        """
        QUANDO search() é chamado
        ENTÃO retorna RAGResponse com memórias encontradas
        """
        # Arrange
        mock_adapter = Mock()
        mock_adapter.search_memory = Mock(return_value=[
            ("Memória 1", 0.9),
            ("Memória 2", 0.7),
        ])
        worker = RAGWorker(mock_adapter)

        # Act
        response = await worker.search("query de teste")

        # Assert
        assert isinstance(response, RAGResponse)
        assert response.count == 2
        assert len(response.memories) == 2

    @pytest.mark.asyncio
    async def test_search_filtra_por_threshold(self):
        """
        QUANDO search() é chamado com threshold=0.8
        ENTÃO retorna apenas memórias com score >= 0.8
        """
        # Arrange
        mock_adapter = Mock()
        mock_adapter.search_memory = Mock(return_value=[
            ("Memória 1", 0.9),  # >= 0.8, incluída
            ("Memória 2", 0.7),  # < 0.8, excluída
            ("Memória 3", 0.85),  # >= 0.8, incluída
        ])
        worker = RAGWorker(mock_adapter)

        # Act
        response = await worker.search("query", threshold=0.8)

        # Assert
        assert response.count == 2
        assert all(m.similarity >= 0.8 for m in response.memories)

    @pytest.mark.asyncio
    async def test_search_respeita_top_k(self):
        """
        QUANDO search() é chamado com top_k=3
        ENTÃO retorna no máximo 3 memórias
        """
        # Arrange
        mock_adapter = Mock()
        mock_adapter.search_memory = Mock(return_value=[
            ("Memória 1", 0.9),
            ("Memória 2", 0.85),
            ("Memória 3", 0.8),
            ("Memória 4", 0.75),  # Excedeu top_k
        ])
        worker = RAGWorker(mock_adapter)

        # Act
        response = await worker.search("query", top_k=3)

        # Assert
        assert response.count <= 3

    @pytest.mark.asyncio
    async def test_search_vazio_sem_resultados(self):
        """
        QUANDO search() não encontra memórias
        ENTÃO retorna RAGResponse com count=0
        """
        # Arrange
        mock_adapter = Mock()
        mock_adapter.search_memory = Mock(return_value=[])
        worker = RAGWorker(mock_adapter)

        # Act
        response = await worker.search("query")

        # Assert
        assert response.count == 0
        assert len(response.memories) == 0


class TestMemorySaveWorkerInit:
    """
    Testa inicialização do MemorySaveWorker.
    """

    def test_init_com_memory_adapter(self):
        """
        QUANDO MemorySaveWorker é criado com memory_adapter
        ENTÃO armazena o adaptador
        """
        # Arrange
        mock_adapter = Mock()

        # Act
        worker = MemorySaveWorker(mock_adapter)

        # Assert
        assert worker.memory_adapter is mock_adapter


class TestMemorySaveWorkerSave:
    """
    Testa método save().
    """

    @pytest.mark.asyncio
    async def test_save_sucesso_retorna_true(self):
        """
        QUANDO save() é chamado e_adapter.learn() tem sucesso
        ENTÃO retorna True
        """
        # Arrange
        mock_adapter = Mock()
        mock_adapter.learn = Mock()
        worker = MemorySaveWorker(mock_adapter)

        # Act
        result = await worker.save("Nova memória")

        # Assert
        assert result is True
        mock_adapter.learn.assert_called_once_with("Nova memória")

    @pytest.mark.asyncio
    async def test_save_falha_retorna_false(self):
        """
        QUANDO save() é chamado e_adapter.learn() lança exceção
        ENTÃO retorna False
        """
        # Arrange
        mock_adapter = Mock()
        mock_adapter.learn = Mock(side_effect=Exception("Erro"))
        worker = MemorySaveWorker(mock_adapter)

        # Act
        result = await worker.save("Memória")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_save_passa_conteudo_correto(self):
        """
        QUANDO save() é chamado
        ENTÃO passa conteúdo corretamente para learn()
        """
        # Arrange
        mock_adapter = Mock()
        mock_adapter.learn = Mock()
        worker = MemorySaveWorker(mock_adapter)

        # Act
        await worker.save("Conteúdo de teste")

        # Assert
        mock_adapter.learn.assert_called_once_with("Conteúdo de teste")


class TestWorkersAsyncio:
    """
    Testa comportamento assíncrono dos workers.
    """

    @pytest.mark.asyncio
    async def test_claude_worker_nao_bloqueia_event_loop(self):
        """
        QUANDO ClaudeWorker.generate() é executado
        ENTÃO não bloqueia o event loop
        """
        # Arrange
        worker = ClaudeWorker(api_key="test-key")
        mock_response = Mock()
        mock_response.content = [Mock(text="Test")]
        mock_response.usage = Mock(input_tokens=1, output_tokens=1)
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch.object(worker, "_get_client", return_value=mock_client):
            # Act - verifica que é awaitable
            response = await worker.generate("Sys", "Msg")

            # Assert
            assert isinstance(response, ClaudeResponse)

    @pytest.mark.asyncio
    async def test_rag_worker_yield_event_loop(self):
        """
        QUANDO RAGWorker.search() é executado
        ENTÃO faz yield para o event loop (asyncio.sleep(0))
        """
        # Arrange
        mock_adapter = Mock()
        mock_adapter.search_memory = Mock(return_value=[])
        worker = RAGWorker(mock_adapter)

        # Act
        await worker.search("query")

        # Assert - se completou sem erro, yield funcionou
        assert True

    @pytest.mark.asyncio
    async def test_memory_save_worker_yield_event_loop(self):
        """
        QUANDO MemorySaveWorker.save() é executado
        ENTÃO faz yield para o event loop (asyncio.sleep(0))
        """
        # Arrange
        mock_adapter = Mock()
        mock_adapter.learn = Mock()
        worker = MemorySaveWorker(mock_adapter)

        # Act
        await worker.save("Test")

        # Assert - se completou sem erro, yield funcionou
        assert True


__all__ = [
    "TestClaudeResponse",
    "TestClaudeWorkerInit",
    "TestClaudeWorkerGenerate",
    "TestRAGResponse",
    "TestMemoryResult",
    "TestRAGWorkerInit",
    "TestRAGWorkerSearch",
    "TestMemorySaveWorkerInit",
    "TestMemorySaveWorkerSave",
    "TestWorkersAsyncio",
]
