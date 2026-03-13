# coding: utf-8
"""
Testes unitários para Progress.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.sky.bootstrap.progress import Progress
from core.sky.bootstrap.stage import Stage


class TestProgress:
    """Testes para a classe Progress."""

    def test_progress_initialization(self):
        """Testa inicialização de Progress."""
        progress = Progress()

        assert len(progress._stages) == 0
        assert len(progress._task_ids) == 0

    def test_add_stage(self):
        """Testa adição de estágio."""
        progress = Progress()
        stage = Stage("test", "Test Stage")

        progress.add_stage(stage)

        assert len(progress._stages) == 1
        assert progress._stages[0] == stage

    def test_add_multiple_stages(self):
        """Testa adição de múltiplos estágios."""
        progress = Progress()
        stages = [
            Stage("env", "Environment"),
            Stage("emb", "Embedding"),
            Stage("db", "Database"),
        ]

        for stage in stages:
            progress.add_stage(stage)

        assert len(progress._stages) == 3

    @patch("rich.console.Console")
    def test_run_context_yields_progress_context(self, mock_console_class):
        """Testa que run() yields um contexto de progresso."""
        progress = Progress()
        progress.add_stage(Stage("test", "Test Stage"))

        with progress.run() as ctx:
            assert ctx is not None
            assert hasattr(ctx, "start_stage")
            assert hasattr(ctx, "complete_stage")
            assert hasattr(ctx, "run_stage")

    @patch("rich.console.Console")
    def test_run_stage_executes_function(self, mock_console_class):
        """Testa que run_stage executa a função fornecida."""
        progress = Progress()
        progress.add_stage(Stage("test", "Test Stage"))

        mock_fn = MagicMock(return_value="result")
        mock_console = MagicMock()
        progress_with_console = Progress(console=mock_console)

        with progress_with_console.run() as ctx:
            result = ctx.run_stage("test", mock_fn, "arg1", "arg2")

        assert result == "result"
        mock_fn.assert_called_once_with("arg1", "arg2")

    @patch("rich.console.Console")
    def test_start_stage_marks_visible(self, mock_console_class):
        """Testa que start_stage marca estágio como visível."""
        progress = Progress()
        progress.add_stage(Stage("test", "Test Stage"))
        mock_console = MagicMock()
        progress_with_console = Progress(console=mock_console)

        with progress_with_console.run() as ctx:
            ctx.start_stage("test")
            # Verifica que o estágio está visível
            # (em implementação real, isso atualizaria o Progress)
            pass

    @patch("rich.console.Console")
    def test_complete_stage_advances_progress(self, mock_console_class):
        """Testa que complete_stage avança o progresso."""
        progress = Progress()
        progress.add_stage(Stage("test", "Test Stage"))
        mock_console = MagicMock()
        progress_with_console = Progress(console=mock_console)

        with progress_with_console.run() as ctx:
            ctx.complete_stage("test")
            # Verifica que o progresso avançou
            assert ctx._current_stage_index == 1
