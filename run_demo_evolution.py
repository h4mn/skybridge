#!/usr/bin/env python
"""
Script para executar Skylab na demo-todo-list.

Uso:
    python run_demo_evolution.py

Este script executa o loop de evolução do Skylab para a change demo-todo-list.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.autokarpa.programs.skylab import run_skylab


def main():
    """Executa evolução da demo-todo-list."""
    print("🚀 Iniciando Skylab para demo-todo-list")
    print("=" * 60)
    print()

    # Executar Skylab para demo-todo-list
    # Iterações: 7 (conforme Ralph Loop)
    results = run_skylab(
        change_name="demo-todo-list",
        iterations=7,
    )

    print()
    print("=" * 60)
    print("🎯 Resultados Finais")
    print(f"   Melhor Code Health: {results['best_code_health']:.4f}")
    print(f"   Melhor Iteração: {results['best_iteration']}")
    print(f"   Total Iterações: {results['total_iterations']}")
    print(f"   Status: {results['status']}")
    print()

    return results


if __name__ == "__main__":
    main()
