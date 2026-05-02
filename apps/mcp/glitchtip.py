#!/usr/bin/env python
"""Fachada MCP para Glitchtip — auto-start Docker + bridge stdio."""

import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import logging

# LOG IMEDIATO — antes de qualquer outra coisa
_LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "glitchtip_facade.log"
_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
_facade_log = logging.getLogger("glitchtip_facade")
_facade_log.setLevel(logging.DEBUG)
_fh = RotatingFileHandler(_LOG_PATH, maxBytes=500_000, backupCount=1, encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
_facade_log.addHandler(_fh)

_facade_log.info("=== FACADE START ===")
_facade_log.info(f"cwd={os.getcwd()}")
_facade_log.info(f"argv={sys.argv}")
_facade_log.info(f"python={sys.executable}")

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

# Resolve caminhos relativos à raiz do projeto
_project_root = Path(__file__).resolve().parents[2]
_facade_log.info(f"project_root={_project_root}")

# Defaults — podem ser sobrescritos por ENV
os.environ.setdefault("GLITCHTIP_MCP_URL", "http://localhost:8000/mcp")
os.environ.setdefault("GLITCHTIP_COMPOSE_DIR", str(_project_root / "runtime" / "observability"))

_token = os.environ.get("GLITCHTIP_API_TOKEN", "")
_facade_log.info(f"has_token={bool(_token)}")

def _load_env(path: Path) -> None:
    if not path.exists():
        _facade_log.debug(f"env missing: {path}")
        return
    count = 0
    for _line in path.read_text(encoding="utf-8").split("\n"):
        _line = _line.strip()
        if not _line or _line.startswith("#"):
            continue
        if "=" in _line:
            _key, _, _val = _line.partition("=")
            _key, _val = _key.strip(), _val.strip()
            if _key and _key not in os.environ:
                os.environ[_key] = _val
                count += 1
    _facade_log.debug(f"env loaded: {path} ({count} vars)")

_load_env(_project_root / ".env")
_load_env(_project_root / "runtime" / "observability" / ".env")

sys.path.insert(0, str(_project_root / "src"))

_facade_log.info("Importing client...")
try:
    from core.observability.glitchtip_client import main
    import asyncio
    _facade_log.info("Client imported, running main()")
    asyncio.run(main())
except KeyboardInterrupt:
    _facade_log.info("Interrupted")
except Exception as e:
    import traceback
    _facade_log.error(f"FATAL: {e}\n{traceback.format_exc()}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
finally:
    _facade_log.info("=== FACADE END ===")
