#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste simples do Discord client para verificar handlers.

Este script inicia o bot Discord e fica aguardando interações.
"""
import os
import sys
import io
import asyncio
import logging
from pathlib import Path

# Abrir arquivo de log com modo unbuffered
LOG_FILE = open("test_discord_DIRECT.log", "w", encoding="utf-8", buffering=1)

def log(msg):
    """Escreve no arquivo e no stdout."""
    LOG_FILE.write(f"{msg}\n")
    LOG_FILE.flush()
    print(msg)
    sys.stdout.flush()

# Configurar logging para sair imediatamente
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# =============================================================================
# FORÇAR UTF-8 NO WINDOWS
# =============================================================================
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
sys.stderr.reconfigure(encoding='utf-8') if hasattr(sys.stderr, 'reconfigure') else None
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Adiciona src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Carrega token
state_dir = Path(os.environ.get("DISCORD_STATE_DIR", Path.home() / ".claude" / "channels" / "discord"))
env_file = state_dir / ".env"

token = None
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            if key.strip() == "DISCORD_BOT_TOKEN":
                token = value.strip()
                break

if not token:
    token = os.environ.get("DISCORD_BOT_TOKEN")

if not token:
    log("[TESTE] DISCORD_BOT_TOKEN não encontrado!")
    sys.exit(1)

log("[TESTE] Iniciando Discord client...")

from discord import InteractionType
from src.core.discord.client import create_discord_client
from src.core.discord.application.services.event_publisher import EventPublisher
from src.core.discord.infrastructure.mcp_button_adapter import MCPButtonAdapter

discord_client = create_discord_client()

@discord_client.event
async def on_ready():
    logger.info(f"[TESTE] === ON READY ===")
    logger.info(f"[TESTE] Bot conectado: {discord_client.user}")
    sys.stdout.flush()

@discord_client.event
async def on_interaction_create(interaction):
    logger.info(f"[TESTE] === INTERACTION CREATE ===")
    logger.info(f"[TESTE] Type: {interaction.type}")
    logger.info(f"[TESTE] Data: {interaction.data}")
    sys.stdout.flush()

    if interaction.type != InteractionType.component:
        logger.info(f"[TESTE] Não é component, ignorando")
        return

    logger.info(f"[TESTE] É COMPONENT! Custom ID: {interaction.data.get('custom_id', 'N/A')}")
    sys.stdout.flush()

    try:
        await interaction.response.defer()
        logger.info(f"[TESTE] Defer OK!")
    except Exception as e:
        logger.error(f"[TESTE] Erro no defer: {e}")
        return

    # Processar
    event_publisher = EventPublisher()
    button_adapter = MCPButtonAdapter(event_publisher)
    result = await button_adapter.handle_interaction(interaction)

    logger.info(f"[TESTE] Resultado: {result}")
    sys.stdout.flush()

async def main():
    logger.info("[TESTE] Fazendo login...")
    sys.stdout.flush()
    try:
        await discord_client.login(token)
    except Exception as e:
        logger.error(f"[ERRO] Login falhou: {e}")
        return

    logger.info("[TESTE] Conectando ao Gateway...")
    sys.stdout.flush()
    try:
        await discord_client.connect()
    except Exception as e:
        logger.error(f"[ERRO] Connect falhou: {e}")
        return

    logger.info("[TESTE] Bot rodando! Pressione Ctrl+C para parar.")
    sys.stdout.flush()

    # Mantém rodando
    try:
        await discord_client.wait_until_ready()
        logger.info("[TESTE] Bot PRONTO!")
        sys.stdout.flush()
        await asyncio.Event().wait()  # Roda para sempre
    except KeyboardInterrupt:
        logger.info("[TESTE] Interrompido")
    finally:
        await discord_client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n[TESTE] Encerrado")
