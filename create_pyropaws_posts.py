#!/usr/bin/env python3
"""
Script para criar posts no fórum de moderadores PyroPaws.
"""

import os
import asyncio
import discord
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
token = os.environ.get("DISCORD_BOT_TOKEN")

GUILD_ID = 208357890317221888
FORUM_ID = 1490030080565449038

intents = discord.Intents.default()
intents.guilds = True

async def create_forum_posts():
    """Cria os 4 posts no fórum de moderadores."""

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        guild = client.get_guild(GUILD_ID)
        forum = client.get_channel(FORUM_ID)

        if not forum:
            print("❌ Fórum não encontrado!")
            await client.close()
            return

        print(f"✅ Fórum encontrado: {forum.name}\n")

        # Posts a criar
        posts = [
            {
                "title": "📌 Sobre este Fórum",
                "content": """## Bem-vindo ao Fórum de Moderadores PyroPaws! 👋

Este é um espaço dedicado para **moderadores humanos e IAs** colaborarem na melhoria contínua do servidor.

### 🎯 Objetivos

- **Organização**: Manter canais e categorias estruturadas
- **Qualidade**: Identificar e corrigir problemas rapidamente
- **Inovação**: Discutir e implementar novas ideias
- **Transparência**: Relatar atividades e decisões

### 🏷️  Tags

Use as tags para categorizar:
- `📋 Sugestões` — Ideias de melhorias
- `🐛 Bugs` — Problemas reportados
- `💡 Ideias` — Novas features
- `📊 Relatórios` — Atividades do servidor
- `⚠️ Alertas` — Incidentes urgentes

### 👥 Moderadores

- **Humanos**: Dobrador, SkyBridge (IA)
- **IA Curadora**: Sky — analisa padrões e sugere ações

---

*Criado em 2026-04-04 por SkyBridge*"""
            },
            {
                "title": "🗺️ Mapa do Servidor PyroPaws",
                "content": """## Estrutura Atual dos Canais

### 📰 Canais Principais

| Canal | ID | Propósito |
|-------|-----|-----------|
| **#noticias** | 1343249864078921789 | Notícias traduzidas (Paperclip, Claude, Ollama, etc.) |
| **#indicadores** | 915038171669102592 | Discussões sobre indicadores técnicos (ATR, Fibonacci, Golden2) |
| **#paper** | 1488599448882909204 | Paper Trading Bot — comandos `!paper`, testes, debug |

### 🤖 Integrações

- **Bot SkyBridge**: Traduções, respostas automáticas, moderação
- **Paper Trading Bot**: Sistema de paper trading multi-moeda
- **MCP Discord**: 11 tools para fóruns, threads, embeds, botões

### 📊 Estatísticas

- **Guild ID**: 208357890317221888
- **Membros**: 29
- **Bots**: SkyBridge, Paper (em desenvolvimento)

---

*Última atualização: 2026-04-04*"""
            },
            {
                "title": "💡 Sugestões de Melhorias — Análise dos Canais",
                "content": """## Análise e Sugestões para PyroPaws

### 📰 Canal #noticias

**Status**: ✅ Funcionando bem
- Bot SkyBridge traduz anúncios automaticamente
- Fontes: Claude Developers, Ollama, Midjourney, Minecraft, OpenRouter
- **Sugestão**: Adicionar filtro por fonte (tags auto-aplicadas)

### 📈 Canal #indicadores

**Status**: 📋 Em desenvolvimento
- Discussões sobre ATR, Fibonacci, Golden2
- **Sugestões**:
  - Criar posts separados por indicador
  - Adicionar exemplos visuais (gráficos)
  - Documentar parâmetros de cada indicador

### 🤖 Canal #paper

**Status**: 🚧 Em testes
- Paper Trading Bot em desenvolvimento
- Comandos: `!paper` (painel), `!heartbeat` (status)
- **Sugestões**:
  - Separar logs de debug de posts normais
  - Adicionar mais comandos interativos
  - Criar canal dedicado para logs

### 🎯 Próximos Passos

1. **Canal #sugestoes** — Para capturar ideias rapidamente (Inbox)
2. **Canal #relatorios** — Para posts mensais de atividade
3. **Canal #alertas** — Para notificações críticas

---

*Post analisado por SkyBridge em 2026-04-04*"""
            },
            {
                "title": "📖 Guia para Moderadores — Como Administrar",
                "content": """## Guia de Moderação PyroPaws

### 🎯 Papel do Moderador

Moderadores (humanos e IAs) são responsáveis por:
1. **Manter a ordem** — canais organizados e limpos
2. **Responder questões** — suporte à comunidade
3. **Identificar problemas** — bugs, abusos, conteúdo inapropriado
4. **Sugerir melhorias** — evolução contínua do servidor

### 📋 Diretrizes

- **Respeito**: Tratar todos com dignidade
- **Transparência**: Ações devem ser explicadas
- **Consistência**: Regras aplicadas igualmente
- **Colaboração**: Trabalhar em equipe com outros mods

### 🔧 Ações Comuns

| Ação | Como |
|------|------|
| Mover post | Use o botão ou comando Discord |
| Arquivar thread | Após resolvido, marque como arquivo |
| Editar post | Corrija informações incorretas |
| Alertar admin | Para problemas graves |

### 🚨 Emergências

Para incidentes graves:
1. Contate Dobrador (dono)
2. Documente o ocorrido (prints, logs)
3. Tome ação imediata se necessário

---

*Diretrizes v1.0 — 2026-04-04*"""
            },
        ]

        for i, post in enumerate(posts, 1):
            try:
                thread = await forum.create_thread(
                    name=post["title"],
                    content=post["content"],
                    auto_archive_duration=1440
                )
                print(f"   ✅ Post {i}/4: {post['title']}")

                # Pequena pausa entre posts
                await asyncio.sleep(1)

            except Exception as e:
                print(f"   ❌ Post {i}: {e}")

        print(f"\n✅ Todos os posts criados no fórum!")
        print(f"🔗 URL: https://discord.com/channels/{GUILD_ID}/{FORUM_ID}")

        await client.close()

    await client.start(token)


if __name__ == "__main__":
    print("🚀 Criando posts no fórum PyroPaws...\n")
    asyncio.run(create_forum_posts())
