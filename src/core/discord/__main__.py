"""
Entry point para o Discord MCP Server.

Uso:
    python -m src.core.discord

Variáveis de ambiente:
    DISCORD_BOT_TOKEN: Token do bot Discord (obrigatório)
    DISCORD_STATE_DIR: Diretório de estado (opcional)
    DISCORD_ACCESS_MODE: 'static' para modo somente leitura (opcional)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def load_env() -> None:
    """Carrega variáveis de ambiente do arquivo .env."""
    state_dir = Path(
        os.environ.get("DISCORD_STATE_DIR", Path.home() / ".claude" / "channels" / "discord")
    )
    env_file = state_dir / ".env"

    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    # Só define se não existe
                    if key and key not in os.environ:
                        os.environ[key] = value
            logger.info(f"Variáveis carregadas de {env_file}")
        except Exception as e:
            logger.warning(f"Erro ao carregar .env: {e}")


def main() -> None:
    """Ponto de entrada principal."""
    # MARCADOR v5 - Garante que estamos carregando código novo
    print("[MARCADOR v5 __main__] Carregando __main__.py NOVO", flush=True)

    # Carrega .env
    load_env()

    # Verifica token
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("DISCORD_BOT_TOKEN não configurado")
        logger.error(f"Configure em ~/.claude/channels/discord/.env")
        sys.exit(1)

    # Importa e executa servidor
    from .server import DiscordMCPServer

    server = DiscordMCPServer()

    try:
        asyncio.run(server.run(token))
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
