#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notificador Discord para Claude Code
Recebe JSON via stdin e envia embed formatado para Discord

Uso:
    echo '{"message": "Teste"}' | DISCORD_WEBHOOK_URL=... python notify_discord.py

Variáveis de ambiente:
    DISCORD_WEBHOOK_URL - URL do webhook Discord (obrigatório)
    CLAUDE_CODE_VERSION - Versão do Claude Code (opcional)
    CLAUDE_MODEL - Modelo atual (opcional)
    CLAUDE_CONTEXT_PCT - Percentual de contexto usado (opcional)
    CLAUDE_CWD - Diretório atual (opcional)
"""
import json
import sys
import os
import platform
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
import io

# Forcar UTF-8 no Windows (stdin, stdout, stderr)
if sys.platform == "win32":
    if hasattr(sys.stdin, 'buffer'):
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuração
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Cores Discord (inteiros)
COLORS = {
    "success": 0x00FF00,      # Verde
    "info": 0x3B82F6,         # Azul
    "warning": 0xFFA500,      # Laranja
    "error": 0xFF0000,        # Vermelho
    "task_completed": 0x00FF00,
    "agent_finished": 0x8B5CF6,  # Violeta (Sky)
}

def get_system_info():
    """Retorna informações amigáveis do sistema"""
    # Nome do computador
    computer_name = os.environ.get("COMPUTERNAME", platform.node())

    # SO e versão amigável
    system = platform.system()
    release = platform.release()
    version = platform.version()

    if system == "Windows":
        # Windows 10/11 detection mais precisa
        try:
            # Build number para distinguir Win10 vs Win11
            build = int(version.split('.')[-1]) if '.' in version else 0
            if build >= 22000:
                os_friendly = f"Windows 11 (Build {build})"
            else:
                os_friendly = f"Windows {release} (Build {build})"
        except:
            os_friendly = f"Windows {release}"
    elif system == "Linux":
        # Tenta pegar distro
        try:
            with open("/etc/os-release") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("PRETTY_NAME="):
                        os_friendly = line.split("=")[1].strip('"')
                        break
                else:
                    os_friendly = f"Linux {release}"
        except:
            os_friendly = f"Linux {release}"
    elif system == "Darwin":
        os_friendly = f"macOS {release}"
    else:
        os_friendly = f"{system} {release}"

    return computer_name, os_friendly

def get_last_assistant_response(transcript_path):
    """Lê o transcript e retorna a última resposta textual do assistant"""
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Ler de trás para frente (últimas mensagens primeiro)
        for line in reversed(lines):
            try:
                entry = json.loads(line.strip())
                message = entry.get("message", {})

                # Verifica se é mensagem do assistant
                if message.get("role") == "assistant":
                    content = message.get("content", [])

                    # Extrai texto não-tool_use
                    text_parts = []
                    for part in content:
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", ""))

                    if text_parts:
                        # Combina todos os textos
                        full_text = "".join(text_parts).strip()

                        # **CRÍTICO**: Só retorna se for LONGO (>200 chars = resumo final)
                        # Mensagens curtas são raciocínio intermediário, não o resumo final
                        if len(full_text) > 200:
                            # Limita tamanho (máx 500 chars para notificação)
                            if len(full_text) > 500:
                                full_text = full_text[:497] + "..."
                            return full_text

            except (json.JSONDecodeError, KeyError):
                continue

        return None  # Nenhuma resposta textual encontrada

    except Exception:
        return None

def summarize_text(text: str, transcript_path: str = "") -> str:
    """Resume texto por truncamento simples - sem Agent SDK"""
    # Trunca diretamente para primeira frase ou 150 caracteres
    # Prioriza: primeira frase completa, ou truncamento em 150 chars

    # Tenta pegar primeira frase (até primeiro ponto final)
    first_period = text.find('. ')
    if first_period > 0 and first_period <= 200:
        result = text[:first_period + 1]
    else:
        # Trunca em 150 caracteres
        result = text[:147] + "..."

    return result[:150] if len(result) > 150 else result

def get_sky_footer(session_data=None):
    """Gera rodapé no formato Sky

    Args:
        session_data: Dados da sessão (mesmo formato da statusline)
    """
    persona = "Sky"

    # Tenta pegar dos dados da sessão (formato statusline)
    if session_data:
        version = session_data.get("version", os.environ.get("CLAUDE_CODE_VERSION", "2.1.90"))
        model_info = session_data.get("model", {})
        model = model_info.get("display_name", os.environ.get("CLAUDE_MODEL", "glm-5"))

        # Contexto usado
        ctx = session_data.get("context_window", {})
        context_pct = ctx.get("used_percentage", "?")

        # Diretório
        cwd = session_data.get("cwd", os.environ.get("CLAUDE_CWD", os.environ.get("PWD", ".")))
    else:
        # Fallback para variáveis de ambiente
        version = os.environ.get("CLAUDE_CODE_VERSION", "2.1.90")
        model = os.environ.get("CLAUDE_MODEL", "glm-5")
        context_pct = os.environ.get("CLAUDE_CONTEXT_PCT", "?")
        cwd = os.environ.get("CLAUDE_CWD", os.environ.get("PWD", "."))

    # Simplifica cwd
    cwd_name = os.path.basename(cwd) if cwd else "?"

    return f"🤖 {persona} v{version} [{model}] | {context_pct}% | {cwd_name}"

def send_to_discord(embed):
    """Envia embed para Discord via webhook"""
    if not DISCORD_WEBHOOK_URL:
        print("ERRO: DISCORD_WEBHOOK_URL não definida", file=sys.stderr)
        return False

    payload = {
        "embeds": [embed],
        "username": "Sky Notifications",
        "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png"
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Claude-Code/2.1.90"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 204
    except urllib.error.HTTPError as e:
        print(f"ERRO Discord: {e.code} - {e.read()}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return False

def main():
    import time as time_module

    # Log estruturado para debug
    HOOK_LOG = Path.home() / "hook_call_log.txt"

    # ========== MARCA TEMPO INÍCIO ==========
    start_time = time_module.time()

    # Lê notificação do stdin
    try:
        input_data = sys.stdin.read()
        if not input_data:
            input_data = "{}"
        notification = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"ERRO JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # ========== LOG ESTRUTURADO (sempre mostra) ==========
    print("\n" + "="*70, file=sys.stderr)
    print("🔔 HOOK DISPARADO - PostToolUse", file=sys.stderr)
    print("="*70, file=sys.stderr)
    print(f"📥 PAYLOAD RAW ({len(input_data)} chars):", file=sys.stderr)
    print(input_data[:500] + ("..." if len(input_data) > 500 else ""), file=sys.stderr)
    print("="*70, file=sys.stderr)

    # Extrai dados da notificação
    notif_type = notification.get("notification_type", "info")
    message = notification.get("message", "")
    session_id = notification.get("session_id", "")
    data = notification.get("data", {})

    # Dados da sessão (mesmo formato da statusline)
    # Pode vir dentro de "session_data" ou diretamente no root
    session_data = notification.get("session_data", notification)

    print(f"📋 notification_type: {notif_type}", file=sys.stderr)
    print(f"📋 session_id: {session_id}", file=sys.stderr)
    print(f"📋 transcript_path: {session_data.get('transcript_path', 'N/A')}", file=sys.stderr)
    print(f"📋 message (payload): {message[:100] if message else '(vazio)'}...", file=sys.stderr)
    print("="*70, file=sys.stderr)
    # ===================================================

    # Dados da sessão (mesmo formato da statusline)
    # Pode vir dentro de "session_data" ou diretamente no root
    session_data = notification.get("session_data", notification)

    # Se não houver mensagem e tiver transcript_path, tenta extrair do transcript
    extract_start = time_module.time()
    if not message and "transcript_path" in session_data:
        transcript_path = session_data.get("transcript_path")
        extracted = get_last_assistant_response(transcript_path)
        if extracted:
            # Se o texto for longo, resume
            if len(extracted) > 180:
                message = summarize_text(extracted)
            else:
                message = extracted

        extract_time = (time_module.time() - extract_start) * 1000
        print(f"⏱️ EXTRAÇÃO do transcript: {extract_time:.0f}ms", file=sys.stderr)
    else:
            message = "✅ Operação concluída"

    # Se ainda não tem mensagem, usa padrão
    if not message:
        message = "Notificação do Claude Code"

    # Informações do sistema
    computer_name, os_friendly = get_system_info()
    footer = get_sky_footer(session_data)

    # Cor baseada no tipo
    color = COLORS.get(notif_type, COLORS["info"])

    # Título
    title = f"💻 {computer_name} • {os_friendly}"

    # Monta embed
    embed = {
        "title": title,
        "description": message,
        "color": color,
        "footer": {
            "text": footer
        },
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

    # Adiciona campos extras se houver
    if data:
        fields = []
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                fields.append({
                    "name": key.replace("_", " ").title(),
                    "value": str(value),
                    "inline": True
                })
        if fields:
            embed["fields"] = fields[:5]  # Max 5 fields

    # ========== LOG DO QUE VAI SER ENVIADO ==========
    print(f"📤 MENSAGEM FINAL ({len(message)} chars):", file=sys.stderr)
    print(message, file=sys.stderr)
    print(f"📤 EMBED TITLE: {embed['title']}", file=sys.stderr)
    print(f"📤 EMBED COLOR: {embed['color']}", file=sys.stderr)
    print(f"📤 EMBED FOOTER: {embed['footer']['text']}", file=sys.stderr)
    print("="*70 + "\n", file=sys.stderr)
    # ================================================

    # Envia
    discord_start = time_module.time()
    success = send_to_discord(embed)
    discord_time = (time_module.time() - discord_start) * 1000

    # ========== TEMPO TOTAL ==========
    total_time = (time_module.time() - start_time) * 1000
    print(f"⏱️ TEMPO Discord API: {discord_time:.0f}ms", file=sys.stderr)
    print(f"⏱️ TEMPO TOTAL script: {total_time:.0f}ms", file=sys.stderr)
    print("="*70 + "\n", file=sys.stderr)
    # ================================================

    # Output JSON para o Claude Code
    output = {
        "systemMessage": "Notificação enviada para Discord" if success else "Falha ao enviar notificação",
        "suppressOutput": True
    }
    print(json.dumps(output))

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
