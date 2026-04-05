#!/usr/bin/env python
"""
Script para executar Skylab na demo-todo-list com mais iterações.

Uso:
    python run_demo_evolution_more.py
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.autokarpa.programs.skylab import run_skylab


def main():
    """Executa evolução da demo-todo-list com mais iterações."""
    print("🚀 Iniciando Skylab para demo-todo-list (mais iterações)")
    print("=" * 60)
    print()

    # Executar Skylab para demo-todo-list com mais iterações
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

    # Verificar se atingiu thresholds
    mutation_threshold = 0.80
    pbt_threshold = 1.0  # 1000 casos passando
    code_health_threshold = 0.70

    print("📊 Thresholds:")
    print(f"   Mutation Score: {results.get('mutation', 'N/A')} (meta: > {mutation_threshold})")
    print(f"   PBT Score: {results.get('pbt', 'N/A')} (meta: {pbt_threshold})")
    print(f"   Code Health: {results['best_code_health']:.4f} (meta: > {code_health_threshold})")
    print()

    if results['best_code_health'] > code_health_threshold:
        print("✅ DEMO COMPLETA: Code Health acima do threshold!")
    else:
        print("⚠️  Demo precisa de mais iterações para atingir threshold")

    return results


if __name__ == "__main__":
    main()
