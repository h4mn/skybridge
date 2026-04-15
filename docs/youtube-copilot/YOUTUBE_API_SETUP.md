# YouTube API Setup - Guia de Configuração

## Visão Geral

Para usar o YouTube Copilot, você precisa de acesso à YouTube Data API v3 via OAuth 2.0.

## Pré-requisitos

1. **Conta Google** - Você já tem uma
2. **Projeto Google Cloud** - Vamos criar
3. **Python 3.11+** - Já instalado

## Passo 1: Criar Projeto Google Cloud

1. Acesse: https://console.cloud.google.com/
2. Crie um novo projeto (ou use existente)
3. Anote o **Project ID**

## Passo 2: Habilitar YouTube Data API

1. No console, vá em: **APIs & Services** → **Library**
2. Pesquise: "YouTube Data API v3"
3. Clique em **Enable**

## Passo 3: Configurar OAuth 2.0

### 3.1 Criar OAuth Client ID

1. Vá em: **APIs & Services** → **Credentials**
2. Clique: **+ Create Credentials** → **OAuth client ID**
3. Se pedir, configure **OAuth consent screen** primeiro:
   - Choose: **External**
   - App name: "Skybridge YouTube Copilot"
   - User support email: seu email
   - Developer contact: seu email
   - Continue e scopes (vamos adicionar depois)

4. Criar OAuth Client ID:
   - Application type: **Desktop app**
   - Name: "Skybridge YouTube Copilot"
   - Create

5. **COPIE o Client ID** e **Client Secret** (vamos precisar)

### 3.2 Configurar Scopes

Na OAuth consent screen, adicione estes scopes:

```
https://www.googleapis.com/auth/youtube.readonly
```

## Passo 4: Obter Access Token (Primeira Vez)

### Opção A: Script Manual (Recomendado)

Crie e rode:

```python
# scripts/get_youtube_token.py

from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_CONFIG = {
    "installed": {
        "client_id": "SEU_CLIENT_ID_AQUI",
        "client_secret": "SEU_CLIENT_SECRET_AQUI",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8080"]
    }
}

def get_token():
    flow = InstalledAppFlow.from_client_config(
        CLIENT_CONFIG,
        scopes=["https://www.googleapis.com/auth/youtube.readonly"]
    )

    flow.run_local_server(port=8080)

    # Print the access token
    print(f"\n✅ Access Token: {flow.credentials.token}")
    print(f"✅ Refresh Token: {flow.credentials.refresh_token}")

    return flow.credentials

if __name__ == "__main__":
    get_token()
```

Rode:
```bash
python scripts/get_youtube_token.py
```

O browser vai abrir, você autoriza, e o script imprime o token.

### Opção B: Usar gcloud CLI

```bash
# Instale gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Autentique
gcloud auth login

# Get access token
gcloud auth print-access-token
```

## Passo 5: Testar

```bash
# Export o token
export GOOGLE_OAUTH_TOKEN="seu_token_aqui"

# Rode o teste
python scripts/youtube_api_test.py
```

## Passo 6: Salvar Token (Permanente)

Para não ter que rodar toda vez, salve o refresh token no settings.json:

```json
{
  "youtube": {
    "client_id": "SEU_CLIENT_ID",
    "client_secret": "SEU_CLIENT_SECRET",
    "refresh_token": "SEU_REFRESH_TOKEN"
  }
}
```

E crie um helper que auto-renova o token.

## Troubleshooting

### Erro: "Invalid Credentials"
- Token expirou (access token dura 1 hora)
- Use refresh token para obter novo access token

### Erro: "Access Denied"
- Verifique se o scope está correto
- Verifique se OAuth consent screen está configurado

### Erro: "Quota Exceeded"
- YouTube API tem quota de 10.000 unidades/dia
- Cada chamada consome ~1-5 unidades
- Implemente cache para reduzir chamadas

## Recursos

- [YouTube Data API Docs](https://developers.google.com/youtube/v3)
- [OAuth 2.0 para Apps Desktop](https://developers.google.com/identity/protocols/oauth2/native-app)

> "Autenticação é chato, mas necessário!" – made by Sky 🔐
