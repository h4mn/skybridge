#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Notifications - Configura notificações Discord para Claude Code

Uso:
    python setup_notifications.py --webhook "https://discord.com/api/webhooks/..."
    python setup_notifications.py --test
    python setup_notifications.py --status
"""
import json
import sys
import os
import argparse
import io

# Forcar UTF-8 no Windows
if sys.platform == "win32":
    if hasattr(sys.stdin, 'buffer'):
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SKILL_DIR)))
SETTINGS_FILE = os.path.join(PROJECT_ROOT, ".claude", "settings.json")

def load_settings():
    """Carrega settings.json atual"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_settings(settings):
    """Salva settings.json"""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def test_webhook(webhook_url):
    """Testa se o webhook funciona"""
    import urllib.request
    import urllib.error

    payload = {"content": "🧪 Teste de conexão - Claude Code Notifications"}
    data = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Claude-Code-Setup/1.0"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 204, "OK"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"
    except Exception as e:
        return False, str(e)

def configure_notifications(webhook_url):
    """Configura notificações no settings.json"""
    # Testa webhook primeiro
    success, message = test_webhook(webhook_url)
    if not success:
        print(f"❌ Webhook inválido: {message}")
        return False

    print("✅ Webhook válido!")

    # Carrega settings atual
    settings = load_settings()

    # Adiciona variáveis de ambiente
    if "env" not in settings:
        settings["env"] = {}

    settings["env"]["DISCORD_WEBHOOK_URL"] = webhook_url
    settings["env"]["PYTHONUTF8"] = "1"

    # Adiciona hook de notificação
    if "hooks" not in settings:
        settings["hooks"] = {}

    # Remove hook existente se houver
    if "Notification" in settings["hooks"]:
        settings["hooks"]["Notification"] = [
            h for h in settings["hooks"]["Notification"]
            if "notify_discord.py" not in str(h.get("hooks", [{}])[0].get("command", ""))
        ]

    # Adiciona novo hook
    notification_hook = {
        "matcher": "task_completed|agent_finished|background_bash",
        "hooks": [
            {
                "type": "command",
                "command": "python .claude/skills/notifications/scripts/notify_discord.py",
                "timeout": 10,
                "statusMessage": "Enviando notificação para Discord..."
            }
        ]
    }

    if "Notification" not in settings["hooks"]:
        settings["hooks"]["Notification"] = []

    settings["hooks"]["Notification"].append(notification_hook)

    # Salva
    save_settings(settings)

    print(f"✅ Configuração salva em: {SETTINGS_FILE}")
    return True

def show_status():
    """Mostra status atual da configuração"""
    settings = load_settings()

    print("📊 Status das Notificações\n")

    # Webhook
    webhook = settings.get("env", {}).get("DISCORD_WEBHOOK_URL", "")
    if webhook:
        # Mascara webhook
        masked = webhook[:50] + "..." + webhook[-20:]
        print(f"🔗 Webhook: {masked}")
    else:
        print("🔗 Webhook: ❌ Não configurado")

    # UTF-8
    utf8 = settings.get("env", {}).get("PYTHONUTF8", "")
    print(f"📝 PYTHONUTF8: {'✅ ' + utf8 if utf8 else '❌ Não configurado'}")

    # Hooks
    hooks = settings.get("hooks", {}).get("Notification", [])
    if hooks:
        print(f"🔔 Hooks ativos: {len(hooks)}")
        for h in hooks:
            matcher = h.get("matcher", "?")
            print(f"   • Matcher: {matcher}")
    else:
        print("🔔 Hooks: ❌ Nenhum configurado")

    # Testa conexão se tiver webhook
    if webhook:
        print("\n🧪 Testando conexão...")
        success, message = test_webhook(webhook)
        if success:
            print("✅ Webhook funcionando!")
        else:
            print(f"❌ Erro no webhook: {message}")

def main():
    parser = argparse.ArgumentParser(
        description="Configura notificações Discord para Claude Code"
    )
    parser.add_argument(
        "--webhook", "-w",
        help="URL do webhook Discord"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Testa o webhook configurado"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Mostra status da configuração"
    )

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.test:
        settings = load_settings()
        webhook = settings.get("env", {}).get("DISCORD_WEBHOOK_URL", "")
        if not webhook:
            print("❌ Nenhum webhook configurado")
            sys.exit(1)
        success, message = test_webhook(webhook)
        if success:
            print("✅ Webhook funcionando!")
        else:
            print(f"❌ Erro: {message}")
            sys.exit(1)
    elif args.webhook:
        configure_notifications(args.webhook)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
