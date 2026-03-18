# -*- coding: utf-8 -*-
"""
Refactor Helper - Ferramenta para ajudar em refatorações seguras.

Previne erros como esquecer de atualizar referências ao renomear/remover código.

Uso:
    python scripts/refactor_helper.py --check "nome_da_funcao"
    python scripts/refactor_helper.py --check "NomeClasse" --type class
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List

# Diretórios para buscar (excluindo node_modules, __pycache__, etc.)
SEARCH_DIRS = [
    "src",
    "tests",
    "apps",
    "scripts",
]
EXCLUDE_PATTERNS = [
    "__pycache__",
    "node_modules",
    ".git",
    "dist",
    "build",
    "*.pyc",
]


def grep_references(name: str, search_type: str = "all") -> List[tuple[str, int, str]]:
    """
    Busca referências a um nome em todo o código.

    Returns:
        Lista de (arquivo, linha, conteudo)
    """
    results = []

    # Padrões de busca baseados no tipo
    if search_type == "class":
        patterns = [
            rf"class {name}\b",
            rf": {name}\b",
            rf"\b{name}\(",
            rf"import.*{name}",
            rf"from.*{name}",
        ]
    elif search_type == "function":
        patterns = [
            rf"\b{name}\(",
            rf"def {name}\b",
            rf"\b{name}=",
            rf"import.*{name}",
            rf"from.*{name}",
        ]
    else:  # all
        patterns = [rf"\b{name}\b"]

    # Busca em cada diretório
    for search_dir in SEARCH_DIRS:
        dir_path = Path(search_dir)
        if not dir_path.exists():
            continue

        # Busca usando ripgrep se disponível, senão grep
        for pattern in patterns:
            try:
                # Tenta ripgrep primeiro (mais rápido)
                result = subprocess.run(
                    ["rg", "--no-ignore", "-n", pattern, str(dir_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                lines = result.stdout.split("\n")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                # Fallback para grep
                result = subprocess.run(
                    ["grep", "-rn", pattern, str(dir_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                lines = result.stdout.split("\n")

            # Parse resultados
            for line in lines:
                if not line.strip():
                    continue

                # Formato: arquivo:linha:conteudo
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    filepath = parts[0]
                    linenum = int(parts[1])
                    content = parts[2]

                    # Filtra excludes
                    if any(excl in filepath for excl in EXCLUDE_PATTERNS):
                        continue

                    results.append((filepath, linenum, content))

    # Remove duplicatas e ordena
    results = list(set(results))
    results.sort(key=lambda x: (x[0], x[1]))

    return results


def check_import(module: str) -> bool:
    """Verifica se um módulo pode ser importado."""
    try:
        sys.path.insert(0, "src")
        __import__(module)
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Helper para refatorações seguras",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Verifica referências antes de remover
  python scripts/refactor_helper.py --check "get_trello_kanban_lists_config"

  # Verifica referências de uma classe
  python scripts/refactor_helper.py --check "TrelloKanbanListsConfig" --type class

  # Testa se um módulo pode ser importado
  python scripts/refactor_helper.py --test-import "core.webhooks.application.handlers"
        """,
    )
    parser.add_argument(
        "--check", "-c", help="Nome da função/classe para buscar referências"
    )
    parser.add_argument(
        "--type",
        "-t",
        choices=["all", "class", "function"],
        default="all",
        help="Tipo de busca (default: all)",
    )
    parser.add_argument(
        "--test-import", "-i", help="Testa se um módulo pode ser importado"
    )
    parser.add_argument(
        "--exclude",
        "-e",
        action="append",
        help="Padrões adicionais para excluir (pode usar múltiplas vezes)",
    )

    args = parser.parse_args()

    # Adiciona excludes extras
    if args.exclude:
        EXCLUDE_PATTERNS.extend(args.exclude)

    if args.test_import:
        # Modo teste de import
        print(f"🧪 Testing import: {args.test_import}")
        if check_import(args.test_import):
            print(f"✅ Import OK")
            return 0
        else:
            return 1

    if args.check:
        # Modo check de referências
        name = args.check
        print(f"🔍 Searching for references to: {name}")
        print(f"   Type: {args.type}")
        print()

        results = grep_references(name, args.type)

        if not results:
            print(f"✅ No references found to '{name}'")
            print(f"   Safe to remove/renamed!")
            return 0

        print(f"⚠️  Found {len(results)} references:")
        print()

        # Agrupa por arquivo
        by_file = {}
        for filepath, linenum, content in results:
            if filepath not in by_file:
                by_file[filepath] = []
            by_file[filepath].append((linenum, content))

        # Exibe resultados
        for filepath, matches in sorted(by_file.items()):
            # Tenta converter para path relativo, senão usa absoluto
            try:
                rel_path = Path(filepath).relative_to(Path.cwd())
            except ValueError:
                rel_path = Path(filepath)
            print(f"📄 {rel_path}")
            for linenum, content in sorted(matches):
                print(f"   {linenum:4d}: {content.strip()[:70]}")
            print()

        print()
        print("=" * 60)
        print("⚠️  CHECKLIST ANTES DE REMOVER/RENOMEAR:")
        print("   1. Atualize TODAS as referências acima")
        print("   2. Execute: pytest tests/ -v")
        print("   3. Execute: bash .husky/pre-commit")
        print("   4. Commit com mensagem descritiva")
        print("=" * 60)

        return 1  # Retorna erro para forçar atenção

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
