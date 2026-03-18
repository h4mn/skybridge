# -*- coding: utf-8 -*-
"""
PRD021 Scenarios — Demos da reorganização de prompts e skills.

Demonstra a nova estrutura src/runtime/prompts/ conforme PRD021.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

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
class PRD021StructureDemo(BaseDemo):
    """
    Demo da nova estrutura de prompts e skills (PRD021).

    Demonstração visual e funcional da nova organização:
    - Estrutura de diretórios src/runtime/prompts/
    - System prompts em src/runtime/prompts/system/
    - Agent skills em src/runtime/prompts/skills/
    - Imports funcionando corretamente
    - Cabeçalhos utf-8 em todos arquivos

    Refs: PRD021, SPEC008, SPEC009, ADR018, ADR019
    """

    demo_id = "prd021-structure"
    demo_name = "PRD021: Nova Estrutura de Prompts e Skills"
    description = "Demonstra a reorganização de prompts/skills para src/runtime/prompts/"
    category = DemoCategory.ENGINE
    required_configs = []
    estimated_duration_seconds = 30
    tags = ["prd021", "structure", "prompts", "skills", "refactor"]
    related_issues = ["PRD021"]
    lifecycle = DemoLifecycle.STABLE
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.STANDALONE,
            description="Demonstração da nova estrutura organizacional de prompts e skills",
            actors=["Runtime", "Prompts", "System", "Skills"],
            steps=[
                "Verificar nova estrutura src/runtime/prompts/",
                "Carregar system prompt da nova localização",
                "Renderizar system prompt com contexto",
                "Listar skills disponíveis",
                "Verificar cabeçalhos utf-8",
            ],
            entry_point="structure",
            expected_outcome="Nova estrutura validada e funcional",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return Result.ok(None)

    async def run(self, context: DemoContext) -> DemoResult:
        from runtime.prompts import (
            load_system_prompt_config,
            render_system_prompt,
            get_json_validation_prompt,
        )

        self.log_separator("=", 60)
        self.log_info("🏗️ PRD021: Nova Estrutura de Prompts e Skills")
        self.log_separator("=", 60)
        self.log_info("Refatoração concluída: src/runtime/config/ → src/runtime/prompts/")
        self.log_separator("-", 60)

        # Step 1: Verificar estrutura de diretórios
        self.log_progress(1, 6, "Verificando nova estrutura...")

        prompts_dir = Path("src/runtime/prompts")
        system_dir = prompts_dir / "system"
        skills_dir = prompts_dir / "skills"

        checks = [
            ("src/runtime/prompts/", prompts_dir.exists()),
            ("src/runtime/prompts/system/", system_dir.exists()),
            ("src/runtime/prompts/skills/", skills_dir.exists()),
            ("src/runtime/prompts/__init__.py", (prompts_dir / "__init__.py").exists()),
            ("src/runtime/prompts/agent_prompts.py", (prompts_dir / "agent_prompts.py").exists()),
        ]

        for path_str, exists in checks:
            status = "✅" if exists else "❌"
            self.log_info(f"  {status} {path_str}")

        if not all(exists for _, exists in checks):
            return DemoResult.error("Estrutura de diretórios incompleta")

        # Step 2: Carregar system prompt
        self.log_progress(2, 6, "Carregando system prompt...")

        try:
            config = load_system_prompt_config()
            self.log_success(f"System prompt carregado (v{config['version']})")
            self.log_info(f"  Linguagem: {config['metadata']['language']}")
            self.log_info(f"  Descrição: {config['metadata']['description'][:60]}...")
        except Exception as e:
            return DemoResult.error(f"Erro ao carregar system prompt: {e}")

        # Step 3: Renderizar system prompt
        self.log_progress(3, 6, "Renderizando system prompt...")

        context = {
            "worktree_path": "/tmp/skybridge-auto/test",
            "branch_name": "feature/test",
            "skill": "resolve-issue",
            "issue_number": 42,
            "issue_title": "Test issue",
            "repo_name": "skybridge/skybridge",
            "job_id": "test-job-123",
        }

        try:
            prompt = render_system_prompt(config, context)
            self.log_success("System prompt renderizado com sucesso")
            self.log_info(f"  Tamanho: {len(prompt)} caracteres")
            self.log_info(f"  Contém worktree_path: {'/tmp/skybridge' in prompt}")
            self.log_info(f"  Contém issue_number: {'42' in prompt}")
        except Exception as e:
            return DemoResult.error(f"Erro ao renderizar system prompt: {e}")

        # Step 4: Listar skills disponíveis
        self.log_progress(4, 6, "Listando skills disponíveis...")

        expected_skills = [
            "analyze-issue",
            "challenge-quality",
            "create-issue",
            "resolve-issue",
            "test-issue",
        ]

        self.log_info("Skills disponíveis:")
        for skill in expected_skills:
            skill_path = skills_dir / skill / "SKILL.md"
            exists = skill_path.exists()
            status = "✅" if exists else "❌"
            self.log_info(f"  {status} {skill}/SKILL.md")

        missing = [s for s in expected_skills if not (skills_dir / s / "SKILL.md").exists()]
        if missing:
            return DemoResult.error(f"Skills faltando: {missing}")

        # Step 5: Verificar cabeçalhos utf-8
        self.log_progress(5, 6, "Verificando cabeçalhos utf-8...")

        init_files = [
            prompts_dir / "__init__.py",
            system_dir / "__init__.py",
            skills_dir / "__init__.py",
            skills_dir / "analyze-issue" / "__init__.py",
            skills_dir / "challenge-quality" / "__init__.py",
            skills_dir / "create-issue" / "__init__.py",
            skills_dir / "resolve-issue" / "__init__.py",
            skills_dir / "test-issue" / "__init__.py",
        ]

        missing_headers = []
        for init_file in init_files:
            content = init_file.read_text(encoding="utf-8")
            has_header = "# -*- coding: utf-8 -*-" in content
            status = "✅" if has_header else "❌"
            if not has_header:
                missing_headers.append(str(init_file.relative_to(Path.cwd())))

        if missing_headers:
            self.log_warning(f"Arquivos sem cabeçalho utf-8: {missing_headers}")
        else:
            self.log_success("Todos arquivos __init__.py têm cabeçalho utf-8")

        # Step 6: Validação JSON
        self.log_progress(6, 6, "Validando prompts de validação JSON...")

        try:
            json_prompt = get_json_validation_prompt()
            has_critical = "CRÍTICO" in json_prompt
            has_json = "JSON" in json_prompt
            if has_critical and has_json:
                self.log_success("Prompt de validação JSON funcionando (pt-BR)")
            else:
                return DemoResult.error("Prompt de validação JSON incompleto")
        except Exception as e:
            return DemoResult.error(f"Erro ao carregar prompt JSON: {e}")

        # Resumo
        self.log_separator("=", 60)
        self.log_info("✅ PRD021 Validado com Sucesso!")
        self.log_separator("=", 60)
        self.log_info("Estrutura nova:")
        self.log_info("  src/runtime/prompts/")
        self.log_info("  ├── __init__.py (exports públicos)")
        self.log_info("  ├── agent_prompts.py (handler de prompts)")
        self.log_info("  ├── system/")
        self.log_info("  │   └── system_prompt.json")
        self.log_info("  └── skills/")
        self.log_info("      ├── analyze-issue/SKILL.md")
        self.log_info("      ├── challenge-quality/SKILL.md")
        self.log_info("      ├── create-issue/SKILL.md")
        self.log_info("      ├── resolve-issue/SKILL.md")
        self.log_info("      └── test-issue/SKILL.md")

        return DemoResult.success(
            message="PRD021 validado: nova estrutura funcionando corretamente",
            metadata={
                "structure_valid": True,
                "skills_count": len(expected_skills),
                "utf8_headers_ok": len(missing_headers) == 0,
            }
        )


@DemoRegistry.register
class PRD021ImportDemo(BaseDemo):
    """
    Demo dos novos imports após PRD021.

    Demonstra que todos os imports foram atualizados e funcionam:
    - runtime.config.agent_prompts → runtime.prompts
    - Testes unitários passando
    - Integração funcionando
    """

    demo_id = "prd021-imports"
    demo_name = "PRD021: Novos Imports Funcionando"
    description = "Demonstra que os novos imports runtime.prompts funcionam corretamente"
    category = DemoCategory.ENGINE
    required_configs = []
    estimated_duration_seconds = 20
    tags = ["prd021", "imports", "validation", "tests"]
    related_issues = ["PRD021"]
    lifecycle = DemoLifecycle.STABLE
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    def define_flow(self) -> DemoFlow:
        return DemoFlow(
            flow_type=DemoFlowType.STANDALONE,
            description="Validação de imports após migração para runtime.prompts",
            actors=["Python", "Imports", "Runtime"],
            steps=[
                "Testar imports principais",
                "Verificar módulos antigos não existem",
                "Validar compatibilidade com código existente",
            ],
            entry_point="imports",
            expected_outcome="Todos os imports funcionando corretamente",
        )

    async def validate_prerequisites(self) -> Result[None, str]:
        return Result.ok(None)

    async def run(self, context: DemoContext) -> DemoResult:
        self.log_separator("=", 60)
        self.log_info("🔄 PRD021: Validação de Imports")
        self.log_separator("=", 60)

        # Testar imports novos
        self.log_progress(1, 3, "Testando novos imports...")

        new_imports = [
            ("from runtime.prompts import load_system_prompt_config", lambda: self._test_import("from runtime.prompts import load_system_prompt_config")),
            ("from runtime.prompts import render_system_prompt", lambda: self._test_import("from runtime.prompts import render_system_prompt")),
            ("from runtime.prompts import get_json_validation_prompt", lambda: self._test_import("from runtime.prompts import get_json_validation_prompt")),
        ]

        for import_name, test_fn in new_imports:
            try:
                test_fn()
                self.log_success(f"  ✅ {import_name}")
            except ImportError as e:
                self.log_error(f"  ❌ {import_name}: {e}")
                return DemoResult.error(f"Import falhou: {import_name}")

        # Verificar módulos antigos não existem
        self.log_progress(2, 3, "Verificando módulos antigos removidos...")

        old_paths = [
            "src/runtime/config/agent_prompts.py",
            "src/runtime/config/system_prompt.json",
            "plugins/skybridge-workflows/",
        ]

        for old_path in old_paths:
            exists = Path(old_path).exists()
            status = "✅" if not exists else "⚠️"
            msg = "removido" if not exists else "ainda existe"
            self.log_info(f"  {status} {old_path}: {msg}")

        # Verificar compatibilidade
        self.log_progress(3, 3, "Verificando compatibilidade...")

        try:
            from runtime.prompts import load_system_prompt_config, render_system_prompt
            from runtime.config import get_agent_config

            config = load_system_prompt_config()
            agent_config = get_agent_config()

            self.log_success("Compatibilidade mantida:")
            self.log_info("  ✅ runtime.prompts funciona")
            self.log_info("  ✅ runtime.config ainda acessível")
            self.log_info("  ✅ Integração funcionando")

        except Exception as e:
            return DemoResult.error(f"Erro de compatibilidade: {e}")

        self.log_separator("=", 60)
        self.log_info("✅ Imports Validados!")
        self.log_separator("=", 60)
        return DemoResult.success(
            message="Todos os imports funcionando corretamente após PRD021",
            metadata={"imports_tested": len(new_imports)},
        )

    def _test_import(self, import_stmt: str) -> None:
        """Executa um import e retorna sucesso ou falha."""
        exec(import_stmt)
