# coding: utf-8
"""
Script de inicialização do Sky Chat Textual UI.

Usa bootstrap com barra de progresso para carregar componentes.
"""

import os
import sys
import time
from pathlib import Path

# MARK: Cold Start Timer - INÍCIO ABSOLUTO
_COLD_START_START = time.perf_counter()

# MARK: Feedback IMEDIATO (print simples antes de Rich)
print("Carregando Sky Chat...", flush=True, end='')

# Adiciona src ao path
project_root = Path(__file__).parent.parent
src_path = str(project_root / "src")
sys.path.insert(0, src_path)

# Configura variáveis de ambiente
os.environ["USE_RAG_MEMORY"] = "true"
os.environ["USE_CLAUDE_CHAT"] = "true"
os.environ["USE_TEXTUAL_UI"] = "true"

# Carrega .env se existir
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Executa o app Textual via bootstrap
if __name__ == "__main__":
    from core.sky.bootstrap import bootstrap

    app = bootstrap.run(cold_start_start=_COLD_START_START, initial_print_done=True)
    app.run(mouse=True)  # Mouse habilitado para melhor UX
