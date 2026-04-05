# -*- coding: utf-8 -*-
"""
Tool: quick_react

Adiciona reação emoji rápida com opções pré-definidas para votação/feedback.

DOC: DDD Migration - Presentation Layer
"""

from __future__ import annotations

import logging
from typing import Any

from ...application.services.discord_service import DiscordService

logger = logging.getLogger(__name__)

# Emojis pré-definidos para diferentes contextos
QUICK_REACTIONS = {
    "vote": {
        "👍": "Concordo / Positivo",
        "👎": "Discordo / Negativo",
        "🤷": "Neutro / Indeciso",
        "🔥": "Prioridade Alta",
        "✅": "Concluído / Feito",
    },
    "priority": {
        "🔴": "Crítico / Urgente",
        "🟠": "Alta Prioridade",
        "🟡": "Média Prioridade",
        "🟢": "Baixa Prioridade",
        "⚪": "Backlog",
    },
    "sentiment": {
        "👍": "Positivo",
        "❤️": "Amei",
        "😂": "Engraçado",
        "🤔": "Interessante",
        "😕": "Confuso",
        "😡": "Frustrado",
    },
    "binary": {
        "✅": "Sim / Aprovo",
        "❌": "Não / Rejeito",
        "❓": "Dúvida",
    },
    "tshirt": {
        "👕": "Pequeno (S)",
        "👚": "Médio (M)",
        "👔": "Grande (L)",
        "🧥": "Extra Grande (XL)",
    },
}


async def handle_quick_react(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Handler para tool quick_react.

    Permite adicionar reações rápidas pré-definidas para votação/feedback.

    Args:
        discord_service: Instância do DiscordService
        args: {chat_id, message_id, category, emoji}

    Returns:
        Dict com status e emojis adicionados
    """
    chat_id = args.get("chat_id")
    message_id = args.get("message_id")
    category = args.get("category", "vote")
    emoji = args.get("emoji")

    if not all([chat_id, message_id]):
        return {
            "status": "error",
            "error": "chat_id e message_id são obrigatórios"
        }

    # Se emoji fornecido, adiciona apenas ele
    if emoji:
        success = await discord_service.add_reaction(
            channel_id=chat_id,
            message_id=message_id,
            emoji=emoji,
        )
        return {
            "status": "success" if success else "failed",
            "emoji": emoji,
            "meaning": QUICK_REACTIONS.get(category, {}).get(emoji, ""),
        }

    # Se não, adiciona todos os emojis da categoria (poll)
    emojis_to_add = QUICK_REACTIONS.get(category, QUICK_REACTIONS["vote"])
    results = []

    for emoji_to_add in emojis_to_add.keys():
        try:
            success = await discord_service.add_reaction(
                channel_id=chat_id,
                message_id=message_id,
                emoji=emoji_to_add,
            )
            results.append({
                "emoji": emoji_to_add,
                "success": success,
                "meaning": emojis_to_add[emoji_to_add]
            })
        except Exception as e:
            logger.warning(f"Falha ao adicionar {emoji_to_add}: {e}")
            results.append({
                "emoji": emoji_to_add,
                "success": False,
                "error": str(e)
            })

    return {
        "status": "success",
        "category": category,
        "added": results,
        "message": f"Adicionadas {len([r for r in results if r['success']])} reações"
    }


async def handle_list_quick_reactions(
    discord_service: DiscordService,
    args: dict[str, Any]
) -> dict[str, Any]:
    """
    Lista as categorias e emojis disponíveis para reações rápidas.

    Args:
        discord_service: Instância do DiscordService (não usado, mas mantido para consistência)
        args: {category} (opcional)

    Returns:
        Dict com categorias e emojis disponíveis
    """
    category = args.get("category")

    if category:
        return {
            "status": "success",
            "category": category,
            "emojis": QUICK_REACTIONS.get(category, {}),
        }

    return {
        "status": "success",
        "categories": {
            cat_name: {
                "description": _get_category_description(cat_name),
                "emojis": list(emojis.keys())
            }
            for cat_name, emojis in QUICK_REACTIONS.items()
        }
    }


def _get_category_description(category: str) -> str:
    """Retorna descrição da categoria."""
    descriptions = {
        "vote": "Votação simples (concordar/discordo/neutro)",
        "priority": "Classificação de prioridade (crítico/baixa/etc)",
        "sentiment": "Sentimento/emoção (positivo/negativo/etc)",
        "binary": "Decisão binária (sim/não/dúvida)",
        "tshirt": "Tamanho de camiseta (S/M/L/XL)",
    }
    return descriptions.get(category, f"Categoria: {category}")


# Tool definitions para registro no MCP

QUICK_REACT_TOOL = {
    "name": "quick_react",
    "description": (
        "Add quick emoji reactions for voting/feedback. "
        "Predefined categories: vote, priority, sentiment, binary, tshirt. "
        "If emoji is provided, adds only that emoji. If not, adds all emojis from category."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "chat_id": {"type": "string", "description": "Channel ID"},
            "message_id": {"type": "string", "description": "Message ID"},
            "category": {
                "type": "string",
                "enum": ["vote", "priority", "sentiment", "binary", "tshirt"],
                "default": "vote",
                "description": "Category of quick reactions"
            },
            "emoji": {"type": "string", "description": "Specific emoji to add (optional)"},
        },
        "required": ["chat_id", "message_id"],
    },
}

LIST_QUICK_REACTIONS_TOOL = {
    "name": "list_quick_reactions",
    "description": "List available quick reaction categories and emojis.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["vote", "priority", "sentiment", "binary", "tshirt"],
                "description": "Category to list (optional, shows all if not provided)"
            },
        },
    },
}
