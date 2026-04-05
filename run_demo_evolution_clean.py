#!/usr/bin/env python
"""
Script limpo para executar Skylab na demo-todo-list.

Este script:
1. Cria um branch limpo
2. Executa Skylab para demo-todo-list
3. Evita problemas com mudanças anteriores

Uso:
    python run_demo_evolution_clean.py
"""

import sys
from pathlib import Path
import subprocess
import shutil

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def reset_target_directory():
    """Reseta o diretório target/ da demo-todo-list para estado limpo."""
    target_dir = Path("src/core/autokarpa/programs/demo-todo-list/target")
    if target_dir.exists():
        # Salvar conteúdo atual
        backup_dir = Path("src/core/autokarpa/programs/demo-todo-list/target.backup")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(target_dir, backup_dir)

        # Recrear target/
        shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copiar __init__.py e arquivos básicos do backup
        if backup_dir.exists():
            for py_file in backup_dir.glob("*.py"):
                shutil.copy2(py_file, target_dir / py_file.name)

        print(f"✅ Target directory reset (backup saved to {backup_dir})")
    else:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "__init__.py").write_text("", encoding="utf-8")
        print("✅ Target directory created")


def create_clean_branch():
    """Cria um branch limpo para o experimento."""
    try:
        # Verificar branch atual
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=False,
        )
        current_branch = result.stdout.strip()

        # Criar branch experimental
        from datetime import datetime
        date_str = datetime.now().strftime("%b%d").lower()
        branch_name = f"demo-todo-{date_str}-0"

        # Criar branch
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            check=True,
            capture_output=True,
        )

        print(f"✅ Created clean branch: {branch_name}")
        return branch_name

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"⚠️ Could not create branch: {e}")
        return None


def main():
    """Executa evolução da demo-todo-list."""
    print("🚀 Iniciando Skylab para demo-todo-list (modo limpo)")
    print("=" * 60)

    # Resetar target directory
    reset_target_directory()

    # Criar branch limpo
    branch = create_clean_branch()

    print()

    # Importar após configurar path
    from core.autokarpa.programs.skylab import run_skylab

    print("🎯 Executando Skylab para demo-todo-list")
    print("=" * 60)
    print()

    try:
        # Executar Skylab para demo-todo-list
        results = run_skylab(
            change_name="demo-todo-list",
            iterations=3,  # Menos iterações para teste rápido
        )

        print()
        print("=" * 60)
        print("🎯 Resultados Finais")
        print(f"   Melhor Code Health: {results['best_code_health']:.4f}")
        print(f"   Melhor Iteração: {results['best_iteration']}")
        print(f"   Total Iterações: {results['total_iterations']}")
        print(f"   Status: {results['status']}")

        if branch:
            print(f"   Branch: {branch}")

        print()

        return results

    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
