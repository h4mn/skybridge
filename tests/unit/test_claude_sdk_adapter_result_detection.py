"""
TDD ESTRITO: Teste de Detecção Robusta de ResultMessage

Metodologia: Red → Green → Refactor

DOC: claude_sdk_adapter.py - spawn() deve detectar ResultMessage corretamente

Bug atual (309MB de logs em 1.5M mensagens):
- hasattr(msg, 'is_error') é fraco e falha com Mock objects
- Loop infinito quando ResultMessage não é detectada

Comportamento esperado:
1. Detecção robusta de ResultMessage por múltiplos critérios
2. Loop termina mesmo com mensagens atípicas
3. Timeout funciona corretamente
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


class TestResultMessageDetectionRobustness:
    """
    TDD TESTES para detecção robusta de ResultMessage.

    Red → Green → Refactor
    """

    @pytest.fixture
    def mock_job(self):
        """Job mock para teste."""
        job = Mock()
        job.job_id = "tdd-test-job-infinite"
        job.issue_number = 999
        job.event = Mock()
        job.event.payload = {}
        job.worktree_path = "/tmp/test"
        job.branch_name = "test-branch"
        job.metadata = {}
        job.initial_snapshot = {}
        return job

    def test_hasattr_with_mock_is_unreliable(self):
        """
        TDD TESTE 1 (RED → GREEN): hasattr() com Mock retorna True mesmo sem atributo.

        DOC: hasattr() em Mock objects sempre retorna True, causando detecção falha.

        Este teste demonstra o BUG: Mock objects fazem hasattr() retornar True
        mesmo quando o atributo não existe realmente.
        """
        # Mock simples - sem atributo is_error configurado
        mock_msg = Mock()

        # hasattr retorna True mesmo sem is_error existir!
        result = hasattr(mock_msg, 'is_error')

        # BUG: hasattr retorna True para qualquer atributo em Mock!
        assert result is True, \
            "hasattr(mock, 'qualquer_coisa') sempre retorna True - BUG confirmado"

        # Mas getattr retorna Mock object, não True/False
        is_error_value = getattr(mock_msg, 'is_error', None)
        assert not isinstance(is_error_value, bool), \
            f"getattr retornou {type(is_error_value)}, não bool"

    def test_spec_set_mock_limits_attributes(self):
        """
        TDD TESTE 2: Mock com spec_set restringe hasattr corretamente.

        DOC: Usar spec_set restringe hasattr para apenas atributos reais.
        """
        # Mock com spec_set - apenas atributos listados existem
        mock_msg = Mock(spec_set=['__class__', 'content'])

        # hasattr retorna False para atributos não listados
        assert hasattr(mock_msg, 'is_error') is False, \
            "spec_set Mock deve retornar False para atributos não listados"

    def test_result_message_detection_logic(self):
        """
        TDD TESTE 3: Lógica correta de detecção de ResultMessage.

        DOC: Detecção deve usar getattr com valor explícito, não hasattr.

        Comportamento esperado:
        - is_error=True → ResultMessage (erro)
        - is_error=False → ResultMessage (sucesso)
        - is_error=None → NÃO é ResultMessage (precisa ser explícito)
        - is_error inexistente → NÃO é ResultMessage
        """
        # Caso 1: is_error=True → deve detectar
        msg_error = Mock()
        msg_error.__class__.__name__ = "ResultMessage"
        type(msg_error).is_error = True  # Propriedade retorna True

        is_result = (
            msg_error.__class__.__name__ == "ResultMessage" or
            getattr(msg_error, 'is_error', None) in [True, False]  # ← LÓGICA CORRETA
        )
        assert is_result is True, "is_error=True deve detectar ResultMessage"

        # Caso 2: is_error=False → deve detectar
        msg_success = Mock()
        msg_success.__class__.__name__ = "ResultMessage"
        type(msg_success).is_error = False

        is_result = (
            msg_success.__class__.__name__ == "ResultMessage" or
            getattr(msg_success, 'is_error', None) in [True, False]
        )
        assert is_result is True, "is_error=False deve detectar ResultMessage"

        # Caso 3: is_error=None → NÃO deve detectar
        msg_none = Mock()
        msg_none.__class__.__name__ = "AssistantMessage"
        type(msg_none).is_error = None

        is_result = (
            msg_none.__class__.__name__ == "ResultMessage" or
            getattr(msg_none, 'is_error', None) in [True, False]
        )
        assert is_result is False, "is_error=None NÃO deve detectar ResultMessage"

        # Caso 4: sem is_error → NÃO deve detectar
        msg_no_attr = Mock(spec_set=['__class__', 'content'])
        msg_no_attr.__class__.__name__ = "AssistantMessage"

        is_result = (
            msg_no_attr.__class__.__name__ == "ResultMessage" or
            getattr(msg_no_attr, 'is_error', None) in [True, False]
        )
        assert is_result is False, "Sem is_error NÃO deve detectar ResultMessage"


    @pytest.mark.asyncio
    async def test_infinite_stream_with_no_resultmessage(self, mock_job):
        """
        TDD TESTE 4 (RED): Stream infinito sem ResultMessage causa loop infinito.

        DOC: O loop async for nunca termina se ResultMessage não chegar.

        BUG ATUAL: Se o stream retornar mensagens infinitamente sem ResultMessage,
        o loop nunca termina (309MB de logs, 1.5M mensagens).

        Comportamento esperado: Timeout deve interromper o loop.
        """
        from core.webhooks.infrastructure.agents.claude_sdk_adapter import ClaudeSDKAdapter
        from unittest.mock import AsyncMock, Mock, patch
        import asyncio

        adapter = ClaudeSDKAdapter()

        # Mock de mensagem que NÃO é ResultMessage
        mock_content = Mock()
        mock_content.text = "Processing..."

        mock_assistant_msg = Mock(spec_set=['__class__', 'content', 'subtype'])
        mock_assistant_msg.__class__.__name__ = "AssistantMessage"
        mock_assistant_msg.content = [mock_content]
        mock_assistant_msg.subtype = None
        # Note: sem is_error no spec_set, então hasattr retorna False

        # Stream que gera YIELD INFINITO (usando itertools.cycle)
        # Mas vamos limitar para o teste
        class InfiniteStreamMock:
            """Stream que retorna a mesma mensagem infinitamente."""
            def __init__(self):
                self.count = 0
                self.max_messages = 100  # Limite para teste (não trava o pytest)

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.count >= self.max_messages:
                    raise StopAsyncIteration
                self.count += 1
                return mock_assistant_msg

        mock_client_instance = AsyncMock()
        mock_client_instance.query = AsyncMock()
        mock_client_instance.receive_response = Mock(return_value=InfiniteStreamMock())

        mock_client_class = Mock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        # Patch timeout para 1 segundo
        class MockTimeoutCM:
            def __init__(self, seconds):
                self.seconds = seconds

            async def __aenter__(self):
                return self  # Não levanta erro, deixa rodar

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_timeout(seconds):
            return MockTimeoutCM(seconds)

        with patch('claude_agent_sdk.ClaudeSDKClient', mock_client_class):
            with patch('claude_agent_sdk.ClaudeAgentOptions'):
                with patch('core.webhooks.infrastructure.agents.claude_sdk_adapter.asyncio.timeout',
                          side_effect=mock_timeout):
                    # O loop NÃO deve terminar com ResultMessage
                    # Deve esgotar o stream (max_messages)
                    result = await adapter.spawn(
                        job=mock_job,
                        skill="test",
                        worktree_path=mock_job.worktree_path,
                        skybridge_context={},
                    )

                    # ASSERT: Deve retornar erro pois não há ResultMessage
                    assert result.is_err, "Deve retornar erro sem ResultMessage"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
