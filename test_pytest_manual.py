#!/usr/bin/env python
"""
Script para testar pytest manualmente da demo-todo-list.
"""

import subprocess
import sys
from pathlib import Path

# Testar pytest manualmente
test_dir = Path("src/core/autokarpa/programs/demo-todo-list/tests")
parent_dir = Path("src/core/autokarpa/programs/demo-todo-list")

# Configurar environment
import os
env = os.environ.copy()

# Adicionar diretório ao PYTHONPATH
current_path = env.get('PYTHONPATH', '')
target_path = str(parent_dir)  # demo-todo-list/
if current_path:
    new_path = f"{target_path}{os.pathsep}{current_path}"
else:
    new_path = target_path
env['PYTHONPATH'] = new_path

print("🔍 Configuração:")
print(f"   PYTHONPATH: {env['PYTHONPATH']}")
print(f"   test_dir: {test_dir}")
print(f"   cwd: {Path.cwd()}")
print()

# Executar pytest
result = subprocess.run(
    [
        sys.executable, "-m", "pytest",
        str(test_dir),
        "-v",  # Verbose para ver erros
    ],
    capture_output=True,
    text=True,
    cwd=str(Path.cwd()),
    env=env,
)

print("STDOUT:")
print(result.stdout)
print()
print("STDERR:")
print(result.stderr)
