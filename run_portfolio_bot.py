# -*- coding: utf-8 -*-
"""Script simplificado para iniciar o bot Portfolio com logging."""

import asyncio
import sys
import logging
from pathlib import Path

from dotenv import dotenv_values

# Configura logging em arquivo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Inicia bot Portfolio."""
    # Carrega configuração
    config = dotenv_values(Path.home() / ".claude/channels/discord" / ".env")
    token = config.get("DISCORD_BOT_TOKEN")

    if not token:
        logger.error("❌ DISCORD_BOT_TOKEN não encontrado em .env")
        return

    logger.info(f"🔑 Token carregado: {token[:10]}...")

    from discord_bot import PortfolioBot

    # Canal #paper-heartbeat
    CHANNEL_ID = 1488599448882909204

    # Cria bot
    bot = PortfolioBot(channel_id=CHANNEL_ID)

    logger.info("="*60)
    logger.info("🤖 PORTFOLIO BOT - Discord")
    logger.info("="*60)
    logger.info(f"Canal alvo: #{CHANNEL_ID} (#paper-heartbeat)")
    logger.info("Iniciando bot...")

    # Inicia bot
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("👋 Bot interrompido")
    except Exception as e:
        logger.error(f"❌ Erro: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
