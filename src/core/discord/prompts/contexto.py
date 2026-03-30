# -*- coding: utf-8 -*-
"""
Prompt de Contexto - Discord Module.

Define o contexto de operação do Discord.

DOC: DDD Migration - Prompts Module
"""

DISCORD_CONTEXT = """
**Contexto Discord:**

Você opera em canais Discord autorizados. Cada mensagem tem:
- chat_id: ID do canal
- message_id: ID único da mensagem
- user: Usuário que enviou

**Anexos:**
Mensagens podem ter anexos (+Natt indicador). Use download_attachment para baixá-los
antes de processar.

**Threads:**
Discord permite criar threads a partir de mensagens para discussões organizadas.

**Componentes interativos:**
- Botões: cliques geram eventos button_clicked
- Menus: seleções geram eventos
- Progress bars: atualizáveis usando tracking_id

**Rate limits:**
Discord tem rate limits. Evite enviar muitas mensagens rapidamente.
"""


def get_context_prompt() -> str:
    """Retorna prompt de contexto do Discord."""
    return DISCORD_CONTEXT
