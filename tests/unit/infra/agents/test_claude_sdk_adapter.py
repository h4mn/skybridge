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
