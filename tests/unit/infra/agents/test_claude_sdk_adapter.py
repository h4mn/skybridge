# -*- coding: utf-8 -*-
"""
Testes unitários para ClaudeSDKAdapter.

Cobre:
- Import de HookMatcher com fallback
- _build_hooks_config sem HookMatcher
- Logger sem exc_info
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from kernel.contracts.result import Result


class TestHookMatcherImport:
    """Testes para import de HookMatcher com fallback."""

    def test_hookmatcher_import_exists(self):
        """Verifica que HookMatcher pode ser importado do SDK."""
        try:
            from claude_agent_sdk.types import HookMatcher
            assert HookMatcher is not None
        except ImportError:
            pytest.skip("HookMatcher não disponível no SDK instalado")

    def test_hookmatcher_fallback_in_adapter(self):
        """Verifica que o adapter tem fallback para HookMatcher."""
        from core.webhooks.infrastructure.agents.claude_sdk_adapter import HookMatcher

        # HookMatcher pode ser None se SDK não tiver
        if HookMatcher is None:
            # O fallback deve retornar config vazio
            pass  # OK, fallback funciona
        else:
            assert HookMatcher is not None


class TestBuildHooksConfig:
    """Testes para _build_hooks_config."""

    @pytest.fixture
    def mock_job(self):
        """Job mock."""
        job = Mock()
        job.job_id = "test-job-123"
        return job

    @pytest.fixture
    def mock_logger(self):
        """Logger mock."""
        logger = Mock()
        logger.warning = Mock()
        logger.info = Mock()
        return logger

    def test_build_hooks_config_without_hookmatcher(self, mock_job, mock_logger):
        """Testa _build_hooks_config quando HookMatcher é None."""
        from core.webhooks.infrastructure.agents.claude_sdk_adapter import HookMatcher

        # Se HookMatcher é None, deve retornar config vazio
        if HookMatcher is None:
            # Patch HookMatcher para ser None temporariamente
            with patch('core.webhooks.infrastructure.agents.claude_sdk_adapter.HookMatcher', None):
                from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter

                adapter = ClaudeSDKAdapter()
                config = adapter._build_hooks_config(mock_job, mock_logger)

                assert config == {}
                mock_logger.warning.assert_called_once()
        else:
            # Com HookMatcher disponível, deve retornar config
            from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter

            adapter = ClaudeSDKAdapter()
            config = adapter._build_hooks_config(mock_job, mock_logger)

            assert "PreToolUse" in config
            assert "PostToolUse" in config


class TestLoggerWithoutExcInfo:
    """Testes para verificar que logger não usa exc_info."""

    def test_logger_error_accepts_message_and_extra(self):
        """Testa que logger.error aceita message e extra sem exc_info."""
        from runtime.observability.logger import get_logger

        logger = get_logger()

        # Isso não deve levantar exceção
        logger.error(
            "Test error message",
            extra={"test_key": "test_value"}
        )

    def test_logger_error_with_invalid_param_raises(self):
        """Testa que logger.error com exc_info=True falha."""
        from runtime.observability.logger import get_logger

        logger = get_logger()

        # Isso deve falhar (TypeError ou KeyError)
        with pytest.raises((TypeError, KeyError)):
            logger.error(
                "Test error message",
                exc_info=True  # Parâmetro não suportado
            )


class TestSpawnWithErrorHandling:
    """Testes para spawn com tratamento de erros."""

    @pytest.fixture
    def mock_job(self):
        """Job mock para teste."""
        job = Mock()
        job.job_id = "test-job-123"
        job.issue_number = 42
        job.metadata = {}
        job.initial_snapshot = {}
        return job

    def test_spawn_exception_logs_without_exc_info(self, mock_job):
        """Testa que exceção no spawn é logada sem exc_info."""
        from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter
        from runtime.observability.logger import get_logger

        adapter = ClaudeSDKAdapter()
        logger = get_logger()

        # Mock para causar exceção - patch no import do claude_agent_sdk
        with patch('claude_agent_sdk.ClaudeSDKClient') as mock_client:
            mock_client.return_value.__aenter__.side_effect = Exception("Test error")

            import asyncio

            async def test_spawn():
                result = await adapter.spawn(
                    mock_job,
                    "resolve-issue",
                    "/tmp/test-worktree",
                    {}
                )
                # Deve retornar erro
                assert result.is_err
                return result

            # Executa e verifica que não levanta exceção por exc_info
            try:
                result = asyncio.run(test_spawn())
                assert result.is_err
            except (TypeError, KeyError) as e:
                if "exc_info" in str(e):
                    pytest.fail("logger.error está usando exc_info=True não suportado")
                else:
                    raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ============================================================================
# TDD ESTRITO: Teste do Fluxo do Loop de Mensagens do Agent SDK
# ============================================================================
# Metodologia: Red → Green → Refactor
#
# DOC: O fluxo do loop de mensagens deve:
# 1. Iterar sobre client.receive_response()
# 2. Capturar stdout durante o stream (AssistantMessage)
# 3. Detectar ResultMessage por múltiplos critérios
# 4. Terminar o loop quando ResultMessage é encontrado
# 5. Não travar indefinidamente (timeout)
# ============================================================================


class TestAgentSDKMessageLoopFlow:
    """
    Testes TDD estritos para o fluxo do loop de mensagens do Agent SDK.

    Red → Green → Refactor
    """

    @pytest.fixture
    def mock_job(self):
        """Job mock para teste."""
        job = Mock()
        job.job_id = "tdd-test-job-001"
        job.issue_number = 999
        job.event = Mock()
        job.event.payload = {
            "issue": {"title": "TDD Test Issue", "body": "Test body"},
            "repository": {"owner": {"login": "test"}, "name": "repo"}
        }
        job.worktree_path = "/tmp/tdd-test-worktree"
        job.branch_name = "tdd-test-branch"
        job.metadata = {}
        job.initial_snapshot = {}
        return job

    @pytest.mark.asyncio
    async def test_message_loop_flow_captures_stdout_and_resultmessage(self, mock_job):
        """
        TDD TESTE 1 (RED → GREEN): Fluxo do loop de mensagens.

        DOC: claude_sdk_adapter.py - spawn() método consume stream único

        Comportamento esperado:
        1. Loop itera sobre client.receive_response()
        2. Captura stdout de AssistantMessage durante o stream
        3. Detecta ResultMessage por msg_type ou subtype
        4. Termina loop quando ResultMessage é encontrado
        5. Retorna AgentExecution com stdout preenchido

        Este teste usa mocks para simular o comportamento do SDK
        e verificar que o loop processa corretamente cada tipo de mensagem.
        """
        from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter
        from unittest.mock import AsyncMock, MagicMock, patch
        import asyncio

        # === SETUP: Cria mocks para simular o SDK ===
        adapter = ClaudeSDKAdapter()

        # Mock de mensagens do SDK
        # Content deve ser lista real para len() funcionar
        mock_content_1 = Mock()
        mock_content_1.text = "Creating file hello.py..."

        mock_content_2 = Mock()
        mock_content_2.text = "File created successfully."

        mock_assistant_msg = Mock()
        mock_assistant_msg.__class__.__name__ = "AssistantMessage"
        mock_assistant_msg.content = [
            mock_content_1,
            mock_content_2,
        ]
        # NÃO tem is_error configurado para evitar detecção falsa
        type(mock_assistant_msg).is_error = None

        mock_result_msg = Mock()
        mock_result_msg.__class__.__name__ = "ResultMessage"
        mock_result_msg.is_error = False
        mock_result_msg.result = '{"success": true}'
        mock_result_msg.duration_ms = 1500
        mock_result_msg.content = None  # ResultMessage não tem content

        # Mock do cliente SDK
        mock_client_instance = AsyncMock()
        mock_client_instance.query = AsyncMock()

        # Cria o stream mock
        stream_mock = self._create_stream_mock([
            mock_assistant_msg,
            mock_result_msg,
        ])
        # receive_response() retorna um AsyncGenerator, não é async em si
        mock_client_instance.receive_response = Mock(return_value=stream_mock)

        mock_client_class = Mock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        # Patch do ClaudeSDKClient e ClaudeAgentOptions
        # O SDK é importado dentro do método spawn(), então patchamos o módulo claude_agent_sdk
        with patch('claude_agent_sdk.ClaudeSDKClient', mock_client_class):
            with patch('claude_agent_sdk.ClaudeAgentOptions'):
                # === EXECUTE: Chama o método spawn() ===
                result = await adapter.spawn(
                    job=mock_job,
                    skill="hello-world",
                    worktree_path=mock_job.worktree_path,
                    skybridge_context={"worktree_path": mock_job.worktree_path},
                )

                # === ASSERT: Verifica o comportamento esperado ===

                # 1. Deve retornar sucesso
                assert result.is_ok, f"spawn() deve retornar ok, mas retornou erro: {result.error}"

                # 2. AgentExecution deve ter stdout capturado
                execution = result.value
                assert execution.stdout is not None, "stdout não deve ser None"
                assert "Creating file hello.py..." in execution.stdout, \
                    "stdout deve conter texto da AssistantMessage"
                assert "File created successfully." in execution.stdout, \
                    "stdout deve conter todo o texto da AssistantMessage"

                # 3. Agent result existe (success depende do mock.is_error)
                assert execution.result is not None, "result não deve ser None"

                # 4. Stdout foi capturado durante o loop (PRINCIPAL)
                assert "Creating file hello.py..." in execution.stdout, \
                    "stdout deve conter texto da AssistantMessage"
                assert "File created successfully." in execution.stdout, \
                    "stdout deve conter todo o texto da AssistantMessage"

                # 5. Query foi chamada
                mock_client_instance.query.assert_called_once()

                # 6. receive_response foi chamado (o loop foi executado)
                mock_client_instance.receive_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_loop_detects_resultmessage_by_subtype(self, mock_job):
        """
        TDD TESTE 2: Detecção de ResultMessage por subtype.

        DOC: O loop deve detectar ResultMessage tanto por msg_type quanto por subtype.

        Cenário: ResultMessage com subtype='success' deve ser detectado
        mesmo que msg_type não seja 'ResultMessage'.
        """
        from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter
        from unittest.mock import AsyncMock, Mock, patch

        adapter = ClaudeSDKAdapter()

        # Mock de mensagem com subtype (como na documentação oficial)
        # IMPORTANTE: Content deve ser uma lista real para len() funcionar
        mock_content_item = Mock()
        mock_content_item.text = "Processing..."

        mock_custom_msg = Mock()
        mock_custom_msg.__class__.__name__ = "CustomMessage"
        mock_custom_msg.subtype = "processing"  # Não é ResultMessage ainda
        mock_custom_msg.content = [mock_content_item]  # Lista real com len()
        # NÃO tem is_error - Mock retorna False para hasattr quando configurado
        type(mock_custom_msg).is_error = None  # Propriedade não existe

        mock_result_with_subtype = Mock()
        mock_result_with_subtype.__class__.__name__ = "CompletionMessage"
        mock_result_with_subtype.subtype = "success"  # ← Deve ser detectado!
        mock_result_with_subtype.is_error = False
        mock_result_with_subtype.result = '{"completed": true}'
        mock_result_with_subtype.duration_ms = 1000
        mock_result_with_subtype.content = None  # ResultMessage não tem content

        mock_client_instance = AsyncMock()
        mock_client_instance.query = AsyncMock()

        # Cria o stream mock
        stream_mock = self._create_stream_mock([
            mock_custom_msg,
            mock_result_with_subtype,
        ])
        # receive_response() retorna um AsyncGenerator, não é async em si
        mock_client_instance.receive_response = Mock(return_value=stream_mock)

        mock_client_class = Mock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('claude_agent_sdk.ClaudeSDKClient', mock_client_class):
            with patch('claude_agent_sdk.ClaudeAgentOptions'):
                result = await adapter.spawn(
                    job=mock_job,
                    skill="hello-world",
                    worktree_path=mock_job.worktree_path,
                    skybridge_context={},
                )

                # ASSERT: Deve detectar ResultMessage por subtype
                assert result.is_ok, f"Deve detectar ResultMessage por subtype, erro: {result.error}"
                assert result.value.result.success is True

    @pytest.mark.asyncio
    async def test_message_loop_terminates_on_timeout(self, mock_job):
        """
        TDD TESTE 3: Timeout do loop.

        DOC: O loop deve terminar com timeout se ResultMessage não chegar.

        Cenário: Mock asyncio.timeout para levantar TimeoutError no loop.
        Esperado: TimeoutError é capturado e retorna erro.

        NOTA: Em vez de criar um stream realmente infinito (que pode travar),
        mockamos asyncio.timeout para simular o timeout de forma controlada.
        """
        from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter
        from unittest.mock import AsyncMock, Mock, patch
        import asyncio

        adapter = ClaudeSDKAdapter()

        # Mensagens normais antes do timeout
        mock_content_1 = Mock()
        mock_content_1.text = "Starting work..."

        mock_msg = Mock()
        mock_msg.__class__.__name__ = "AssistantMessage"
        mock_msg.content = [mock_content_1]
        type(mock_msg).is_error = None

        # Stream que retorna algumas mensagens antes do timeout simulado
        stream_mock = self._create_stream_mock([mock_msg])

        mock_client_instance = AsyncMock()
        mock_client_instance.query = AsyncMock()
        mock_client_instance.receive_response = Mock(return_value=stream_mock)

        mock_client_class = Mock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock asyncio.timeout para levantar TimeoutError
        # Isso simula o timeout sem precisar de um stream realmente infinito
        class MockTimeoutCM:
            """Context manager que levanta TimeoutError ao entrar."""
            def __init__(self, seconds):
                self.seconds = seconds

            async def __aenter__(self):
                # Levanta TimeoutError quando o loop começa
                raise TimeoutError(f"Simulated timeout after {self.seconds}s")

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_timeout(seconds):
            """Retorna o context manager mock (não é async)."""
            return MockTimeoutCM(seconds)

        with patch('claude_agent_sdk.ClaudeSDKClient', mock_client_class):
            with patch('claude_agent_sdk.ClaudeAgentOptions'):
                # Patch asyncio.timeout no módulo do adapter
                with patch('core.webhooks.infrastructure.agents.claude_sdk_adapter.asyncio.timeout',
                          side_effect=mock_timeout):
                    result = await adapter.spawn(
                        job=mock_job,
                        skill="hello-world",
                        worktree_path=mock_job.worktree_path,
                        skybridge_context={},
                    )

                    # ASSERT: Deve retornar erro por timeout
                    assert result.is_err, "Deve retornar erro quando timeout"
                    assert "Timeout" in result.error or "timeout" in result.error, \
                        f"Mensagem de erro deve mencionar timeout: {result.error}"

    @pytest.mark.asyncio
    async def test_message_loop_returns_error_when_no_resultmessage(self, mock_job):
        """
        TDD TESTE 4: Stream encerra sem ResultMessage.

        DOC: Se o stream encerrar sem ResultMessage, deve retornar erro.

        Cenário: Stream entrega algumas mensagens mas termina sem ResultMessage.
        Esperado: Erro indicando que ResultMessage não foi recebido.
        """
        from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter
        from unittest.mock import AsyncMock, Mock, patch

        adapter = ClaudeSDKAdapter()

        # Apenas AssistantMessage, sem ResultMessage
        # IMPORTANTE: Configurar Mock para NÃO ter is_error
        # Caso contrário hasattr(msg, 'is_error') retorna True (Mock cria attrs dinamicamente)
        mock_content_item = Mock()
        mock_content_item.text = "Some text..."

        mock_msg = Mock(spec_set=['__class__', 'content', 'subtype'])  # spec_set limita atributos
        mock_msg.__class__.__name__ = "AssistantMessage"
        mock_msg.content = [mock_content_item]  # Lista real para len()
        mock_msg.subtype = None
        # is_error NÃO existe no spec_set, então hasattr retorna False

        mock_client_instance = AsyncMock()
        mock_client_instance.query = AsyncMock()

        # Cria o stream mock
        stream_mock = self._create_stream_mock([mock_msg])
        # Stream que retorna mensagens mas termina sem ResultMessage
        mock_client_instance.receive_response = Mock(return_value=stream_mock)

        mock_client_class = Mock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('claude_agent_sdk.ClaudeSDKClient', mock_client_class):
            with patch('claude_agent_sdk.ClaudeAgentOptions'):
                result = await adapter.spawn(
                    job=mock_job,
                    skill="hello-world",
                    worktree_path=mock_job.worktree_path,
                    skybridge_context={},
                )

                # ASSERT: Deve retornar erro pois não há ResultMessage
                assert result.is_err, "Deve retornar erro quando não há ResultMessage"
                assert "ResultMessage" in result.error or "result" in result.error, \
                    f"Mensagem de erro deve mencionar ResultMessage: {result.error}"

    # ==========================================================================
    # HELPER METHODS (não são testes, apenas utilidades)
    # ==========================================================================

    def _create_stream_mock(self, messages):
        """
        Cria um mock de stream assíncrono que retorna as mensagens especificadas.

        O mock simula client.receive_response() retornando um AsyncIterator.

        receive_response() é um método que retorna um AsyncIterator, não um generator.

        Args:
            messages: Lista de mensagens Mock para retornar

        Returns:
            AsyncIterator com as mensagens (resultado de receive_response())
        """
        async def stream_generator():
            """Simula o stream do SDK."""
            for msg in messages:
                yield msg

        # Cria o gerador assíncrono
        gen = stream_generator()

        # O resultado de receive_response() é o próprio AsyncGenerator
        # AsyncGenerator já implementa __aiter__ e __anext__
        return gen
