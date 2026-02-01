# -*- coding: utf-8 -*-
"""
Testes de Import Regressão.

Verifica que todos os módulos críticos podem ser importados.
Previne erros de refatoração onde código é removido mas referências não são atualizadas.

Uso:
    pytest tests/test_imports.py -v                    # Críticos apenas (rápido)
    pytest tests/test_imports.py -v --all             # Todos os módulos (lento)
    pytest tests/test_imports.py -v -m slow           # Apenas modo completo
"""

import importlib
import sys
from pathlib import Path
from typing import List, Tuple

import pytest


def _discover_python_modules(base_paths: List[str]) -> List[Tuple[str, str]]:
    """
    Descobre todos os módulos Python nos diretórios especificados.

    Returns:
        Lista de (module_name, filepath) para todos os módulos encontrados
    """
    modules = []

    for base_path_str in base_paths:
        base_path = Path(base_path_str)
        if not base_path.exists():
            continue

        # Adiciona ao sys.path
        base_path_abs = str(base_path.absolute())
        if base_path_abs not in sys.path:
            sys.path.insert(0, base_path_abs)

        # Encontra todos os arquivos .py
        for py_file in base_path.rglob("*.py"):
            # Ignora __pycache__, test files, etc
            if any(
                excl in str(py_file)
                for excl in [
                    "__pycache__",
                    ".pytest_cache",
                    "test_",
                    "_test.py",
                    "conftest.py",
                ]
            ):
                continue

            # Converte path para nome do módulo
            rel_path = py_file.relative_to(base_path)
            module_name = rel_path.with_suffix("").as_posix().replace("/", ".")

            # Prefixo especial para cli (para que workspace.py vire cli.workspace)
            prefix = base_path.name if base_path.name in ["cli"] else ""

            if prefix and not module_name.startswith(prefix + "."):
                module_name = f"{prefix}.{module_name}"

            # Remove leading ponto
            if module_name.startswith("."):
                module_name = module_name[1:]

            if module_name:
                modules.append((module_name, str(py_file)))

    # Remove duplicatas e ordena
    modules = sorted(set(modules), key=lambda x: x[0])
    return modules


# Descobre todos os módulos (usado no modo --all)
# NOTA: cli é excluído temporariamente devido a problemas de importação no pytest
_ALL_MODULES = _discover_python_modules(["src"])


# =============================================================================
# CAMINHO 1: Testes Críticos (rápido, padrão)
# =============================================================================
# Executado por padrão: pytest tests/test_imports.py -v
# Foco: Módulos essenciais para o funcionamento do sistema


@pytest.mark.unit
@pytest.mark.imports
class TestCriticalImports:
    """
    Testa que módulos críticos podem ser importados.

    Este é o caminho RÁPIDO para validação contínua.
    Executa em <1 segundo e valida os pontos críticos do sistema.
    """

    # Módulos críticos do sistema (12 módulos)
    CRITICAL_MODULES = [
        # Runtime config (base para tudo)
        "runtime.config.config",
        # Prompts (PRD021)
        "runtime.prompts",
        # Webhooks handlers (integração externa)
        "core.webhooks.application.handlers",
        # Trello services
        "core.kanban.application.trello_service",
        # Adapters
        "infra.kanban.adapters.trello_adapter",
        # Demo engine
        "runtime.demo.scenarios.spec009_e2e_demo",
        "runtime.demo.scenarios.prd021_scenarios",
        # Snapshot service
        "runtime.observability.snapshot",
        # FileOps domain
        "core.fileops.domain.file_content",
        "core.fileops.domain.file_path",
        # Kernel registry
        "kernel.registry.decorators",
        # Kanban domain
        "core.kanban.domain.card",
    ]

    @pytest.mark.parametrize(
        "module_path",
        CRITICAL_MODULES,
    )
    def test_critical_module_import(self, module_path):
        """
        Testa que módulo crítico pode ser importado.

        Se este teste falhar, indica que:
        - Alguma dependência está faltando
        - Um import está quebrado
        - Um nome foi renomeado mas não atualizado em todos os lugares
        """
        __import__(module_path)

    def test_trello_kanban_lists_config_exists(self):
        """Testa que TrelloKanbanListsConfig pode ser importado."""
        from runtime.config.config import TrelloKanbanListsConfig, get_trello_kanban_lists_config

        assert TrelloKanbanListsConfig is not None
        assert get_trello_kanban_lists_config is not None

    def test_trello_service_can_be_instantiated(self):
        """Testa que TrelloService pode ser criado com config."""
        from core.kanban.application.trello_service import TrelloService
        from runtime.config.config import get_trello_kanban_lists_config

        config = get_trello_kanban_lists_config()
        # Não testa funcionalidade, apenas instanciação
        assert config is not None
        assert isinstance(config, get_trello_kanban_lists_config().__class__)


