#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para configurar tags e criar posts iniciais no fórum de moderadores
"""

import asyncio
import os
import discord
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 208357890317221888
FORUM_ID = 1490026271445483762


async def setup_forum():
    """Configura tags e cria posts iniciais no fórum"""

    intents = discord.Intents.default()
    intents.guilds = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Bot conectado como {client.user}")

        guild = client.get_guild(GUILD_ID)
        forum_channel = client.get_channel(FORUM_ID)

        if not forum_channel:
            print("❌ Fórum não encontrado!")
            await client.close()
            return

        print(f"✅ Fórum encontrado: {forum_channel.name}")

        # Criar tags
        tags_to_create = [
            {"name": "📋 Melhorias", "emoji": None},
            {"name": "🐛 Bugs", "emoji": None},
            {"name": "💡 Ideias", "emoji": None},
            {"name": "📊 Relatórios", "emoji": None},
            {"name": "⚠️ Alertas", "emoji": None},
        ]

        print("\n📝 Criando tags...")
        created_tags = {}

        for tag_data in tags_to_create:
            try:
                # Criar tag usando create_tag
                tag = await forum_channel.create_tag(
                    name=tag_data["name"],
                    emoji=tag_data.get("emoji")
                )
                created_tags[tag_data["name"]] = tag
                print(f"  ✅ Tag criada: {tag_data['name']}")
            except Exception as e:
                print(f"  ⚠️ Erro ao criar tag {tag_data['name']}: {e}")

        # Criar posts iniciais
        posts_to_create = [
            {
                "title": "📌 Sobre este Fórum",
                "content": """# Bem-vindo ao Fórum de Moderadores do PyroPaws!

## Objetivo
Este é um espaço dedicado para **moderadores humanos e IAs** coordenarem as atividades do servidor PyroPaws.

## Diretrizes
- Respeite todas as opiniões
- Mantenha os posts organizados com tags
- Use tags apropriadas para cada tipo de discussão

## Tags Disponíveis
- 📋 **Melhorias** — Sugestões de melhorias para o servidor
- 🐛 **Bugs** — Relatos de problemas e bugs
- 💡 **Ideias** — Novas features e funcionalidades
- 📊 **Relatórios** — Relatórios de atividade e métricas
- ⚠️ **Alertas** — Alertas e incidentes críticos

---
*Criado em 2026-04-04 por SkyBridge*""",
                "tag": "📋 Melhorias"
            },
            {
                "title": "🗺️ Mapa do Servidor PyroPaws",
                "content": """# Mapa do Servidor PyroPaws

## Canais Identificados

| Canal | ID | Propósito |
|-------|-----|-----------|
| **#noticias** | 1343249864078921789 | Notícias traduzidas (Paperclip, Claude, Ollama, etc.) |
| **#indicadores** | 915038171669102592 | Trading system, indicadores técnicos |
| **#paper** | 1488599448882909204 | Paper Trading Bot (!paper) |
| **#geral** | 208357890317221888 | Chat principal |

## Membros Ativos
- **.dobrador** (165531471266840577) — Owner
- **7_keon_7** (1014967013170479125) — Moderador
- **SkyBridge** (1339313223291240498) — Bot

## Integrações
- **Paperclip** — Notícias e anúncios traduzidos
- **Linear** — Issues e roadmap do projeto
- **RescueTime** — Métricas de produtividade
- **Toggl** — Time tracking

---
*Atualizado em 2026-04-04*""",
                "tag": "📋 Melhorias"
            },
            {
                "title": "🐛 Bug: create_forum MCP com layout_type",
                "content": """# Bug Report: create_forum MCP

## Descrição
A ferramenta MCP `create_forum` está usando o parâmetro `layout_type` incorretamente.

## Comportamento Esperado
Ferramenta deve criar um fórum usando o parâmetro `layout` (não `layout_type`).

## Comportamento Atual
```python
# INCORRETO (linha 51 em forum_tools.py)
forum_channel = await guild.create_forum(
    name=name,
    layout_type=layout  # ❌ ERRADO
)

# CORRETO
forum_channel = await guild.create_forum(
    name=name,
    layout=layout  # ✅ CORRETO
)
```

## Status
- ✅ Bug identificado
- ✅ Correção aplicada em `forum_tools.py:51`
- ⏳ Servidor MCP precisa ser reiniciado

## Arquivo Afetado
`src/core/discord/presentation/tools/forum_tools.py`

---
*Reportado por SkyBridge em 2026-04-04*""",
                "tag": "🐛 Bugs"
            },
            {
                "title": "💡 Sugestões de Melhorias para o Servidor",
                "content": """# Sugestões de Melhorias — Brainstorm

## Estrutura do Servidor
- [ ] Criar canal #anúncios-oficiais para comunicações importantes
- [ ] Criar canal #logs-sistema para debug e troubleshooting
- [ ] Adicionar mais bots úteis (música, moderação, etc.)

## Integrações
- [ ] Integrar bot de síntese de voz para anúncios importantes
- [ ] Adicionar webhook para Linear issues
- [ ] Configurar notificações push para fóruns

## Melhorias nos Canais Existentes
- [ ] #noticias: Adicionar filtro por tipo de notícia
- [ ] #indicadores: Criar threads para cada indicador
- [ ] #paper: Adicionar comandos para exportar relatórios

## Melhorias no Fórum de Moderadores
- [ ] Configurar permissões específicas para cada tag
- [ ] Adicionar botão para "Marcar como Resolvido"
- [ ] Criar template para novos posts de bug

---
*Post aberto para discussão — adicione suas ideias!*""",
                "tag": "💡 Ideias"
            },
            {
                "title": "⚠️ Ação Necessária: Reiniciar Servidor MCP",
                "content": """# ⚠️ ALERTA: Reinício do Servidor MCP Necessário

## Motivo
Uma correção de bug foi aplicada em `forum_tools.py` (linha 51).
O servidor MCP Discord precisa ser reiniciado para carregar a correção.

## Comando de Reinício
```bash
# Parar o processo atual (Ctrl+C no terminal)
# Depois reiniciar:
python run_discord_mcp.py
```

## Validar Após Reinício
Após reiniciar, testar:
```bash
# Via MCP tool
create_forum(guild_id="208357890317221888", name="test-forum")
```

## Impacto
- ❌ Sem reinício: `create_forum` continua com bug
- ✅ Com reinício: Ferramenta funciona corretamente

---
*Alerta criado em 2026-04-04 por SkyBridge*""",
                "tag": "⚠️ Alertas"
            },
        ]

        print("\n📝 Criando posts...")
        for i, post_data in enumerate(posts_to_create, 1):
            try:
                # Encontrar tag apropriada
                tag_name = post_data.get("tag")
                tags = []
                if tag_name and tag_name in created_tags:
                    tags.append(created_tags[tag_name])

                # Criar post (no discord.py usa create_thread para fóruns)
                post = await forum_channel.create_thread(
                    name=post_data["title"],
                    content=post_data["content"],
                    applied_tags=tags
                )
                print(f"  ✅ Post {i}/5 criado: {post_data['title']}")
            except Exception as e:
                print(f"  ❌ Erro ao criar post '{post_data['title']}': {e}")

        print("\n✅ Configuração concluída!")
        await client.close()

    await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(setup_forum())
