#!/usr/bin/env python3
"""Script para obter OAuth Token do YouTube.

Uso:
    1. Configure CLIENT_ID e CLIENT_SECRET abaixo
    2. Rode: python scripts/get_youtube_token.py
    3. Autorize no browser
    4. Copie o token impresso
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google_auth_oauthlib.flow import InstalledAppFlow


# Configure aqui OU use variáveis de ambiente
CLIENT_CONFIG = {
    "installed": {
        "client_id": os.getenv("YOUTUBE_CLIENT_ID", "SEU_CLIENT_ID_AQUI"),
        "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET", "SEU_CLIENT_SECRET_AQUI"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8080"]
    }
}

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly"
]


def get_token():
    """Obtém access token via OAuth 2.0 flow."""

    # Validar configuração
    if CLIENT_CONFIG["installed"]["client_id"] == "SEU_CLIENT_ID_AQUI":
        print("❌ Configure CLIENT_ID e CLIENT_SECRET no script!")
        print("\nOu use variáveis de ambiente:")
        print("  export YOUTUBE_CLIENT_ID=seu_id")
        print("  export YOUTUBE_CLIENT_SECRET=seu_secret")
        return None

    # Criar OAuth flow
    flow = InstalledAppFlow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES
    )

    # Abrir browser para autorização
    print("🔐 Abrindo browser para autorização...")
    print("   Você será redirecionado para uma página do Google.\n")

    credentials = flow.run_local_server(
        port=8080,
        authorization_prompt_message="",
        success_message="✅ Autorização bem-sucedida! Você pode fechar esta aba."
    )

    # Imprimir tokens
    print("\n" + "="*60)
    print("  ✅ AUTORIZAÇÃO CONCLUÍDA!")
    print("="*60)
    print(f"\n🔑 Access Token:\n{credentials.token}\n")
    print(f"🔄 Refresh Token:\n{credentials.refresh_token}\n")
    print(f"⏰ Expira em: {credentials.expiry} segundos\n")
    print("="*60)
    print("\nUse o access_token para testar:")
    print("  export GOOGLE_OAUTH_TOKEN='seu_token_aqui'")
    print("  python scripts/youtube_api_test.py\n")

    return credentials


def main():
    """Função principal."""
    print("📺 YouTube OAuth Token Generator")
    print("="*60)
    print()

    try:
        credentials = get_token()

        if credentials:
            print("✅ Tokens obtidos com sucesso!")
            return 0
        else:
            print("❌ Erro ao obter tokens.")
            return 1

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