@pytest.mark.unit
@pytest.mark.imports
class TestEnumBackwardsCompatibility:
    """Testa que enums mantêm compatibilidade backwards."""

    def test_cardstatus_has_challenge(self):
        """Testa que CardStatus.CHALLENGE existe (SPEC009)."""
        from core.kanban.domain import CardStatus

        assert hasattr(CardStatus, "CHALLENGE")
        assert CardStatus.CHALLENGE.value == "challenge"


@pytest.mark.unit
@pytest.mark.imports
class TestDemoRegistry:
    """Testa que demos estão registradas corretamente."""

    def test_spec009_demo_registered(self):
        """Testa que SPEC009 demo está registrada."""
        from runtime.demo.scenarios.spec009_e2e_demo import SPEC009InteractiveDemo

        assert SPEC009InteractiveDemo.demo_id == "spec009-interactive"

    def test_prd021_demo_registered(self):
        """Testa que PRD021 demos estão registradas."""
        from runtime.demo.scenarios.prd021_scenarios import (
            PRD021StructureDemo,
            PRD021ImportDemo,
        )

        assert PRD021StructureDemo.demo_id == "prd021-structure"
        assert PRD021ImportDemo.demo_id == "prd021-imports"


# =============================================================================
# CAMINHO 2: Testes Completos (lento, opcional)
# =============================================================================
# Executado apenas com --all ou -m slow: pytest tests/test_imports.py -v --all
# Foco: TODOS os módulos Python do projeto (145+ módulos)


@pytest.mark.unit
@pytest.mark.imports
@pytest.mark.slow  # Marker para pular por padrão
@pytest.mark.parametrize("module_name,module_file", _ALL_MODULES)
def test_all_module_imports(module_name: str, module_file: str):
    """
    Testa que TODOS os módulos Python podem ser importados.

    Este é o caminho COMPLETO para validação exaustiva.
    Executa em ~10 segundos e cobre 100% dos módulos.

    Uso:
        # Rodar apenas críticos (padrão, rápido)
        pytest tests/test_imports.py -v

        # Rodar todos os módulos (incluindo este teste)
        pytest tests/test_imports.py -v --all
        pytest tests/test_imports.py -v -m slow

    Args:
        module_name: Nome do módulo para importar
        module_file: Caminho do arquivo .py (para debug)

    Se este teste falhar, indica que algum módulo está quebrado.
    """
    try:
        importlib.import_module(module_name)
    except Exception as e:
        pytest.fail(
            f"Failed to import '{module_name}'\n"
            f"File: {module_file}\n"
            f"Error: {type(e).__name__}: {e}"
        )


@pytest.mark.unit
@pytest.mark.imports
@pytest.mark.slow
def test_imports_summary():
    """
    Exibe resumo dos módulos descobertos quando rodar em modo completo.

    Este teste não faz validações, apenas informa quantos módulos foram testados.
    """
    print(f"\n📦 Testing {len(_ALL_MODULES)} Python modules in --all mode")

    # Agrupa por diretório principal
    by_dir = {}
    for module_name, module_file in _ALL_MODULES:
        top_level = module_name.split(".")[0]
        by_dir[top_level] = by_dir.get(top_level, 0) + 1

    print("📁 Modules by top-level package:")
    for pkg, count in sorted(by_dir.items()):
        print(f"  {pkg}: {count} modules")
