# -*- coding: utf-8 -*-
"""
Prompt de Tools Guide - Discord Module.

Guia de uso das tools MCP do Discord.

DOC: DDD Migration - Prompts Module
"""

DISCORD_TOOLS_GUIDE = """
**Tools MCP Discord Disponíveis:**

**Mensagens Básicas:**
- `reply`: Enviar mensagem simples (suporta threading e anexos)
- `edit_message`: Editar mensagem existente
- `react`: Adicionar emoji react

**Mensagens Ricas:**
- `send_embed`: Enviar embed com campos, cor, rodapé
- `send_buttons`: Enviar embed com botões interativos
- `send_menu`: Enviar menu suspenso (dropdown)
- `send_progress`: Enviar/ATUALIZAR barra de progresso (use tracking_id!)

**Consulta:**
- `fetch_messages`: Buscar histórico de mensagens

**Componentes:**
- `update_component`: Atualizar componente existente (desabilitar botões, atualizar progresso)

**Threads:**
- `create_thread`: Criar thread a partir de mensagem
- `list_threads`: Listar threads do canal
- `archive_thread`: Arquivar thread
- `rename_thread`: Renomear thread

**Anexos:**
- `download_attachment`: Baixar anexos para inbox local

**Dicas Importantes:**
1. Use `tracking_id` em `send_progress` para ATUALIZAR a mesma mensagem, não criar novas
2. Use `update_component` com `disable_buttons: true` após clique em botões
3. Sempre verifique `attachment_count` após `fetch_messages` antes de processar
"""


def get_tools_guide_prompt() -> str:
    """Retorna guia de tools do Discord."""
    return DISCORD_TOOLS_GUIDE
