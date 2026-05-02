"""
Glitchtip MCP Client — Bridge stdio para HTTP/SSE com auto-start Docker.

Conecta ao Glitchtip MCP server via HTTP/SSE, faz handshake initialize,
e entra no loop stdio para repassar mensagens do Claude Code.
"""

import asyncio
import json
import logging
import os
import shutil
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import httpx

# Logging em arquivo apenas (stderr limpo pro protocolo MCP)
LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = logging.getLogger("glitchtip_mcp")
_logger.setLevel(logging.DEBUG)
_fh = RotatingFileHandler(LOG_DIR / "glitchtip_mcp.log", maxBytes=2_000_000, backupCount=2, encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
_logger.addHandler(_fh)


def _log(msg: str) -> None:
    _logger.info(msg)


async def _check_server(host: str = "localhost", port: int = 8000) -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            r = await c.get(f"http://{host}:{port}")
            return r.status_code < 500
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError):
        return False


async def _maybe_start_docker() -> None:
    """Auto-start Docker Compose se server não está disponível."""
    host = os.getenv("GLITCHTIP_HOST", "localhost")
    port = int(os.getenv("GLITCHTIP_PORT", "8000"))

    if await _check_server(host, port):
        _log("Glitchtip already running")
        return

    compose_dir = os.getenv("GLITCHTIP_COMPOSE_DIR", "")
    if not compose_dir:
        _log("No compose dir configured, skipping auto-start")
        return

    if not shutil.which("docker"):
        _log("Docker not found, skipping auto-start")
        return

    if not Path(compose_dir).exists():
        _log(f"Compose dir not found: {compose_dir}")
        return

    _log(f"Auto-starting Glitchtip in {compose_dir}...")
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose", "up", "-d",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=compose_dir,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        if proc.returncode != 0:
            _log(f"Docker compose failed: {stderr.decode().strip()}")
            return
    except Exception as e:
        _log(f"Auto-start error: {e}")
        return

    # Poll até disponível (timeout 30s)
    timeout = int(os.getenv("GLITCHTIP_STARTUP_TIMEOUT", "30"))
    for _ in range(timeout // 2):
        if await _check_server(host, port):
            _log("Glitchtip started successfully")
            return
        await asyncio.sleep(2)
    _log(f"Startup timeout ({timeout}s)")


def _parse_sse(text: str) -> dict[str, Any]:
    for line in text.strip().split("\n"):
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    raise ValueError(f"No data in SSE: {text[:200]}")


async def _send_message(url: str, message: dict[str, Any], headers: dict) -> dict[str, Any]:
    """Envia mensagem ao MCP server via HTTP/SSE."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=message, headers=headers)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type or "event: message" in response.text:
            return _parse_sse(response.text)
        return response.json()


async def main() -> None:
    url = os.getenv("GLITCHTIP_MCP_URL", "http://localhost:8000/mcp").rstrip("/")
    token = os.getenv("GLITCHTIP_API_TOKEN", "")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1]

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "Claude-Desktop-MCP-Client",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    _log(f"Starting — url={url}, has_token={bool(token)}")

    await _maybe_start_docker()

    # Handshake initialize — igual ao client original
    try:
        init_result = await _send_message(url, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "claude-desktop",
                    "version": "1.0.0"
                }
            }
        }, headers)
        server_name = init_result.get("result", {}).get("serverInfo", {}).get("name", "Unknown")
        _log(f"Connected to: {server_name}")
    except Exception as e:
        _log(f"Initialize failed: {e}")
        sys.exit(1)

    _log("Entering stdio loop")

    # Loop stdio — bridge puro
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            message = json.loads(line.strip())
            _logger.debug(f"→ {message.get('method', message.get('id'))}")

            result = await _send_message(url, message, headers)

            _logger.debug(f"← ok")
            print(json.dumps(result))
            sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except Exception as e:
            _logger.error(f"Error: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": message.get("id") if "message" in dir() else None,
                "error": {"code": -32603, "message": str(e)},
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

    _log("Exiting")


if __name__ == "__main__":
    asyncio.run(main())
