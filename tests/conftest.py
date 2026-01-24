# -*- coding: utf-8 -*-
"""
pytest configuration for Skybridge tests.

Adds src directory to Python path.
"""
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def is_server_online() -> bool:
    """
    Verifica se o servidor Skybridge está online.

    Returns:
        True se o servidor responde em http://localhost:8000
    """
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False
