"""Script simples para iniciar a Voice API."""

import sys
from pathlib import Path

# Adiciona src ao path
src_path = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    import uvicorn
    from core.sky.voice.api.app import app

    print("[Voice API] Starting on http://127.0.0.1:8765")
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
