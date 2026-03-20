
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(src_path))

import uvicorn
from core.sky.voice.api.app import app

print(f"[Voice API] Starting on http://127.0.0.1:8767")
uvicorn.run(app, host="127.0.0.1", port=8767, log_level="warning")
