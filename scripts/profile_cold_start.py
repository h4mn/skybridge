# coding: utf-8
"""
Profile do cold start para identificar o que está demorando.
"""

import os
import sys
import time
from pathlib import Path

# Adiciona src ao path
project_root = Path(__file__).parent.parent
src_path = str(project_root / "src")
sys.path.insert(0, src_path)

# Configura variáveis de ambiente
os.environ["USE_RAG_MEMORY"] = "true"
os.environ["USE_CLAUDE_CHAT"] = "true"
os.environ["USE_TEXTUAL_UI"] = "true"

print("=== Cold Start Profiling ===\n")

times = {}

# MARCO 1: Início absoluto
t0 = time.perf_counter()
print(f"[{0:6.0f}ms] INÍCIO - script começou")

# MARCO 2: Depois dos imports leves
import os as os_import
import sys as sys_import
import time as time_import
from pathlib import Path as Path_import
t1 = time.perf_counter()
print(f"[{(t1-t0)*1000:6.0f}ms] Imports leves (os, sys, time, Path)")

# MARCO 3: Depois de dotenv
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass
t2 = time.perf_counter()
print(f"[{(t2-t1)*1000:6.0f}ms] dotenv.load_dotenv()")

# MARCO 4: Import do módulo bootstrap (não a função run)
print(f"\n--- Importando core.sky.bootstrap ---")
from core.sky import bootstrap
t3 = time.perf_counter()
print(f"[{(t3-t2)*1000:6.0f}ms] from core.sky import bootstrap")

# MARCO 5: Import de Rich
print(f"\n--- Importando Rich ---")
from rich.console import Console
t4 = time.perf_counter()
print(f"[{(t4-t3)*1000:6.0f}ms] from rich.console import Console")

# MARCO 6: Primeiro print com Rich
console = Console()
console.print("[green][OK][/green] Teste Rich")
t5 = time.perf_counter()
print(f"[{(t5-t4)*1000:6.0f}ms] Primeiro print Rich")

print(f"\n=== Total: {(t5-t0)*1000:.0f}ms ===")

# Breakdown detalhado do que foi importado
print("\n=== Módulos carregados ===")
print(f"stdlib: {len([m for m in sys.modules if m.split('.')[0] in os.__name__])}")
print(f"third-party: {len([m for m in sys.modules if m.split('.')[0] in ['rich', 'dotenv']])}")
print(f"core.sky: {len([m for m in sys.modules if m.startswith('core.sky')])}")
print(f"Total módulos: {len(sys.modules)}")
