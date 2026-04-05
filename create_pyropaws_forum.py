#!/usr/bin/env python3
"""
Script para criar o Fórum de Moderadores no servidor PyroPaws.

Executa:
    python create_pyropaws_forum.py

Requisitos:
    - discord.py instalado
    - DISCORD_BOT_TOKEN no ambiente ou .env
"""

import os
import sys
import asyncio
from pathlib import Path

# Adiciona src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    import discord
except ImportError:
    print("Instale discord.py: pip install discord.py")
    sys.exit(1)

# Carrega token
token = os.environ.get("DISCORD_BOT_TOKEN")
if not token:
    # Tenta ler do .env
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").split("\n"):
            if line.startswith("DISCORD_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip()
                break

if not token:
    print("ERRO: DISCORD_BOT_TOKEN não encontrado")
    print("Defina a variável de ambiente ou adicione ao .env")
    sys.exit(1)

GUILD_ID = 208357890317221888

intents = discord.Intents.default()
intents.guilds = True


async def create_moderator_forum():
    """Cria o fórum de moderadores com tags e posts iniciais."""

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"\n{'='*60}")
        print(f"Conectado como {client.user}")
        print(f"{'='*60}\n")

        guild = client.get_guild(GUILD_ID)
        if not guild:
            print(f"❌ Servidor PyroPaws (ID: {GUILD_ID}) não encontrado")
            await client.close()
            return

        print(f"📋 Servidor: {guild.name}")
        print(f"👥 Membros: {guild.member_count}\n")

        # 1. Criar Fórum
        print("🔨 Criando fórum de moderadores...")
        try:
            forum_channel = await guild.create_forum(
                name="📋 Forum Moderadores",
                topic="Espaço para moderadores humanos e IAs discutirem melhorias, bugs, ideias e relatórios do PyroPaws.",
            )
            print(f"   ✅ Fórum criado: {forum_channel.name}")
            print(f"   📌 ID: {forum_channel.id}")
            print(f"   🔗 URL: https://discord.com/channels/{GUILD_ID}/{forum_channel.id}\n")
        except Exception as e:
            print(f"   ❌ Erro ao criar fórum: {e}")
            await client.close()
            return

        # 2. Criar Tags
        print("🏷️  Criando tags...")
        tags_data = [
            ("📋", "sugestoes", "Sugestões de Melhorias"),
            ("🐛", "bugs", "Bugs e Problemas"),
            ("💡", "ideias", "Ideias e Features"),
            ("📊", "relatorios", "Relatórios de Atividade"),
            ("⚠️", "alertas", "Alertas e Incidentes"),
        ]

        for emoji, slug, name in tags_data:
            try:
                await forum_channel.create_tag(name=name)
                print(f"   ✅ Tag: {name}")
            except Exception as e:
                print(f"   ⚠️  Tag {name}: {e}")

        # 3. Criar Posts Iniciais
        print("\n📝 Criando posts iniciais...")

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

*Criado em 2026-04-04 por SkyBridge*""",
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
- **Membros**: Variável
- **Bots**: SkyBridge, Paper (em desenvolvimento)

---

*Última atualização: 2026-04-04*""",
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

*Post analisado por SkyBridge em 2026-04-04*""",
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

*Diretrizes v1.0 — 2026-04-04*""",
            },
        ]

        for i, post in enumerate(posts, 1):
            try:
                await forum_channel.create_thread(
                    name=post["title"],
                    content=post["content"],
                    auto_archive_duration=1440,  # 24 horas
                )
                print(f"   ✅ Post {i}/4: {post['title']}")
            except Exception as e:
                print(f"   ⚠️  Post {i}: {e}")

        print(f"\n{'='*60}")
        print("✅ Fórum de Moderadores PyroPaws criado com sucesso!")
        print(f"{'='*60}\n")
        print(f"🔗 Acesse: https://discord.com/channels/{GUILD_ID}/{forum_channel.id}")

        await client.close()

    await client.start(token)


if __name__ == "__main__":
    print("🚀 Iniciando criação do Fórum PyroPaws...\n")
    asyncio.run(create_moderator_forum())
