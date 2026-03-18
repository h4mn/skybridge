# -*- coding: utf-8 -*-
"""
Script wrapper para executar demos do Skybridge.
"""
import sys
from pathlib import Path

# Adiciona src ao path - ANTES dos imports
_repo_root = Path(__file__).parent.parent
_src_path = _repo_root / "src"
# IMPORTANTE: src deve vir ANTES de _repo_root para evitar conflitos
# Remove _repo_root do path se existir, para inserir na ordem correta
if str(_repo_root) in sys.path:
    sys.path.remove(str(_repo_root))
# Insere src PRIMEIRO
sys.path.insert(0, str(_src_path))
# Depois insere _repo_root
sys.path.insert(1, str(_repo_root))

from apps.demo.cli import main
import asyncio

if __name__ == "__main__":
    # main() lê sys.argv diretamente
    asyncio.run(main())
