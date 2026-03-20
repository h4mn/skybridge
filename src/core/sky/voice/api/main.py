"""Voice API - Main entry point."""

import argparse
import io
import sys
import signal
import uvicorn

# UTF-8 fix para Windows (emojis e acentos)
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.sky.voice.api.app import app


def main():
    """Entry point para Voice API."""
    parser = argparse.ArgumentParser(description="Sky Voice API")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host para bind (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Porta para bind (default: 8765)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload para desenvolvimento"
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug"],
        help="Log level (default: info)"
    )

    args = parser.parse_args()

    print(f"[Voice API] Starting on http://{args.host}:{args.port}")

    # Signal handlers para shutdown graciosos
    def signal_handler(sig, frame):
        print("\n[Voice API] Shutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Roda Uvicorn
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
