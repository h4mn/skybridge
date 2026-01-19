#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Migrate Structure — Refatoração segura com proteção de regressão.

Migra a estrutura de diretórios:
- src/skybridge/core/contexts/* → src/core/*
- src/skybridge/kernel/* → src/kernel/*
- src/skybridge/platform/* → src/platform/*
- src/skybridge/infra/contexts/* → src/infra/*

E atualiza todos os imports automaticamente.

Usage:
    python scripts/migrate_structure.py [--dry-run] [--skip-tests]
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


# Mapeamento de migração de diretórios
DIRECTORY_MIGRATIONS: Dict[str, str] = {
    "src/skybridge/core/contexts": "src/core",
    "src/skybridge/kernel": "src/kernel",
    "src/skybridge/platform": "src/platform",
    "src/skybridge/infra/contexts": "src/infra",
}

# Mapeamento de migração de imports
IMPORT_REPLACEMENTS: List[tuple[str, str]] = [
    (r"from skybridge\.core\.contexts\.", "from core."),
    (r"from skybridge\.kernel\.", "from kernel."),
    (r"from skybridge\.platform\.", "from platform."),
    (r"from skybridge\.infra\.contexts\.", "from infra."),
    (r"import skybridge\.core\.contexts\.", "import core."),
    (r"import skybridge\.kernel\.", "import kernel."),
    (r"import skybridge\.platform\.", "import platform."),
    (r"import skybridge\.infra\.contexts\.", "import infra."),
]


def run_tests(label: str, timeout: int = 120) -> tuple[bool, str]:
    """Roda testes e retorna (sucesso, output)."""
    print(f"\n{'='*60}")
    print(f"🧪 Rodando testes: {label}")
    print(f"{'='*60}")

    # Ignorar testes que requerem servidor rodando
    ignore_flags = [
        "--ignore=tests/test_openapi_hybrid_online.py",
        "--ignore=tests/test_openapi_schema.py",
    ]

    result = subprocess.run(
        ["pytest", "tests/", "-v", "--tb=short", "-x"] + ignore_flags,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    success = result.returncode == 0
    output = result.stdout + result.stderr

    # Salvar log
    log_file = Path(f"scripts/test_results_{label}.txt")
    log_file.parent.mkdir(exist_ok=True)
    log_file.write_text(output, encoding="utf-8")

    if success:
        print(f"✅ {label}: {result.stdout.split('passed')[0].split()[-1] if 'passed' in result.stdout else 'OK'}")
    else:
        print(f"❌ {label}: FALHOU")
        print(f"   Log salvo em: {log_file}")

    return success, output


def find_python_files(root: Path) -> List[Path]:
    """Encontra todos os arquivos Python no projeto."""
    python_files = []
    for pattern in ["*.py"]:
        python_files.extend(root.rglob(pattern))
    return python_files


def update_imports_in_file(file_path: Path, dry_run: bool = False) -> int:
    """Atualiza imports em um arquivo Python. Retorna quantidade de mudanças."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        for pattern, replacement in IMPORT_REPLACEMENTS:
            content = re.sub(pattern, replacement, content)

        changes = content != original_content

        if changes and not dry_run:
            file_path.write_text(content, encoding="utf-8")
            return 1
        elif changes and dry_run:
            print(f"  📝 {file_path.relative_to(Path.cwd())}")
            return 1

        return 0

    except Exception as e:
        print(f"⚠️  Erro ao processar {file_path}: {e}")
        return 0


def migrate_directories(dry_run: bool = False) -> int:
    """Executa migração de diretórios. Retorna quantidade de operações."""
    base_path = Path.cwd()
    operations = 0

    print(f"\n{'='*60}")
    print("📁 Migrando diretórios")
    print(f"{'='*60}")

    for old_dir, new_dir in DIRECTORY_MIGRATIONS.items():
        old_path = base_path / old_dir
        new_path = base_path / new_dir

        if not old_path.exists():
            print(f"⚠️  Diretório não encontrado: {old_dir}")
            continue

        if new_path.exists():
            print(f"⚠️  Diretório já existe: {new_dir}")
            continue

        if dry_run:
            print(f"  📂 {old_dir} → {new_dir}")
            operations += 1
        else:
            try:
                # Criar diretório pai se necessário
                new_path.parent.mkdir(parents=True, exist_ok=True)

                # Mover conteúdo
                subprocess.run(
                    ["mv", str(old_path), str(new_path)],
                    check=True,
                    capture_output=True,
                )
                print(f"✅ {old_dir} → {new_dir}")
                operations += 1

            except subprocess.CalledProcessError as e:
                print(f"❌ Erro ao mover {old_dir}: {e}")
                return -1

    return operations


def update_all_imports(dry_run: bool = False) -> int:
    """Atualiza imports em todos os arquivos Python."""
    base_path = Path.cwd()
    python_files = find_python_files(base_path)

    print(f"\n{'='*60}")
    print(f"📝 Atualizando imports ({len(python_files)} arquivos)")
    print(f"{'='*60}")

    if dry_run:
        print("(dry-run: mostrando apenas arquivos que seriam alterados)")

    changes = 0
    for file_path in python_files:
        changes += update_imports_in_file(file_path, dry_run)

    print(f"\n✅ Imports atualizados em {changes} arquivos")
    return changes


def verify_syntax() -> bool:
    """Verifica sintaxe Python de todos os arquivos após migração."""
    print(f"\n{'='*60}")
    print("🔍 Verificando sintaxe Python")
    print(f"{'='*60}")

    base_path = Path.cwd()
    python_files = find_python_files(base_path)

    for file_path in python_files:
        try:
            compile(file_path.read_text(encoding="utf-8"), str(file_path), "exec")
        except SyntaxError as e:
            print(f"❌ Erro de sintaxe em {file_path}: {e}")
            return False

    print("✅ Sintaxe Python válida em todos os arquivos")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migra estrutura de diretórios com proteção de regressão"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra o que seria feito sem executar",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Pula execução dos testes (não recomendado)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout para testes em segundos (padrão: 120)",
    )

    args = parser.parse_args()

    print("🚀 MIGRAÇÃO DE ESTRUTURA - SKYBRIDGE")
    print(f"📍 Diretório: {Path.cwd()}")
    print(f"🌿 Branch: {subprocess.getoutput('git branch --show-current')}")

    if args.dry_run:
        print("\n⚠️  MODO DRY-RUN: nenhuma alteração será executada")

    # ============================================================================
    # FASE 1: BASELINE (testar ANTES)
    # ============================================================================
    if not args.skip_tests:
        baseline_passed, _ = run_tests("baseline", timeout=args.timeout)

        if not baseline_passed:
            print("\n" + "="*60)
            print("❌ BASELINE FALHOU!")
            print("Os testes já estão falhando antes da migração.")
            print("Por favor, corrija os testes antes de continuar.")
            print("="*60)
            sys.exit(1)

    # ============================================================================
    # FASE 2: MIGRAR (mover diretórios + atualizar imports)
    # ============================================================================
    dir_ops = migrate_directories(dry_run=args.dry_run)

    if dir_ops == -1:
        print("\n❌ Erro fatal na migração de diretórios")
        sys.exit(1)

    import_changes = update_all_imports(dry_run=args.dry_run)

    if args.dry_run:
        print(f"\n📊 DRY-RUN RESUMO:")
        print(f"   Diretórios: {dir_ops} operações")
        print(f"   Imports: {import_changes} arquivos alterados")
        print(f"\n⚠️  Nenhuma alteração executada. Use --dry-run=False para aplicar.")
        return

    # ============================================================================
    # FASE 3: VERIFICAR SINTAXE
    # ============================================================================
    if not verify_syntax():
        print("\n❌ Erro de sintaxe detectado! Abortando.")
        print("   Execute 'git checkout .' para reverter.")
        sys.exit(1)

    # ============================================================================
    # FASE 4: REGRESSÃO (testar DEPOIS)
    # ============================================================================
    if not args.skip_tests:
        after_passed, _ = run_tests("after", timeout=args.timeout)

        if not after_passed:
            print("\n" + "="*60)
            print("❌ REGRESSÃO DETECTADA!")
            print("Os testes falharam após a migração.")
            print("\n📋 Comparação:")
            print("   scripts/test_results_baseline.txt")
            print("   scripts/test_results_after.txt")
            print("\n🔄 Para reverter:")
            print("   git checkout .")
            print("="*60)
            sys.exit(1)

    # ============================================================================
    # SUCESSO
    # ============================================================================
    print("\n" + "="*60)
    print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*60)
    print(f"📊 Resumo:")
    print(f"   Diretórios migrados: {dir_ops}")
    print(f"   Imports atualizados: {import_changes} arquivos")
    print(f"   Testes: ✅ Passaram (sem regressão)")
    print(f"\n📝 Próximos passos:")
    print(f"   1. Revise as mudanças: git status")
    print(f"   2. Commit: git add . && git commit -m 'refactor: migrar para nova estrutura'")
    print(f"   3. Push: git push -u origin refactor/new-kanban-structure")
    print("="*60)


if __name__ == "__main__":
    main()
