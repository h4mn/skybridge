# -*- coding: utf-8 -*-
"""
Testes TDD Estrito para lifespan handler.

DOC: runtime/bootstrap/app.py - lifespan deve gerenciar lifecycle do webhook worker.

Fluxo TDD:
1. RED → Teste que reproduz bug/explica comportamento esperado
2. GREEN → Implementação mínima para passar
3. REFACTOR → Melhorar código mantendo verde

Bug Original:
    CancelledError durante shutdown do Uvicorn quando webhook worker está ativo.

Comportamento Esperado:
    - Startup: Inicia worker em thread separada com event loop próprio
    - Shutdown: Chama worker.stop(), aguarda thread com timeout, para listener
    - Sem CancelledError: Event loops são encerrados graciosamente
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import asyncio


class TestLifespanGerenciamentoWorker:
    """
    Testa gerenciamento do webhook worker no lifespan handler.

    Especificação:
        DOC: .claude/CLAUDE.md - TDD Estrito
        DOC: runtime/bootstrap/app.py - lifespan context manager
    """

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_chama_worker_stop_graciosamente(self):
        """
        RED → GREEN: Shutdown deve chamar worker.stop() para evitar CancelledError.

        BUG REPRODUZIDO:
            Originalmente, o lifespan não chamava worker.stop(), causando
            CancelledError quando Uvicorn tentava encerrar o event loop.

        COMPORTAMENTO ESPERADO:
            - worker.stop() é chamado no shutdown (after yield)
            - Isso sinaliza o worker para parar o loop de processamento
            - Event loop pode ser encerrado sem CancelledError

        Dado:
            - Worker instance existe (_webhook_worker_instance global)
            - Worker thread está ativa

        Quando:
            - Lifespan shutdown é executado (after yield)

        Então:
            - worker.stop() é chamado exatamente uma vez
        """
        # Arrange
        mock_app = Mock()
        mock_worker = Mock()
        mock_thread = Mock()
        mock_thread.is_alive = Mock(side_effect=[True, False])  # Thread viva, depois encerra

        # Patch nas globais do módulo
        import runtime.bootstrap.app as app_module
        original_worker_instance = app_module._webhook_worker_instance
        original_worker_thread = app_module._webhook_worker_thread
        original_listener = app_module._trello_listener

        try:
            # Configura mocks nas globais
            app_module._webhook_worker_instance = mock_worker
            app_module._webhook_worker_thread = mock_thread
            app_module._trello_listener = None

            # Act: Startup + Shutdown usando async with
            from runtime.bootstrap.app import lifespan

            with patch('runtime.config.config.get_webhook_config') as mock_config:
                mock_config.return_value.enabled_sources = []  # Desabilita worker real

                async with lifespan(mock_app):
                    pass  # Startup aconteceu aqui

            # Assert: worker.stop() foi chamado (no shutdown, após sair do async with)
            mock_worker.stop.assert_called_once()
        finally:
            # Restore originals
            app_module._webhook_worker_instance = original_worker_instance
            app_module._webhook_worker_thread = original_worker_thread
            app_module._trello_listener = original_listener

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_aguarda_thread_com_timeout_5_segundos(self):
        """
        GREEN: Shutdown deve aguardar thread com timeout de 5 segundos.

        Dado:
            - Worker thread está ativa
            - worker.stop() já foi chamado

        Quando:
            - Lifespan shutdown é executado

        Então:
            - thread.join(timeout=5.0) é chamado
            - Não bloqueia indefinidamente se thread não responder
        """
        # Arrange
        mock_app = Mock()
        mock_worker = Mock()
        mock_thread = Mock()
        mock_thread.is_alive = Mock(return_value=True)  # Thread está viva inicialmente

        import runtime.bootstrap.app as app_module
        original_worker_instance = app_module._webhook_worker_instance
        original_worker_thread = app_module._webhook_worker_thread
        original_listener = app_module._trello_listener

        try:
            app_module._webhook_worker_instance = mock_worker
            app_module._webhook_worker_thread = mock_thread
            app_module._trello_listener = None

            # Act
            from runtime.bootstrap.app import lifespan

            with patch('runtime.config.config.get_webhook_config') as mock_config:
                mock_config.return_value.enabled_sources = []

                async with lifespan(mock_app):
                    pass  # Startup

            # Assert: thread.join() foi chamado com timeout de 5s
            mock_thread.join.assert_called_once_with(timeout=5.0)
        finally:
            app_module._webhook_worker_instance = original_worker_instance
            app_module._webhook_worker_thread = original_worker_thread
            app_module._trello_listener = original_listener

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_avisa_quando_thread_nao_termina(self):
        """
        GREEN: Deve avisar quando thread não termina em 5 segundos.

        Dado:
            - Worker thread continua ativa após join(timeout=5.0)

        Quando:
            - Lifespan shutdown é executado

        Então:
            - Logger.warning é chamado com mensagem apropriada
        """
        # Arrange
        mock_app = Mock()
        mock_logger = Mock()
        mock_worker = Mock()
        mock_thread = Mock()
        mock_thread.is_alive = Mock(return_value=True)  # Thread ainda viva!

        import runtime.bootstrap.app as app_module
        original_worker_instance = app_module._webhook_worker_instance
        original_worker_thread = app_module._webhook_worker_thread
        original_listener = app_module._trello_listener

        try:
            app_module._webhook_worker_instance = mock_worker
            app_module._webhook_worker_thread = mock_thread
            app_module._trello_listener = None

            # Act
            from runtime.bootstrap.app import lifespan

            with patch('runtime.config.config.get_webhook_config') as mock_config, \
                 patch('runtime.observability.logger.get_logger', return_value=mock_logger):
                mock_config.return_value.enabled_sources = []

                async with lifespan(mock_app):
                    pass  # Startup

            # Assert: logger.warning foi chamado
            assert any(
                'não terminou em 5 segundos' in str(call)
                for call in mock_logger.warning.call_args_list
            ), "Deve emitir warning quando thread não termina"
        finally:
            app_module._webhook_worker_instance = original_worker_instance
            app_module._webhook_worker_thread = original_worker_thread
            app_module._trello_listener = original_listener

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_para_trello_listener_se_ativo(self):
        """
        GREEN: TrelloListener.stop() deve ser chamado no shutdown.

        Dado:
            - TrelloListener foi iniciado no startup
            - _trello_listener global não é None

        Quando:
            - Lifespan shutdown é executado

        Então:
            - trello_listener.stop() é chamado
        """
        # Arrange
        mock_app = Mock()
        mock_worker = Mock()
        mock_thread = Mock()
        mock_thread.is_alive = Mock(side_effect=[True, False])  # Thread viva, depois encerra
        mock_listener = Mock()
        mock_listener.stop = AsyncMock()

        import runtime.bootstrap.app as app_module
        original_worker_instance = app_module._webhook_worker_instance
        original_worker_thread = app_module._webhook_worker_thread
        original_listener = app_module._trello_listener

        try:
            app_module._webhook_worker_instance = mock_worker
            app_module._webhook_worker_thread = mock_thread
            app_module._trello_listener = mock_listener

            # Act
            from runtime.bootstrap.app import lifespan

            with patch('runtime.config.config.get_webhook_config') as mock_config:
                mock_config.return_value.enabled_sources = []

                async with lifespan(mock_app):
                    pass  # Startup

            # Assert: listener.stop() foi chamado
            mock_listener.stop.assert_called_once()
        finally:
            app_module._webhook_worker_instance = original_worker_instance
            app_module._webhook_worker_thread = original_worker_thread
            app_module._trello_listener = original_listener

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_faz_nothing_se_worker_nao_existe(self):
        """
        GREEN: Shutdown deve ser seguro mesmo se worker nunca foi iniciado.

        Dado:
            - _webhook_worker_instance é None
            - _webhook_worker_thread é None

        Quando:
            - Lifespan shutdown é executado

        Então:
            - Nenhum erro é levantado
            - Lifespan completa normalmente
        """
        # Arrange
        mock_app = Mock()

        import runtime.bootstrap.app as app_module
        original_worker_instance = app_module._webhook_worker_instance
        original_worker_thread = app_module._webhook_worker_thread
        original_listener = app_module._trello_listener

        try:
            app_module._webhook_worker_instance = None
            app_module._webhook_worker_thread = None
            app_module._trello_listener = None

            # Act & Assert: Não deve levantar exceção
            from runtime.bootstrap.app import lifespan

            with patch('runtime.config.config.get_webhook_config') as mock_config:
                mock_config.return_value.enabled_sources = []

                async with lifespan(mock_app):
                    pass  # Startup

            # Se chegou aqui, não houve exceção - TESTE PASSA
        finally:
            app_module._webhook_worker_instance = original_worker_instance
            app_module._webhook_worker_thread = original_worker_thread
            app_module._trello_listener = original_listener

    @pytest.mark.asyncio
    async def test_lifespan_integration_shutdown_gracioso_com_worker_mock(self):
        """
        GREEN: Integração completa de shutdown com worker mock.

        Este teste valida o fluxo completo de shutdown:
        1. worker.stop() é chamado
        2. thread.join(timeout=5.0) é chamado
        3. Thread encerra graciosamente
        4. Nenhum erro é levantado
        """
        # Arrange
        mock_app = Mock()
        mock_worker = Mock()
        mock_thread = Mock()
        # Thread está viva inicialmente, após join encerra (is_alive retorna False)
        mock_thread.is_alive = Mock(side_effect=[True, False])

        import runtime.bootstrap.app as app_module
        original_worker_instance = app_module._webhook_worker_instance
        original_worker_thread = app_module._webhook_worker_thread
        original_listener = app_module._trello_listener

        try:
            app_module._webhook_worker_instance = mock_worker
            app_module._webhook_worker_thread = mock_thread
            app_module._trello_listener = None

            # Act
            from runtime.bootstrap.app import lifespan

            with patch('runtime.config.config.get_webhook_config') as mock_config, \
                 patch('runtime.observability.logger.get_logger') as mock_logger:
                mock_config.return_value.enabled_sources = []

                async with lifespan(mock_app):
                    pass  # Startup

            # Assert: fluxo completo de shutdown
            mock_worker.stop.assert_called_once()
            mock_thread.join.assert_called_once_with(timeout=5.0)
            # Thread encerrou, então não há warning
            assert not any(
                'não terminou em 5 segundos' in str(call)
                for call in mock_logger.warning.call_args_list
            )
        finally:
            app_module._webhook_worker_instance = original_worker_instance
            app_module._webhook_worker_thread = original_worker_thread
            app_module._trello_listener = original_listener


class TestLifespanSemWorker:
    """
    Testa comportamento do lifespan quando worker não é iniciado.
    """

    @pytest.mark.asyncio
    async def test_lifespan_com_github_desabilitado_nao_inicia_worker(self):
        """
        GREEN: Com GitHub desabilitado, nenhuma thread deve ser criada.

        Este é um teste de integração leve que verifica que o lifespan
        não tenta iniciar worker quando GitHub não está habilitado.
        """
        # Arrange
        mock_app = Mock()

        # Act
        from runtime.bootstrap.app import lifespan

        # Config: GitHub não habilitado (lista vazia)
        with patch('runtime.config.config.get_webhook_config') as mock_config:
            mock_config.return_value.enabled_sources = []  # Vazio = sem github
            mock_config.return_value.worktree_base_path = '/tmp/test'
            mock_config.return_value.base_branch = 'main'

            async with lifespan(mock_app):
                # Startup aconteceu
                pass

            # Assert: Nenhuma thread foi criada (globais ainda são None)
            from runtime.bootstrap.app import _webhook_worker_thread
            assert _webhook_worker_thread is None


# -----------------------------------------------------------------------------
# DOCUMENTAÇÃO DE REFACTORING
# -----------------------------------------------------------------------------

"""
REFACTOR NOTAS (após GREEN):

Após todos os testes passarem, considerar melhorias:

1. EXTRAIR run_worker_in_thread():
   A função está aninhada no lifespan. Pode ser movida para module-level:
   - Melhor testabilidade
   - Permite testar isoladamente
   - Reduz complexidade do lifespan

2. CONFIGURAR timeout via ambiente:
   Atualmente 5.0s está hardcoded. Considerar:
   - WEBHOOK_WORKER_SHUTDOWN_TIMEOUT env var
   - Default de 5.0s se não configurado

3. ADICIONAR métricas de shutdown:
   - Tempo que shutdown levou
   - Quantas workers foram parados
   - Quantas threads falharam em terminar

4. MELHORAR structured logging:
   - Adicionar correlation_id nos logs de lifespan
   - Incluir timestamps relativos (startup duration, etc.)

5. REVISAR estratégia de teste:
   - Atualmente modificando globais diretamente
   - Considerar injeção de dependências para melhor testabilidade

6. SIMPLIFICAR setup de testes:
   - Criar fixture pytest para setup/teardown das globais
   - Reduzir duplicação nos testes
"""
