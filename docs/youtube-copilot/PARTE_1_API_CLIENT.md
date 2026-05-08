# YouTube Copilot - Parte 1: API Client

## O que foi criado

### 1. YouTubeAPIClient
**Arquivo:** `src/core/youtube/infrastructure/youtube_api_client.py`

Cliente Python para YouTube Data API v3 com funções para:
- Listar playlists do usuário
- Buscar itens de uma playlist (favoritos, watch later)
- Obter detalhes de vídeos
- Parse de durações ISO 8601

### 2. Testes
**Arquivo:** `tests/integration/youtube/test_youtube_api_client.py`

Testes TDD:
- Testes de integração (requer token real)
- Testes unitários (validação de input)

### 3. Scripts de Teste
**Arquivo:** `scripts/youtube_api_test.py`

Script manual para validar a integração:
```bash
export GOOGLE_OAUTH_TOKEN=seu_token
python scripts/youtube_api_test.py
```

### 4. Gerador de Token
**Arquivo:** `scripts/get_youtube_token.py'

Script para obter OAuth token pela primeira vez.

## Como Testar

### Passo 1: Configurar Google Cloud

Siga o guia: `docs/youtube-copilot/YOUTUBE_API_SETUP.md`

Resumo:
1. Criar projeto no Google Cloud Console
2. Habilitar YouTube Data API v3
3. Criar OAuth Client ID (Desktop app)
4. Copiar Client ID e Secret

### Passo 2: Obter Token

```bash
# Configure as credenciais
export YOUTUBE_CLIENT_ID="seu_client_id"
export YOUTUBE_CLIENT_SECRET="seu_client_secret"

# Rode o gerador
python scripts/get_youtube_token.py
```

O browser vai abrir, você autoriza, e o script imprime o token.

### Passo 3: Testar API Client

```bash
# Export o token obtido
export GOOGLE_OAUTH_TOKEN="seu_access_token"

# Rode o teste
python scripts/youtube_api_test.py
```

Saída esperada:
```
==================================================
  FAVORITOS (Liked Videos)
==================================================

Total: 10 vídeos (mostrando primeiros 10)

1. Amazing Python Tutorial
    Canal: Corey Schafer
    Duração: 45min 23s
    ID: abc123

...
```

## Estrutura do Código

```
src/core/youtube/infrastructure/
├── youtube_api_client.py      # Cliente principal
├── yt_dlp_adapter.py         # (existente) Download de vídeos
└── rag_repository.py         # (existente) Busca semântica

tests/integration/youtube/
├── __init__.py
└── test_youtube_api_client.py

scripts/
├── youtube_api_test.py       # Teste manual
└── get_youtube_token.py      # Gerador de token

docs/youtube-copilot/
├── YOUTUBE_API_SETUP.md      # Guia de configuração
└── PARTE_1_API_CLIENT.md     # Este arquivo
```

## Próximos Passos

- [ ] Parte 2: State Repository (SQLite)
- [ ] Parte 3: Video Analyzer (priorização)
- [ ] Parte 4: Discord Notifier (mensagens proativas)
- [ ] Parte 5: Daemon/Scheduler (poll contínuo)

> "Parte 1: API Client - FEITO! ✅" – made by Sky 📺
