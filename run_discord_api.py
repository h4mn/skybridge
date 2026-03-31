#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API FastAPI para debugar Discord MCP

Permite testar o bot Discord sem depender do MCP stdio.

Uso:
    python run_discord_api.py

Acesse: http://localhost:8000
Docs: http://localhost:8000/docs
"""
import os
import sys
import io
from pathlib import Path

# =============================================================================
# FORÇAR UTF-8 NO WINDOWS
# =============================================================================
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Adiciona src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# =============================================================================
# FASTAPI SETUP
# =============================================================================
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import asyncio

app = FastAPI(
    title="Discord Debug API",
    description="API para debugar Discord MCP sem depender de stdio",
    version="1.0.0"
)

# =============================================================================
# CARREGA TOKEN
# =============================================================================
state_dir = Path(os.environ.get("DISCORD_STATE_DIR", Path.home() / ".claude" / "channels" / "discord"))
env_file = state_dir / ".env"

if env_file.exists():
    print(f"[INFO] Carregando variáveis de {env_file}")
    for line in env_file.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value

token = os.environ.get("DISCORD_BOT_TOKEN")
if not token:
    print("[ERRO] DISCORD_BOT_TOKEN não configurado!")
    print(f"\nCrie o arquivo {env_file} com:")
    print('DISCORD_BOT_TOKEN="seu_token_aqui"')
    sys.exit(1)

# =============================================================================
# DISCORD CLIENT (GLOBAL)
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
        "endpoints": {
            "status": "/status",
            "send_message": "/send-message (POST)",
            "send_buttons": "/send-buttons (POST)",
            "test_notification": "/test-notification (GET)"
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

        # Converter dict para ButtonConfig
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

@app.get("/test-notification")
async def test_notification():
    """Teste de notificação MCP (simula clique)."""
    return {
        "message": "Esta é uma notificação de teste",
        "timestamp": "2026-03-30T23:59:59Z",
        "test": "Se você recebeu isso, a API está funcionando!"
    }

# =============================================================================
# STARTUP/SHUTDOWN
# =============================================================================
@app.on_event("startup")
async def startup_event():
    """Inicia Discord client ao iniciar a API."""
    global discord_client, discord_ready

    print("[INFO] Iniciando Discord client...")

    from src.core.discord.client import create_discord_client
    from src.core.discord.application.services.event_publisher import EventPublisher
    from src.core.discord.infrastructure.mcp_button_adapter import MCPButtonAdapter

    discord_client = create_discord_client()

    # Registrar handler de interações
    from discord import InteractionType

    @discord_client.event
    async def on_ready():
        global discord_ready
        discord_ready = True
        print(f"[INFO] Discord conectado como {discord_client.user}")

    @discord_client.event
    async def on_interaction_create(interaction):
        """Handler de interações (botões)."""
        print(f"[DEBUG] Interação recebida: type={interaction.type}")

        if interaction.type != InteractionType.component:
            return

        try:
            await interaction.response.defer()
        except Exception as e:
            print(f"[ERROR] Falha no defer: {e}")
            return

        # Processar via adapter (sem notificação MCP na API)
        event_publisher = EventPublisher()
        button_adapter = MCPButtonAdapter(event_publisher)
        result = await button_adapter.handle_interaction(interaction)

        print(f"[DEBUG] Resultado: {result}")

    # Iniciar Discord client em background
    async def keep_discord_connected():
        try:
            await discord_client.login(token)
            await discord_client.connect()
        except Exception as e:
            print(f"[ERROR] Erro Discord: {e}")

    asyncio.create_task(keep_discord_connected())

    # Aguardar Discord estar pronto
    for _ in range(30):
        await asyncio.sleep(1)
        if discord_ready:
            break

    if not discord_ready:
        print("[WARNING] Discord não conectou em 30s")

@app.on_event("shutdown")
async def shutdown_event():
    """Fecha Discord client ao desligar a API."""
    global discord_client

    if discord_client:
        await discord_client.close()
        print("[INFO] Discord client fechado")

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Discord Debug API")
    print("=" * 60)
    print(f"[INFO] State dir: {state_dir}")
    print(f"[INFO] Docs: http://localhost:8000/docs")
    print(f"[INFO] Root: http://localhost:8000/")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
