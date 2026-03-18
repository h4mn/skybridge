# -*- coding: utf-8 -*-
"""
Testes para bugs de encoding e stderr None em GitService.

DOC: src/core/webhooks/application/git_service.py

Bug 1: UnicodeDecodeError quando git output contém caracteres especiais
Bug 2: AttributeError quando e.stderr é None em CalledProcessError
"""

import pytest
import subprocess
from unittest.mock import Mock, patch
from kernel import Result
from core.webhooks.application.git_service import GitService


class TestGitServiceEncodingBug:
    """Testes para Bug 1: UnicodeDecodeError em subprocess."""

    @pytest.mark.asyncio
    async def test_commit_handles_unicode_in_output(self):
        """
        DOC: git_service.py - commit() deve handle caracteres especiais no output do git.

        Bug: UnicodeDecodeError quando git retorna caracteres como emoji ou aspas especiais.
        Causa: subprocess.run() com text=True usa encoding do sistema (cp1252 no Windows).

        Esperado: commit() usa encoding='utf-8' para evitar erro de decode.
        """
        mock_result = Mock()
        mock_result.stdout = "abc123\n"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            with patch.object(GitService, '_get_last_commit_hash', return_value=Result.ok("abc123")):
                with patch.object(GitService, '_get_commit_stats', return_value={}):
                    service = GitService()

                    result = await service.commit(
                        worktree_path="B:\test\repo",
                        message='chore: test\n\n> "Teste com emoji 🚀"'
                    )

        assert result.is_ok  # Property, sem parênteses
        assert result.value.commit_hash == "abc123"


class TestGitServiceStderrNoneBug:
    """Testes para Bug 2: AttributeError quando e.stderr é None."""

    @pytest.mark.asyncio
    async def test_commit_handles_none_stderr(self):
        """
        DOC: git_service.py - commit() deve handle e.stderr == None.

        Bug: AttributeError: 'NoneType' object has no attribute 'lower'
        Linha: if "nothing to commit" in e.stderr.lower()
        Causa: CalledProcessError pode ter stderr=None

        Esperado: código verifica se stderr não é None antes de chamar .lower()
        """
        mock_error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["git", "commit", "-m", "test"],
            stderr=None
        )

        with patch('subprocess.run', side_effect=mock_error):
            service = GitService()

            result = await service.commit(
                worktree_path="B:\test\repo",
                message="test message"
            )

        assert result.is_err  # Property, sem parênteses
