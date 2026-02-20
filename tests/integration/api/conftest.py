# -*- coding: utf-8 -*-
"""
pytest configuration para testes de integração da API.
"""

import sys
from pathlib import Path

# Adiciona src e apps ao path antes de qualquer import
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
apps_path = Path(__file__).parent.parent.parent.parent.parent / "apps"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
if str(apps_path) not in sys.path:
    sys.path.insert(0, str(apps_path))
