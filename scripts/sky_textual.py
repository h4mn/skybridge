# coding: utf-8
"""
Script de inicialização do Sky Chat Textual UI.

Idêntico à POC: usa SkyApp com CSS_PATH relativo ao módulo.
"""

import os
import sys
from pathlib import Path
from core.sky.chat.textual_ui import SkyApp

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

# Executa o app Textual - usa SkyApp do __init__.py
if __name__ == "__main__":
    app = SkyApp()
    app.run(mouse=True)  # Mouse habilitado para melhor UX
