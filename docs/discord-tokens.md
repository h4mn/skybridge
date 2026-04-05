# Discord Tokens - Skybridge

## Visão Geral

Skybridge utiliza **2 tokens Discord diferentes** para bots com propósitos distintos:

## Tokens

### 1. Sky (MCP Discord)

**Propósito:** Bot principal para integrações via MCP (Model Context Protocol)

- **Usado por:** `run_discord_mcp.py`
- **Localização:** `~/.claude/channels/discord/.env` (fora do projeto)
- **Variável:** `DISCORD_BOT_TOKEN`
- **Aplicação:** Skybridge no Discord Developer Portal

**Funções:**
- Recebe mensagens do Discord
- Envia embeds, botões e gráficos
- Processa interações via MCP
- Canais principais (#paper-heartbeat, etc.)

### 2. Paper Trading Bot

**Propósito:** Bot dedicado para operações do simulador de trading

- **Usado por:** `discord_bot_paper.py` (em desenvolvimento)
- **Localização:** `.env` (raiz do projeto)
- **Variável:** `DISCORD_PAPER_BOT_TOKEN`
- **Aplicação:** Paper Trading (nova aplicação)

**Funções:**
- Simula operações de compra/venda
- Envia painel Portfolio com dados reais
- Processa comandos de trading
- Gráficos profissionais de candlestick

## Configuração

### Criar Novo Bot Paper

1. Acesse https://discord.com/developers/applications
2. Clique "New Application"
3. Nome: "Paper Trading"
4. Avatar: use a imagem gerada no Gemini/IA
5. Vá em "Bot" → "Create Bot"
6. Copie o token e adicione ao `.env`:

```bash
DISCORD_PAPER_BOT_TOKEN=MTMzOTMx...
```

### Configurar Intents (Paper Bot)

- **Message Content Intent**: ✅ (Privileged)
- **Server Members Intent**: ❌
- **Presence Intent**: ❌

### Convite para Servidor

Use a URL de convite com escopo `bot`:
```
https://discord.com/api/oauth2/authorize?client_id=CLIENT_ID&permissions=274878024640&scope=bot
```

Permissões necessárias:
- Send Messages
- Embed Links
- Attach Files
- Use External Emojis
- Read Message History
- Add Reactions

## Segurança

⚠️ **NUNCA** commite tokens no repositório!

- `.env` está no `.gitignore`
- Tokens em arquivos locais (`~/.claude/`) não são versionados
- Ao criar novo bot, gere token novo e compartilhe apenas via `.env`

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     Discord Server                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐              ┌──────────────────────────┐  │
│  │  Sky (MCP)  │              │   Paper Trading Bot      │  │
│  │             │              │                          │  │
│  │  - Mensagens│              │  - Painel Portfolio      │  │
│  │  - Embeds   │              │  - Compra/Venda         │  │
│  │  - Botões   │              │  - Gráficos              │  │
│  │  - Gráficos │              │  - Dados reais Yahoo     │  │
│  └──────┬──────┘              └──────────┬───────────────┘  │
│         │                                │                   │
│         │         ┌──────────────────────┘                   │
│         │         │                                          │
│         ▼         ▼                                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Skybridge (Backend)                       │   │
│  │                                                       │   │
│  │  - Paper Module (DDD)                               │   │
│  │  - Queries (GetPortfolio, GetAssetDetail)            │   │
│  │  - Handlers (ConsultarPortfolioHandler)              │   │
│  │  - Events (PortfolioUpdatedEvent)                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Suporte

Problemas com tokens? Verifique:
1. Token válido (não expirado)
2. Bot está ativo no Discord Developer Portal
3. Correta variável de ambiente no `.env`
4. Permissões corretas no servidor

---

> "Dois tokens, propósitos distintos, arquitetura unificada" – made by Sky 🔑
