# -*- coding: utf-8 -*-
"""
Tool MCP para listar categorias do servidor Discord.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.discord.application.services.discord_service import DiscordService

LIST_CATEGORIES_TOOL = TOOL_DEFINITION = {
    "name": "list_categories",
    "description": "Lista todas as categorias de um servidor Discord, mostrando nome, posição e canais em cada categoria",
    "inputSchema": {
        "type": "object",
        "properties": {
            "guild_id": {
                "type": "string",
                "description": "ID do servidor Discord (opcional, usa o primeiro disponível se não fornecido)",
            },
        },
    },
}


async def handle_list_categories(discord_service: "DiscordService", arguments: dict) -> dict:
    """
    Lista todas as categorias de um servidor Discord.

    Args:
        discord_service: Instância do DiscordService
        arguments: Dicionário com argumentos da tool

    Returns:
        dict com lista de categorias
    """
    guild_id = arguments.get("guild_id")

    client = discord_service.client

    try:
        # Obter guild
        if guild_id:
            guild = client.get_guild(int(guild_id))
            if not guild:
                # Tenta fetch via API
                guild = await client.fetch_guild(int(guild_id))
        else:
            # Usa o primeiro guild disponível
            guilds = client.guilds
            if not guilds:
                return {"error": "Bot não está em nenhum servidor"}
            guild = guilds[0]

        # Buscar canais do guild para obter categorias
        categories = {}
        for channel in guild.channels:
            if channel.category:
                cat_id = str(channel.category.id)
                if cat_id not in categories:
                    categories[cat_id] = {
                        "id": cat_id,
                        "name": channel.category.name,
                        "position": channel.category.position,
                        "channels": [],
                    }
                # Adiciona canal à categoria
                categories[cat_id]["channels"].append({
                    "id": str(channel.id),
                    "name": channel.name,
                    "type": str(channel.type),
                })

        # Ordenar por posição
        sorted_categories = sorted(
            categories.values(),
            key=lambda x: x["position"]
        )

        return {
            "guild": {
                "id": str(guild.id),
                "name": guild.name,
            },
            "categories": sorted_categories,
            "total": len(sorted_categories),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
