# -*- coding: utf-8 -*-
"""
Guardrails para validação de jobs.

PRD018 Fase 3: Validações rápidas antes de commit/push/PR.
- Diff check: arquivos modificados
- Syntax check: py_compile para validar Python
- Pytest check: roda testes (não-bloqueante, marca metadata)

Os guardrails são executados após o agente modificar arquivos
e antes das operações de commit/push/PR.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.contracts.result import Result

from kernel.contracts.result import Result


class GuardrailsResult:
    """
    Resultado dos guardrails.

    Attributes:
        passed: Lista de guardrails que passaram
        warnings: Lista de avisos (não bloqueia)
        failed: Lista de guardrails que falharam (bloqueia)
        metadata: Informações adicionais (pytest, diff, etc.)
    """

    def __init__(
        self,
        passed: list[str] | None = None,
        warnings: list[str] | None = None,
        failed: list[str] | None = None,
        metadata: dict | None = None,
    ):
        self.passed = passed or []
        self.warnings = warnings or []
        self.failed = failed or []
        self.metadata = metadata or {}

    @property
    def is_success(self) -> bool:
        """True se nenhum guardrail crítico falhou."""
        return len(self.failed) == 0

    def add_passed(self, name: str) -> None:
        """Adiciona guardrail que passou."""
        self.passed.append(name)

    def add_warning(self, name: str, message: str) -> None:
        """Adiciona aviso (não-bloqueante)."""
        self.warnings.append(f"{name}: {message}")

    def add_failure(self, name: str, message: str) -> None:
        """Adiciona falha crítica (bloqueia)."""
        self.failed.append(f"{name}: {message}")

    def update_metadata(self, key: str, value: object) -> None:
        """Atualiza metadata."""
        self.metadata[key] = value


class JobGuardrails:
    """
    Guardrails para validação de jobs.

    Responsabilidades:
    - Diff check: valida que arquivos foram modificados
    - Syntax check: valida syntax Python
    - Pytest check: roda testes (não-bloqueante)

    O guardrails retornam Result com metadata para ser usado
    no commit/push/PR.
    """

    def __init__(self, timeout_syntax: int = 30, timeout_pytest: int = 120):
        """
        Inicializa guardrails.

        Args:
            timeout_syntax: Timeout em segundos para syntax check
            timeout_pytest: Timeout em segundos para pytest
        """
        self.timeout_syntax = timeout_syntax
        self.timeout_pytest = timeout_pytest

    async def validate_all(self, worktree_path: str) -> Result[GuardrailsResult, str]:
        """
        Executa todos os guardrails em sequência.

        Args:
            worktree_path: Caminho para o worktree

        Returns:
            Result com GuardrailsResult ou erro

        Note:
            Diff check e syntax check são BLOQUEANTES.
            Pytest check é NÃO-BLOQUEANTE (apenas aviso).
        """
        result = GuardrailsResult()

        # Guardrail 1: Diff check (BLOQUEANTE)
        diff_result = await self._diff_check(worktree_path)
        if diff_result.is_err:
            return Result.err(diff_result.error)
        result.update_metadata("diff", diff_result.value)
        result.add_passed("diff_check")

        # Guardrail 2: Syntax check (BLOQUEANTE)
        syntax_result = await self._syntax_check(worktree_path)
        if syntax_result.is_err:
            return Result.err(syntax_result.error)
        result.add_passed("syntax_check")

        # Guardrail 3: Pytest check (NÃO-BLOQUEANTE)
        pytest_result = await self._pytest_check(worktree_path)
        if pytest_result.is_ok:
            pytest_data = pytest_result.value

            # Verifica se pytest falhou
            if pytest_data.get("pytest_failed"):
                failed_tests = pytest_data.get("failed_tests", [])
                result.add_warning(
                    "pytest_check",
                    f"{pytest_data.get('failed', 0)} testes falharam: {failed_tests}"
                )
            elif pytest_data.get("skipped"):
                result.add_warning(
                    "pytest_check",
                    f"Pytest skipped: {pytest_data.get('skipped')}"
                )
            else:
                result.add_passed("pytest_check")

            result.update_metadata("pytest", pytest_data)

        return Result.ok(result)

    async def _diff_check(self, worktree_path: str) -> Result[dict, str]:
        """
        Verifica se arquivos foram modificados (git diff).

        Args:
            worktree_path: Caminho para o worktree

        Returns:
            Result com dict de diff ou erro

        Note:
            BLOQUEANTE: Se nenhum arquivo foi modificado, retorna erro.
        """
        try:
            # Verifica arquivos modificados
            modified = subprocess.check_output(
                ["git", "diff", "--name-only"],
                cwd=worktree_path,
                text=True,
                stderr=subprocess.DEVNULL,
            )

            # Verifica arquivos untracked
            untracked = subprocess.check_output(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=worktree_path,
                text=True,
                stderr=subprocess.DEVNULL,
            )

            modified_files = [f for f in modified.strip().splitlines() if f]
            untracked_files = [f for f in untracked.strip().splitlines() if f]

            all_changes = modified_files + untracked_files

            if not all_changes:
                return Result.err("Agente não modificou nenhum arquivo")

            return Result.ok({
                "modified_count": len(modified_files),
                "untracked_count": len(untracked_files),
                "total_changes": len(all_changes),
                "files": all_changes[:20],  # Limita a 20 arquivos
            })

        except subprocess.CalledProcessError as e:
            return Result.err(f"Erro ao verificar diff: {e}")
        except FileNotFoundError:
            return Result.err("Git não encontrado no worktree")

    async def _syntax_check(self, worktree_path: str) -> Result[dict, str]:
        """
        Valida syntax de arquivos Python (py_compile).

        Args:
            worktree_path: Caminho para o worktree

        Returns:
            Result com dict de status ou erro

        Note:
            BLOQUEANTE: Se há erro de syntax, retorna erro.
        """
        try:
            # Encontra arquivos .py modificados
            result = subprocess.check_output(
                ["git", "diff", "--name-only", "--diff-filter=MR", "*.py"],
                cwd=worktree_path,
                text=True,
                stderr=subprocess.DEVNULL,
            )

            modified_py_files = [f for f in result.strip().splitlines() if f]

            # Encontra arquivos .py untracked
            untracked_result = subprocess.check_output(
                ["git", "ls-files", "--others", "--exclude-standard", "*.py"],
                cwd=worktree_path,
                text=True,
                stderr=subprocess.DEVNULL,
            )

            untracked_py_files = [f for f in untracked_result.strip().splitlines() if f]

            all_py_files = modified_py_files + untracked_py_files

            if not all_py_files:
                # Nenhum arquivo Python modificado
                return Result.ok({"checked": False, "reason": "no_python_files"})

            # Compila cada arquivo para validar syntax
            errors = []
            for py_file in all_py_files:
                full_path = Path(worktree_path) / py_file
                try:
                    with open(full_path, encoding="utf-8") as f:
                        compile(f.read(), py_file, "exec")
                except SyntaxError as e:
                    errors.append(f"{py_file}:{e.lineno}: {e.msg}")

            if errors:
                return Result.err(f"Erros de syntax:\n" + "\n".join(errors))

            return Result.ok({
                "checked": True,
                "files_checked": len(all_py_files),
                "files": all_py_files[:20],
            })

        except subprocess.CalledProcessError:
            # Git command pode falhar se não há .py files
            return Result.ok({"checked": False, "reason": "git_diff_failed"})
        except FileNotFoundError:
            return Result.err("Git não encontrado no worktree")

    async def _pytest_check(self, worktree_path: str) -> Result[dict, str]:
        """
        Roda pytest para validar código (NÃO-BLOQUEANTE).

        Args:
            worktree_path: Caminho para o worktree

        Returns:
            Result com dict de resultados ou erro

        Note:
            NÃO-BLOQUEANTE: Mesmo com falhas, retorna ok com metadata.
            Se não há testes ou pytest não instalado, skip com metadata.
        """
        # Descobre diretórios de teste
        test_dirs = []
        worktree = Path(worktree_path)

        if (worktree / "tests").exists():
            test_dirs.append("tests")
        if (worktree / "test").exists():
            test_dirs.append("test")

        # Se não tem testes, skip
        if not test_dirs:
            return Result.ok({"skipped": "no_tests_found"})

        # Roda pytest
        try:
            proc = await asyncio.create_subprocess_exec(
                "python",
                "-m", "pytest",
                "--tb=short",
                "-v",
                "--no-header",
                "-x",
                *test_dirs,
                cwd=worktree_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout_pytest,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return Result.ok({
                    "timeout": True,
                    "pytest_failed": True,
                    "output": "pytest timeout after {self.timeout_pytest}s"
                })

            output = stdout.decode("utf-8", errors="replace")

            if proc.returncode == 0:
                # Testes passaram
                return Result.ok({
                    "passed": self._extract_passed_count(output),
                    "failed": 0,
                    "duration": self._extract_duration(output),
                    "output": output,
                    "pytest_failed": False,
                })
            else:
                # Testes falharam - NÃO BLOQUEIA
                output += stderr.decode("utf-8", errors="replace")
                failed_tests = self._extract_failed_tests(output)

                return Result.ok({
                    "passed": self._extract_passed_count(output),
                    "failed": len(failed_tests),
                    "failed_tests": failed_tests,
                    "pytest_failed": True,
                    "output": output,
                })

        except FileNotFoundError:
            # Pytest não instalado - skip
            return Result.ok({"skipped": "pytest_not_installed"})

    def _extract_passed_count(self, output: str) -> int:
        """Extrai quantidade de testes que passaram do output."""
        match = re.search(r"(\d+)\s+passed", output)
        return int(match.group(1)) if match else 0

    def _extract_duration(self, output: str) -> float:
        """Extrai duração dos testes do output."""
        match = re.search(r"in\s+([\d.]+)+s", output)
        return float(match.group(1)) if match else 0.0

    def _extract_failed_tests(self, output: str) -> list[str]:
        """Extrai nomes dos testes que falharam."""
        failed = []
        # Padrão: tests/test_foo.py::test_bar FAILED
        matches = re.findall(r"(\S+::\S+)\s+FAILED", output)
        failed.extend(matches)

        # Padrão alternativo: FAILED tests/test_foo.py::test_bar
        matches = re.findall(r"FAILED\s+(\S+::\S+)", output)
        failed.extend(matches)

        return list(set(failed))  # Remove duplicatas


# Import asyncio aqui para evitar import circular
import asyncio
