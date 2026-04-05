#!/usr/bin/env python
"""
Script para debugar test_runner da demo-todo-list.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.autokarpa.programs.skylab.core.test_runner import run_pytest

# Testar com demo-todo-list
test_dir = Path("src/core/autokarpa/programs/demo-todo-list/tests")
target_dir = Path("src/core/autokarpa/programs/demo-todo-list/target")

print("🔍 Testando pytest com demo-todo-list")
print(f"   test_dir: {test_dir}")
print(f"   target_dir: {target_dir}")
print()

results = run_pytest(test_dir, target_dir=target_dir, verbose=True)

print()
print("📊 Resultados:")
print(f"   passed: {results.get('passed', 0)}")
print(f"   failed: {results.get('failed', 0)}")
print(f"   total: {results.get('total', 0)}")
print(f"   success: {results.get('success', False)}")
print(f"   error: {results.get('error', 'None')}")
print()

if 'output' in results:
    print("📝 Output:")
    print(results['output'])
