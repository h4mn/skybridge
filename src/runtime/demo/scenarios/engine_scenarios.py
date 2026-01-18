# -*- coding: utf-8 -*-
"""
Engine Scenarios — Demos que testam a própria Demo Engine.

Demos de validação da infraestrutura da CLI e do sistema de demos.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from kernel import Result
from runtime.demo.base import (
    BaseDemo,
    DemoCategory,
    DemoContext,
    DemoLifecycle,
    DemoFlow,
    DemoFlowType,
    DemoResult,
)
from runtime.demo.registry import DemoRegistry


@DemoRegistry.register
class CLITestSuiteDemo(BaseDemo):
    """
    Demo de Teste Suite - Valida todos os comandos da CLI.

    Testa sistematicamente cada comando da Demo CLI:
    1. list - Lista todas as demos
    2. info - Mostra informações de uma demo específica
    3. stats - Mostra estatísticas
    4. issues - Lista demos por issue
    5. diff - Testa comandos de diff (sem snapshots)
    """

    demo_id = "cli-test-suite"
    demo_name = "CLI Test Suite Demo"
    description = "Testa todos os comandos da Demo CLI sistematicamente"
    category = DemoCategory.ENGINE
    required_configs = []
    estimated_duration_seconds = 30
    tags = ["cli", "testing", "validation", "engine"]
    related_issues = []
    lifecycle = DemoLifecycle.STABLE
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.STANDALONE,
            description="Validação completa da interface de linha de comando",
            actors=["CLI", "DemoEngine", "DemoRegistry"],
            steps=[
                "Testar comando list",
                "Testar comando info",
                "Testar comando stats",
                "Testar comando issues",
                "Testar comando diff",
                "Relatório final",
            ],
            entry_point="cli",
            expected_outcome="Todos os comandos da CLI validados com sucesso",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        # Sem pré-requisitos - testa apenas a CLI local
        return Result.ok(None)

    async def run(self, context: DemoContext) -> DemoResult:
        results = []
        total_tests = 0
        passed_tests = 0

        self.log_info("Iniciando testes da CLI...")

        # Test 1: list
        self.log_progress(1, 5, "Testando comando 'list'...")
        result = await self._test_command_list()
        total_tests += result["total"]
        passed_tests += result["passed"]
        results.append(("list", result))
        await asyncio.sleep(0.5)

        # Test 2: info
        self.log_progress(2, 5, "Testando comando 'info'...")
        result = await self._test_command_info()
        total_tests += result["total"]
        passed_tests += result["passed"]
        results.append(("info", result))
        await asyncio.sleep(0.5)

        # Test 3: stats
        self.log_progress(3, 5, "Testando comando 'stats'...")
        result = await self._test_command_stats()
        total_tests += result["total"]
        passed_tests += result["passed"]
        results.append(("stats", result))
        await asyncio.sleep(0.5)

        # Test 4: issues
        self.log_progress(4, 5, "Testando comando 'issues'...")
        result = await self._test_command_issues()
        total_tests += result["total"]
        passed_tests += result["passed"]
        results.append(("issues", result))
        await asyncio.sleep(0.5)

        # Test 5: diff
        self.log_progress(5, 5, "Testando comando 'diff'...")
        result = await self._test_command_diff()
        total_tests += result["total"]
        passed_tests += result["passed"]
        results.append(("diff", result))

        # Relatório final
        self.log_separator("=")
        print()
        print(f"📊 RELATÓRIO FINAL")
        print(f"   Total de testes: {total_tests}")
        print(f"   Testes passados: {passed_tests}")
        print(f"   Testes falhados: {total_tests - passed_tests}")

        if passed_tests == total_tests:
            self.log_success("✅ TODOS OS TESTES PASSARAM!")
        else:
            self.log_warning(f"⚠️  {total_tests - passed_tests} teste(s) falhou(aram)")

        print()

        # Detalhes por comando
        for cmd, result in results:
            status = "✅" if result["passed"] == result["total"] else "❌"
            print(f"   {status} {cmd}: {result['passed']}/{result['total']} passou")

        print()
        self.log_separator("=")

        return DemoResult.success(
            message=f"Teste concluído: {passed_tests}/{total_tests} passaram",
            tests_total=total_tests,
            tests_passed=passed_tests,
            tests_failed=total_tests - passed_tests,
            results={cmd: res for cmd, res in results},
        )

    async def _run_cli_command(self, args: list[str]) -> tuple[int, str, str]:
        """Executa um comando da CLI e retorna (exit_code, stdout, stderr)."""
        cmd = [sys.executable, "-m", "apps.demo.cli"] + args

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path(__file__).parent.parent.parent.parent.parent,
        )

        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode("utf-8"), stderr.decode("utf-8")

    async def _test_command_list(self) -> dict:
        """Testa o comando list."""
        tests_passed = 0
        tests_total = 0

        # Test 1: list básico
        tests_total += 1
        exit_code, stdout, stderr = await self._run_cli_command(["list"])
        if exit_code == 0:
            self.log_success("  ✓ list básico funcionou")
            tests_passed += 1
        else:
            self.log_error(f"  ✗ list básico falhou: exit={exit_code}")

        # Test 2: list com categoria
        tests_total += 1
        exit_code, stdout, stderr = await self._run_cli_command(["list", "--category", "trello"])
        if exit_code == 0:
            self.log_success("  ✓ list --category funcionou")
            tests_passed += 1
        else:
            self.log_error(f"  ✗ list --category falhou: exit={exit_code}")

        # Test 3: list com flow
        tests_total += 1
        exit_code, stdout, stderr = await self._run_cli_command(["list", "--flow", "card_sync"])
        if exit_code == 0:
            self.log_success("  ✓ list --flow funcionou")
            tests_passed += 1
        else:
            self.log_error(f"  ✗ list --flow falhou: exit={exit_code}")

        return {"total": tests_total, "passed": tests_passed}

    async def _test_command_info(self) -> dict:
        """Testa o comando info."""
        tests_passed = 0
        tests_total = 0

        # Pega uma demo válida
        demos = DemoRegistry.list_all()
        if not demos:
            self.log_warning("  ⚠ Nenhuma demo encontrada para testar info")
            return {"total": 0, "passed": 0}

        first_demo_id = list(demos.keys())[0]

        # Test 1: info válido
        tests_total += 1
        exit_code, stdout, stderr = await self._run_cli_command(["info", first_demo_id])
        if exit_code == 0:
            self.log_success(f"  ✓ info {first_demo_id} funcionou")
            tests_passed += 1
        else:
            self.log_error(f"  ✗ info {first_demo_id} falhou: exit={exit_code}")

        # Test 2: info inválido
        tests_total += 1
        exit_code, stdout, stderr = await self._run_cli_command(["info", "demo-inexistente-xyz"])
        if exit_code != 0:  # Deve falhar
            self.log_success("  ✓ info demo inválido falhou corretamente")
            tests_passed += 1
        else:
            self.log_error("  ✗ info demo inválido não falhou como esperado")

        return {"total": tests_total, "passed": tests_passed}

    async def _test_command_stats(self) -> dict:
        """Testa o comando stats."""
        tests_passed = 0
        tests_total = 0

        # Test 1: stats básico
        tests_total += 1
        exit_code, stdout, stderr = await self._run_cli_command(["stats"])
        if exit_code == 0:
            self.log_success("  ✓ stats funcionou")
            tests_passed += 1
        else:
            self.log_error(f"  ✗ stats falhou: exit={exit_code}")

        return {"total": tests_total, "passed": tests_passed}

    async def _test_command_issues(self) -> dict:
        """Testa o comando issues."""
        tests_passed = 0
        tests_total = 0

        # Test 1: issues --all
        tests_total += 1
        exit_code, stdout, stderr = await self._run_cli_command(["issues", "--all"])
        if exit_code == 0:
            self.log_success("  ✓ issues --all funcionou")
            tests_passed += 1
        else:
            self.log_error(f"  ✗ issues --all falhou: exit={exit_code}")

        # Test 2: issues com número (issue que pode não existir)
        tests_total += 1
        exit_code, stdout, stderr = await self._run_cli_command(["issues", "99999"])
        if exit_code == 0:  # Deve retornar 0 mesmo sem demos
            self.log_success("  ✓ issues 99999 funcionou (sem demos)")
            tests_passed += 1
        else:
            self.log_error(f"  ✗ issues 99999 falhou: exit={exit_code}")

        return {"total": tests_total, "passed": tests_passed}

    async def _test_command_diff(self) -> dict:
        """Testa o comando diff."""
        tests_passed = 0
        tests_total = 0

        # Test 1: diff list (sem snapshots deve funcionar mesmo assim)
        tests_total += 1
        exit_code, stdout, stderr = await self._run_cli_command(["diff", "list", "trello-flow"])
        if exit_code == 0:
            self.log_success("  ✓ diff list funcionou")
            tests_passed += 1
        else:
            self.log_error(f"  ✗ diff list falhou: exit={exit_code}")

        # Test 2: diff show com ID inválido
        tests_total += 1
        exit_code, stdout, stderr = await self._run_cli_command(["diff", "show", "diff-inexistente"])
        if exit_code == 0:  # Retorna 0 mesmo sem diff
            self.log_success("  ✓ diff show diff-inexistente funcionou (sem diff)")
            tests_passed += 1
        else:
            self.log_error(f"  ✗ diff show falhou: exit={exit_code}")

        # Test 3: diff sub-comando inválido
        tests_total += 1
        exit_code, stdout, stderr = await self._run_cli_command(["diff", "invalid-subcommand"])
        if exit_code != 0:  # Deve falhar
            self.log_success("  ✓ diff sub-comando inválido falhou corretamente")
            tests_passed += 1
        else:
            self.log_error("  ✗ diff sub-comando inválido não falhou como esperado")

        return {"total": tests_total, "passed": tests_passed}


@DemoRegistry.register
class DemoEngineValidationDemo(BaseDemo):
    """
    Demo de Validação do Demo Engine.

    Testa componentes internos do Demo Engine:
    - Registry (registro de demos)
    - Engine (execução)
    - Context (contexto de execução)
    - Result (resultados)
    """

    demo_id = "engine-validation"
    demo_name = "Demo Engine Validation"
    description = "Valida componentes internos do Demo Engine"
    category = DemoCategory.ENGINE
    required_configs = []
    estimated_duration_seconds = 15
    tags = ["engine", "validation", "registry", "internals"]
    related_issues = []
    lifecycle = DemoLifecycle.STABLE
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.STANDALONE,
            description="Validação de componentes internos do Demo Engine",
            actors=["DemoRegistry", "DemoEngine", "DemoContext", "DemoResult"],
            steps=[
                "Validar registro de demos",
                "Validar metadados das demos",
                "Validar mapeamento de issues",
                "Validar filtragem por categoria",
            ],
            entry_point="engine",
            expected_outcome="Todos os componentes do engine validados",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return Result.ok(None)

    async def run(self, context: DemoContext) -> DemoResult:
        from runtime.demo.registry import DemoRegistry

        tests_passed = 0
        tests_total = 0

        self.log_info("Validando componentes do Demo Engine...")

        # Test 1: Registro de demos
        self.log_progress(1, 4, "Validando registro de demos...")
        tests_total += 1
        all_demos = DemoRegistry.list_all()
        if all_demos:
            self.log_success(f"  ✓ {len(all_demos)} demos registradas")
            tests_passed += 1
        else:
            self.log_error("  ✗ Nenhuma demo registrada")

        # Test 2: Metadados das demos
        self.log_progress(2, 4, "Validando metadados das demos...")
        tests_total += 1
        invalid_demos = []
        for demo_id, demo_class in all_demos.items():
            demo = demo_class()
            if not demo.demo_id or not demo.demo_name or not demo.description:
                invalid_demos.append(demo_id)

        if not invalid_demos:
            self.log_success("  ✓ Todas as demos têm metadados válidos")
            tests_passed += 1
        else:
            self.log_error(f"  ✗ Demos inválidas: {', '.join(invalid_demos)}")

        # Test 3: Mapeamento de issues
        self.log_progress(3, 4, "Validando mapeamento de issues...")
        tests_total += 1
        issue_mapping = DemoRegistry.get_issue_mapping()
        if issue_mapping is not None:
            self.log_success(f"  ✓ {len(issue_mapping)} issues com demos mapeadas")
            for issue, demo_ids in issue_mapping.items():
                self.log_info(f"     Issue #{issue}: {', '.join(demo_ids)}")
            tests_passed += 1
        else:
            self.log_error("  ✗ Falha ao obter mapeamento de issues")

        # Test 4: Filtragem por categoria
        self.log_progress(4, 4, "Validando filtragem por categoria...")
        tests_total += 1
        try:
            categories = set()
            for demo_class in all_demos.values():
                demo = demo_class()
                categories.add(demo.category.value)

            self.log_success(f"  ✓ {len(categories)} categorias encontradas: {', '.join(sorted(categories))}")
            tests_passed += 1
        except Exception as e:
            self.log_error(f"  ✗ Erro ao filtrar por categoria: {e}")

        # Relatório
        self.log_separator("=")
        print()
        print(f"📊 VALIDAÇÃO DO ENGINE")
        print(f"   Testes passados: {tests_passed}/{tests_total}")

        if tests_passed == tests_total:
            self.log_success("✅ ENGINE VALIDADO!")
        else:
            self.log_warning(f"⚠️  {tests_total - tests_passed} teste(s) falhou(aram)")

        print()
        self.log_separator("=")

        return DemoResult.success(
            message=f"Validação do engine: {tests_passed}/{tests_total} testes passaram",
            tests_total=tests_total,
            tests_passed=tests_passed,
            demos_registered=len(all_demos),
            categories_found=len(categories),
        )
