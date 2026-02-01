# -*- coding: utf-8 -*-
"""
Testes unitários para safe_git_tool.

TDD Estrito: Testes escritos ANTES da implementação.

Esses testes seguem o ciclo Red-Green-Refactor:
1. RED - Testes falham inicialmente (safe_git_tool.py não existe)
2. GREEN - Implementação mínima para passar
3. REFACTOR - Melhorias mantendo testes verdes

DOC: PLAN.md - Fase 2: Criar Custom Tool safe_git
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from kernel.contracts.result import Result


class TestSafeGitBlocksCheckoutExistingBranch:
    """
    Testa que safe_git bloqueia git checkout de branches existentes.

    DOC: PLAN.md Fase 2 - Regra: "Bloqueia checkout de branches existentes"
    """

    @pytest.fixture
    def mock_cwd(self):
        """Diretório de trabalho mock."""
        return "B:/_repositorios/skybridge-auto/test/worktree"

    def test_safe_git_blocks_checkout_existing_branch_dev(self, mock_cwd):
        """
        Testa que git checkout dev é bloqueado.

        BUG: Agentes podem mudar para branch existente (dev, main, etc)
        Esperado: Comando é rejeitado com erro de permissão
        """
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        result = safe_git(
            command="git checkout dev",
            cwd=mock_cwd
        )

        assert result.is_err
        assert "bloqueado" in result.error.lower() or "not allowed" in result.error.lower()
        assert "checkout" in result.error.lower() or "branch existente" in result.error.lower()

    def test_safe_git_blocks_checkout_existing_branch_main(self, mock_cwd):
        """Testa que git checkout main é bloqueado."""
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        result = safe_git(
            command="git checkout main",
            cwd=mock_cwd
        )

        assert result.is_err
        assert "checkout" in result.error.lower() or "existente" in result.error.lower()

    def test_safe_git_blocks_checkout_existing_branch_auto(self, mock_cwd):
        """Testa que git checkout auto é bloqueado (branch base)."""
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        result = safe_git(
            command="git checkout auto",
            cwd=mock_cwd
        )

        assert result.is_err

    def test_safe_git_blocks_checkout_with_dash_b_without_sky_prefix(self, mock_cwd):
        """
        Testa que git checkout -b sem prefixo sky/ é bloqueado.

        Exemplos bloqueados:
        - git checkout -b feature-xyz
        - git checkout -b bugfix-123
        - git checkout -b teste
        """
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        result = safe_git(
            command="git checkout -b feature-xyz",
            cwd=mock_cwd
        )

        assert result.is_err
        assert "prefixo" in result.error.lower() or "sky/" in result.error.lower()

    def test_safe_git_blocks_checkout_new_branch_without_sky_prefix(self, mock_cwd):
        """Testa que git checkout -b sem-prefixo é bloqueado."""
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        result = safe_git(
            command="git checkout -b nova-branch",
            cwd=mock_cwd
        )

        assert result.is_err
        assert "sky/" in result.error.lower()


class TestSafeGitAllowsCheckoutWithSkyPrefix:
    """
    Testa que safe_git permite git checkout -b com prefixo sky/*.

    DOC: PLAN.md Fase 2 - Regra: "Permite apenas git checkout -b sky/*"
    """

    @pytest.fixture
    def mock_cwd(self):
        """Diretório de trabalho mock."""
        return "B:/_repositorios/skybridge-auto/test/worktree"

    @patch('subprocess.run')
    def test_safe_git_allows_checkout_with_sky_prefix(self, mock_run, mock_cwd):
        """
        Testa que git checkout -b sky/test-branch é permitido.

        Esperado:
        - Comando é executado
        - Subprocess.run é chamado com argumentos corretos
        - Retorna stdout do git
        """
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        # Mock subprocess.run para retornar sucesso
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Branch 'sky/test-branch' criada"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = safe_git(
            command="git checkout -b sky/test-branch",
            cwd=mock_cwd
        )

        assert result.is_ok
        assert "sky/test-branch" in result.value or "criada" in result.value

    @patch('subprocess.run')
    def test_safe_git_allows_checkout_sky_github_issue(self, mock_run, mock_cwd):
        """
        Testa que git checkout -b sky/github/issue/123/abc123 é permitido.

        Este é o padrão usado para worktrees de agentes.
        """
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Branch criada"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = safe_git(
            command="git checkout -b sky/github/issue/123/a5a8ad30",
            cwd=mock_cwd
        )

        assert result.is_ok

    @patch('subprocess.run')
    def test_safe_git_allows_checkout_sky_test_prefix(self, mock_run, mock_cwd):
        """
        Testa que git checkout -b sky-test/* é permitido para worktrees de teste.

        DOC: PLAN.md Fase 5 - "sky-test/*: Prefixo para worktrees de desenvolvimento/teste"
        """
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Branch criada"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = safe_git(
            command="git checkout -b sky-test/hello-world-20250131-143000",
            cwd=mock_cwd
        )

        assert result.is_ok


class TestSafeGitAllowsCommitAndPush:
    """
    Testa que safe_git permite git commit e git push.

    DOC: PLAN.md Fase 2 - Regra: "Permite: commit, push, status, worktree add"
    """

    @pytest.fixture
    def mock_cwd(self):
        """Diretório de trabalho mock."""
        return "B:/_repositorios/skybridge-auto/test/worktree"

    @patch('subprocess.run')
    def test_safe_git_allows_git_commit(self, mock_run, mock_cwd):
        """Testa que git commit é permitido."""
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "[sky/test-branch 1234567] Test commit"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = safe_git(
            command="git commit -m 'Test commit'",
            cwd=mock_cwd
        )

        assert result.is_ok
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_safe_git_allows_git_push(self, mock_run, mock_cwd):
        """Testa que git push é permitido."""
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Everything up-to-date"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = safe_git(
            command="git push origin sky/test-branch",
            cwd=mock_cwd
        )

        assert result.is_ok


class TestSafeGitAllowsStatus:
    """
    Testa que safe_git permite git status.
    """

    @pytest.fixture
    def mock_cwd(self):
        """Diretório de trabalho mock."""
        return "B:/_repositorios/skybridge-auto/test/worktree"

    @patch('subprocess.run')
    def test_safe_git_allows_git_status(self, mock_run, mock_cwd):
        """Testa que git status é permitido."""
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "On branch sky/test-branch\nnothing to commit"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = safe_git(
            command="git status",
            cwd=mock_cwd
        )

        assert result.is_ok
        assert "branch" in result.value.lower()


class TestSafeGitAllowsWorktreeAdd:
    """
    Testa que safe_git permite git worktree add.

    DOC: PLAN.md Fase 2 - Regra: "Permite: commit, push, status, worktree add"
    """

    @pytest.fixture
    def mock_cwd(self):
        """Diretório de trabalho mock."""
        return "B:/_repositorios/skybridge-auto"

    @patch('subprocess.run')
    def test_safe_git_allows_worktree_add(self, mock_run, mock_cwd):
        """Testa que git worktree add é permitido."""
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Worktree criada"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = safe_git(
            command="git worktree add ../skybridge-auto/webhook/github/issue/123/abc123 -b sky/github/issue/123/abc123 auto",
            cwd=mock_cwd
        )

        assert result.is_ok


class TestSafeGitBlocksDestructiveCommands:
    """
    Testa que safe_git bloqueia comandos destrutivos.

    DOC: PLAN.md Fase 2 - Segurança: Bloqueia comandos que podem destruir trabalho
    """

    @pytest.fixture
    def mock_cwd(self):
        """Diretório de trabalho mock."""
        return "B:/_repositorios\skybridge-auto\test/worktree"

    def test_safe_git_blocks_reset_hard(self, mock_cwd):
        """
        Testa que git reset --hard é bloqueado.

        RAZÃO: Comando destrutivo pode descartar mudanças não commitadas
        """
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        result = safe_git(
            command="git reset --hard HEAD",
            cwd=mock_cwd
        )

        assert result.is_err
        assert "bloqueado" in result.error.lower() or "destructivo" in result.error.lower()

    def test_safe_git_blocks_clean(self, mock_cwd):
        """
        Testa que git clean é bloqueado.

        RAZÃO: Comando destrutivo pode remover arquivos não rastreados
        """
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        result = safe_git(
            command="git clean -fd",
            cwd=mock_cwd
        )

        assert result.is_err

    def test_safe_git_blocks_restore(self, mock_cwd):
        """
        Testa que git restore é bloqueado.

        RAZÃO: Comando destrutivo pode descartar mudanças
        """
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        result = safe_git(
            command="git restore .",
            cwd=mock_cwd
        )

        assert result.is_err


class TestSafeGitReturnsErrorOnGitFailure:
    """
    Testa que safe_git retorna erro quando git falha.

    Isso garante que falhas do git são propagadas corretamente.
    """

    @pytest.fixture
    def mock_cwd(self):
        """Diretório de trabalho mock."""
        return "B:/_repositorios/skybridge-auto/test/worktree"

    @patch('subprocess.run')
    def test_safe_git_returns_error_on_git_failure(self, mock_run, mock_cwd):
        """
        Testa que falhas do git são retornadas como Result.err.

        Cenário: git status falha porque não é um repositório git
        """
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        # Mock subprocess.run para simular falha do git
        mock_result = Mock()
        mock_result.returncode = 128
        mock_result.stdout = ""
        mock_result.stderr = "fatal: not a git repository"
        mock_run.return_value = mock_result

        result = safe_git(
            command="git status",
            cwd=mock_cwd
        )

        assert result.is_err
        assert "git" in result.error.lower() or "repositório" in result.error.lower()


class TestSafeGitValidationErrors:
    """
    Testa validações de entrada do safe_git.
    """

    @pytest.fixture
    def mock_cwd(self):
        """Diretório de trabalho mock."""
        return "B:/_repositorios/skybridge-auto/test/worktree"

    def test_safe_git_rejects_empty_command(self, mock_cwd):
        """Testa que comando vazio é rejeitado."""
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        result = safe_git(
            command="",
            cwd="/tmp/test"
        )

        assert result.is_err

    def test_safe_git_rejects_none_cwd(self, mock_cwd):
        """Testa que cwd None é rejeitado."""
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        result = safe_git(
            command="git status",
            cwd=None
        )

        assert result.is_err

    @patch('subprocess.run')
    def test_safe_git_passes_cwd_to_subprocess(self, mock_run, mock_cwd):
        """
        Testa que cwd é passado corretamente para subprocess.run.

        IMPORTANTE: Isso garante que operações git acontecem no worktree correto,
        não no repositório principal.
        """
        from core.webhooks.infrastructure.agents.safe_git_tool import safe_git

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "OK"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        test_cwd = "B:/_repositorios/skybridge-auto/test/worktree"

        result = safe_git(
            command="git status",
            cwd=test_cwd
        )

        assert result.is_ok
        # Verifica que subprocess.run foi chamado com cwd correto
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1] if mock_run.call_args[1] else {}
        assert call_kwargs.get('cwd') == test_cwd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
