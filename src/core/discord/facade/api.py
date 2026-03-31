# -*- coding: utf-8 -*-
"""
API FastAPI para debugar Discord MCP.

Permite testar o bot Discord via HTTP sem depender do MCP stdio.

Uso:
    python -m src.core.discord.facade.api

Acesse: http://localhost:8000/docs
"""
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import asyncio
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# FASTAPI APP
# =============================================================================
app = FastAPI(
    title="Discord Debug API",
    description="API HTTP para debugar Discord MCP",
    version="1.0.0"
)

# =============================================================================
# ESTADO GLOBAL
# =============================================================================
discord_client = None
discord_ready = False

# =============================================================================
# MODELOS
# =============================================================================
class SendMessageRequest(BaseModel):
    chat_id: str
    content: str

class SendButtonsRequest(BaseModel):
    chat_id: str
    title: str
    description: str = ""
    buttons: list[dict]

# =============================================================================
# ENDPOINTS
# =============================================================================
@app.get("/")
async def root():
    """Status da API e do Discord client."""
    return {
        "status": "running",
        "discord_ready": discord_ready,
        "discord_user": str(discord_client.user) if discord_ready and discord_client.user else None,
        "docs": "/docs",
        "endpoints": {
            "GET /": "Status",
            "GET /status": "Status detalhado",
            "POST /send-message": "Enviar mensagem",
            "POST /send-buttons": "Enviar botões",
            "GET /test": "Teste de notificação"
        }
    }

@app.get("/status")
async def status():
    """Status detalhado do Discord client."""
    if not discord_client:
        return {"connected": False, "error": "Discord client não inicializado"}

    return {
        "connected": discord_ready,
        "user": str(discord_client.user) if discord_client.user else None,
        "user_id": str(discord_client.user.id) if discord_client.user else None,
        "guilds": len(discord_client.guilds) if discord_ready else 0,
    }

@app.post("/send-message")
async def send_message(req: SendMessageRequest):
    """Envia mensagem para canal Discord."""
    if not discord_ready:
        raise HTTPException(status_code=503, detail="Discord não está pronto")

    try:
        from src.core.discord.application.services.discord_service import DiscordService

        service = DiscordService(client=discord_client)
        msg = await service.send_message(
            channel_id=req.chat_id,
            content=req.content
        )

        return {
            "success": True,
            "message_id": str(msg.id) if msg else None,
            "channel_id": req.chat_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-buttons")
async def send_buttons(req: SendButtonsRequest):
    """Envia botões para canal Discord."""
    if not discord_ready:
        raise HTTPException(status_code=503, detail="Discord não está pronto")

    try:
        from src.core.discord.application.services.discord_service import DiscordService, ButtonConfig

        service = DiscordService(client=discord_client)

        buttons = [
            ButtonConfig(
                label=b["label"],
                style=b.get("style", "primary"),
                custom_id=b["id"],
                disabled=b.get("disabled", False)
            )
            for b in req.buttons
        ]

        msg = await service.send_buttons(
            channel_id=req.chat_id,
            title=req.title,
            description=req.description,
            buttons=buttons
        )

        return {
            "success": True,
            "message_id": str(msg.id) if msg else None,
            "channel_id": req.chat_id,
            "buttons_count": len(buttons)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
async def test():
    """Teste de API."""
    return {
        "message": "API funcionando!",
        "discord_ready": discord_ready
    }

# =============================================================================
# STARTUP/SHUTDOWN
# =============================================================================
@app.on_event("startup")
async def startup_event():
    """Inicia Discord client ao iniciar a API."""
    global discord_client, discord_ready

    import sys
    sys.stdout.flush()
    logger.info("[API] ========== STARTUP EVENT ==========")
    logger.info("[API] Iniciando Discord client...")

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
        print("[API] ERRO: DISCORD_BOT_TOKEN não encontrado!")
        return

    # Inicia Discord client
    from src.core.discord.client import create_discord_client
    from src.core.discord.application.services.event_publisher import EventPublisher
    from src.core.discord.infrastructure.mcp_button_adapter import MCPButtonAdapter
    from discord import InteractionType

    discord_client = create_discord_client()

    # ============================================================================
    # REGISTRAR HANDLERS ANTES DE CONECTAR!
    # ============================================================================
    logger.info("[API] Registrando handlers BEFORE connect...")

    @discord_client.event
    async def on_ready():
        global discord_ready
        discord_ready = True
        logger.info(f"[API] on_ready DISPARADO! Usuario: {discord_client.user}")

    @discord_client.event
    async def on_interaction_create(interaction):
        """Handler de interações - DEBUG."""
        logger.info(f"[API] === INTERACTION CREATE ===")
        logger.info(f"[API] type={interaction.type}, data={interaction.data}")

        if interaction.type != InteractionType.component:
            logger.info(f"[API] NAO eh component, retornando")
            return

        logger.info(f"[API] EH component! Processando...")

        try:
            await interaction.response.defer()
            logger.info(f"[API] Defer OK!")
        except Exception as e:
            logger.error(f"[API] Erro defer: {e}")
            return

        # Processar (sem MCP notification na API)
        event_publisher = EventPublisher()
        button_adapter = MCPButtonAdapter(event_publisher)
        result = await button_adapter.handle_interaction(interaction)

        logger.info(f"[API] Resultado: {result['status']} - {result.get('message', '')}")

    # Conecta em background
    async def keep_discord_connected():
        try:
            await discord_client.login(token)
            await discord_client.connect()
        except Exception as e:
            print(f"[API] Erro Discord: {e}")

    asyncio.create_task(keep_discord_connected())

    # Aguarda conexão
    for _ in range(30):
        await asyncio.sleep(1)
        if discord_ready:
            break

    if discord_ready:
        print("[API] Discord pronto!")
    else:
        print("[API] Discord não conectou em 30s")

@app.on_event("shutdown")
async def shutdown_event():
    """Fecha Discord client."""
    global discord_client

    if discord_client:
        await discord_client.close()
        print("[API] Discord client fechado")

# =============================================================================
# MAIN
# =============================================================================
def main():
    """Entry point para executar a API."""
    print("=" * 50)
    print("  Discord Facade API")
    print("=" * 50)
    print(f"Docs: http://localhost:8000/docs")
    print(f"Root: http://localhost:8000/")
    print("=" * 50)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
