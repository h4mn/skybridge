# Fluxo de Clique em Botão - Discord MCP

> Baseado no código real em `src/core/discord/server.py` e `infrastructure/mcp_button_adapter.py`

---

## Diagrama de Sequência Completo

```mermaid
sequenceDiagram
    participant U as Usuário Discord
    participant DG as Discord Gateway
    participant DC as discord.py Client
    participant OI as on_interaction_create()
    participant BA as MCPButtonAdapter
    participant BH as ButtonClickHandler
    participant EP as EventPublisher
    participant SN as send_notification()
    participant CC as Claude Code

    U->>DG: 1. Clica no botão "Confirmar"
    DG->>DC: 2. Evento INTERACTION_CREATE<br/>type=component (2)
    DC->>OI: 3. on_interaction_create(interaction)<br/>server.py:397-474

    OI->>OI: 4. debug_log.write_text()<br/>Log: "HANDLER CHAMADO! Type: component"

    OI->>OI: 5. Verifica: interaction.type<br/>if != InteractionType.component → return

    OI->>OI: 6. await interaction.response.defer()<br/>Acknowledge não existe no discord.py 2.x<br/>Defer evita timeout (3s)

    OI->>BA: 7. await button_adapter.handle_interaction(interaction)<br/>infrastructure/mcp_button_adapter.py:50-92

    BA->>BA: 8. HandleButtonClickCommand.from_discord_interaction()<br/>Cria command com custom_id, label, user, etc.

    BA->>BH: 9. await self._handler.handle(command)<br/>application/handlers/button_click_handler.py

    BH->>BH: 10. Valida command<br/>Verifica se button_custom_id existe

    BH->>BH: 11. Processa ação do botão<br/>Executa lógica específica (se houver)

    BH->>EP: 12. await self._event_publisher.publish(<br/>  ButtonClickedEvent(<br/>    button_id=command.button_custom_id,<br/>    user_id=command.user_id<br/>  )<br/>)

    EP->>EP: 13. Evento publicado no EventBus<br/>Outros handlers podem reagir

    BH->>BA: 14. Retorna Result(is_success=True, message="...", data={...})

    BA->>SN: 15. await self._send_mcp_notification(<br/>  interaction,<br/>  command,<br/>  result<br/>)<br/>infrastructure/mcp_button_adapter.py:94-119

    BA->>BA: 16. Prepara notification payload<br/>notification = {<br/>  "button_id": command.button_custom_id,<br/>  "button_label": command.button_label,<br/>  "user": command.user_name,<br/>  "user_id": command.user_id,<br/>  "channel_id": command.channel_id,<br/>  "message_id": command.message_id,<br/>  "event_id": result.data.get("event_id"),<br/>  "ts": interaction.created_at.isoformat()<br/>}

    BA->>CC: 17. await self._server.send_notification(<br/>  "notifications/claude/button_clicked",<br/>  notification<br/>)

    Note over CC: PRIMEIRA notificação recebida<br/>method: "notifications/claude/button_clicked"

    BA->>OI: 18. Retorna {"status": "success", "message": "...", "data": {...}}

    OI->>OI: 19. logger.info(f"Interação processada: {result['message']}")

    OI->>OI: 20. Extrai informações do botão<br/>custom_id = interaction.data.get("custom_id")<br/>button_label = component.label (da mensagem original)

    OI->>OI: 21. Prepara SEGUNDA notification payload<br/>notification = {<br/>  "content": f"[button] {button_label} ({custom_id})",<br/>  "meta": {<br/>    "chat_id": str(interaction.channel_id),<br/>    "message_id": str(interaction.message.id),<br/>    "user": interaction.user.name,<br/>    "user_id": str(interaction.user.id),<br/>    "ts": interaction.created_at.isoformat(),<br/>    "interaction_type": "button_click",<br/>    "custom_id": custom_id,<br/>    "button_label": button_label<br/>  }<br/>}

    OI->>CC: 22. await self.send_notification(<br/>  "notifications/claude/channel",<br/>  notification<br/>)

    Note over CC: SEGUNDA notificação recebida<br/>method: "notifications/claude/channel"<br/>content: "[button] Confirmar (test_confirm)"

    CC->>U: 23. <channel source="discord"<br/>chat_id="..."<br/>message_id="..."<br/>user="..."<br/>ts="..."<br/>interaction_type="button_click"<br/>custom_id="test_confirm"<br/>button_label="Confirmar">[button] Confirmar (test_confirm)</channel>
```

---

## ⚠️ DUPLICAÇÃO DE NOTIFICAÇÃO DETECTADA

O código atual envia **DUAS notificações MCP** para cada clique em botão:

| Local | Method | Arquivo | Linha |
|-------|--------|---------|-------|
| MCPButtonAdapter | `notifications/claude/button_clicked` | `mcp_button_adapter.py` | 114 |
| on_interaction_create | `notifications/claude/channel` | `server.py` | 467 |

### Notificação 1: `notifications/claude/button_clicked`
```python
# infrastructure/mcp_button_adapter.py:94-119
async def _send_mcp_notification(self, interaction, command, result):
    notification = {
        "button_id": command.button_custom_id,
        "button_label": command.button_label,
        "user": command.user_name,
        "user_id": command.user_id,
        "channel_id": command.channel_id,
        "message_id": command.message_id,
        "event_id": result.data.get("event_id"),
        "ts": interaction.created_at.isoformat(),
    }
    await self._server.send_notification(
        "notifications/claude/button_clicked",
        notification,
    )
```

**Payload:**
```json
{
  "button_id": "test_confirm",
  "button_label": "Confirmar",
  "user": ".dobrador",
  "user_id": "165531471266840577",
  "channel_id": "1487521449781756066",
  "message_id": "1488312544627130401",
  "event_id": "evt_123",
  "ts": "2026-03-30T23:03:45.123000+00:00"
}
```

### Notificação 2: `notifications/claude/channel`
```python
# server.py:427-468 (adicionado na correção)
# ========================================
# CRÍTICO: Enviar notificação MCP para Claude Code
# ========================================
chat_id = str(interaction.channel_id)

custom_id = "unknown"
button_label = "unknown"

if interaction.data:
    custom_id = interaction.data.get("custom_id", "unknown")

try:
    message = interaction.message
    if message and message.components:
        for action_row in message.components:
            for component in action_row.children:
                if component.custom_id == custom_id:
                    button_label = component.label or custom_id
                    break
except Exception:
    button_label = custom_id

notification = {
    "content": f"[button] {button_label} ({custom_id})",
    "meta": {
        "chat_id": chat_id,
        "message_id": str(interaction.message.id) if interaction.message else "",
        "user": interaction.user.name,
        "user_id": str(interaction.user.id),
        "ts": interaction.created_at.isoformat(),
        "interaction_type": "button_click",
        "custom_id": custom_id,
        "button_label": button_label,
    },
}

await self.send_notification("notifications/claude/channel", notification)
```

**Payload:**
```json
{
  "content": "[button] Confirmar (test_confirm)",
  "meta": {
    "chat_id": "1487521449781756066",
    "message_id": "1488312544627130401",
    "user": ".dobrador",
    "user_id": "165531471266840577",
    "ts": "2026-03-30T23:03:45.123000+00:00",
    "interaction_type": "button_click",
    "custom_id": "test_confirm",
    "button_label": "Confirmar"
  }
}
```

---

## Código de Referência

### 1. on_interaction_create() - Entry Point
```python
# server.py:397-474
@self.discord_client.event
async def on_interaction_create(interaction):
    debug_log.write_text(f"[{datetime.now().isoformat()}] HANDLER CHAMADO! Type: {interaction.type}\n", mode='a')
    """
    Handler DDD para interações Discord (botões, select menus).

    Envia notificação MCP para Claude Code quando usuário clica em botão.
    """
    print(f"[DEBUG on_interaction_create] Interaction type: {interaction.type}")
    try:
        # Apenas interações de componente
        if interaction.type != InteractionType.component:
            print(f"[DEBUG] Não é componente, retornando")
            return

        print(f"[DEBUG] É componente! Fazendo defer...")
        # Fazer defer para evitar timeout (acknowledge não existe em discord.py 2.x)
        try:
            await interaction.response.defer()
        except Exception:
            print(f"[DEBUG] Falha no defer")
            return

        print(f"[DEBUG] Chamando adapter...")
        # Processar via adapter DDD
        result = await button_adapter.handle_interaction(interaction)

        print(f"[DEBUG] Adapter result: {result}")
        if result["status"] == "success":
            logger.info(f"Interação processada: {result['message']}")

        # ========================================
        # CRÍTICO: Enviar notificação MCP para Claude Code
        # ========================================
        # Sem isso, Claude Code nunca sabe que o botão foi clicado
        chat_id = str(interaction.channel_id)

        # Extrair informações do botão clicado
        custom_id = "unknown"
        button_label = "unknown"

        if interaction.data:
            custom_id = interaction.data.get("custom_id", "unknown")

        # Tentar obter label da mensagem original
        try:
            message = interaction.message
            if message and message.components:
                for action_row in message.components:
                    for component in action_row.children:
                        if component.custom_id == custom_id:
                            button_label = component.label or custom_id
                            break
        except Exception:
            button_label = custom_id

        # Enviar notificação MCP
        notification = {
            "content": f"[button] {button_label} ({custom_id})",
            "meta": {
                "chat_id": chat_id,
                "message_id": str(interaction.message.id) if interaction.message else "",
                "user": interaction.user.name,
                "user_id": str(interaction.user.id),
                "ts": interaction.created_at.isoformat(),
                "interaction_type": "button_click",
                "custom_id": custom_id,
                "button_label": button_label,
            },
        }

        await self.send_notification("notifications/claude/channel", notification)
        print(f"[DEBUG] Notificação MCP enviada: {custom_id}")

    except Exception as e:
        print(f"[ERROR] Erro no handler: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Erro no handler de interação DDD: {e}")
```

### 2. MCPButtonAdapter.handle_interaction()
```python
# infrastructure/mcp_button_adapter.py:50-92
async def handle_interaction(self, interaction) -> dict:
    """
    Processa interação Discord.

    Args:
        interaction: Interação Discord (discord.Interaction)

    Returns:
        Dict com status da operação
    """
    print(f"[DEBUG MCPButtonAdapter] Interacao recebida: {interaction.type}")
    try:
        # 1. Converter para Command
        print(f"[DEBUG MCPButtonAdapter] Convertendo para command...")
        command = HandleButtonClickCommand.from_discord_interaction(interaction)
        print(f"[DEBUG MCPButtonAdapter] Command criado: {command.button_custom_id}")

        # 2. Processar via Handler
        print(f"[DEBUG MCPButtonAdapter] Processando via handler...")
        result = await self._handler.handle(command)
        print(f"[DEBUG MCPButtonAdapter] Handler result: {result.is_success}, {result.message}")

        # 3. Enviar notificação MCP para Claude Code
        if result.is_success:
            print(f"[DEBUG MCPButtonAdapter] Enviando notificacao MCP...")
            await self._send_mcp_notification(interaction, command, result)
            print(f"[DEBUG MCPButtonAdapter] Notificacao enviada!")

        return {
            "status": "success" if result.is_success else "error",
            "message": result.message,
            "data": result.data,
        }

    except Exception as e:
        print(f"[ERROR MCPButtonAdapter] Erro no adapter: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "data": None,
        }
```

---

## Arquivos Envolvidos

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `server.py:397` | 77 | `on_interaction_create()` - Entry point + 2ª notificação |
| `mcp_button_adapter.py:50` | 42 | `handle_interaction()` - Processa interação |
| `mcp_button_adapter.py:94` | 25 | `_send_mcp_notification()` - 1ª notificação |
| `button_click_handler.py` | - | `ButtonClickHandler.handle()` - Lógica do botão |
| `event_publisher.py` | - | Publica `ButtonClickedEvent` |

---

## Recomendação

**Remover duplicação:** Escolher UMA notificação para manter:

1. **Manter apenas `notifications/claude/channel`** (padrão com mensagens de texto)
2. **Remover `_send_mcp_notification()` do `MCPButtonAdapter`**

Isso simplifica o código e evita notificações duplicadas.

---

> "Botão sem notificação é como árvore que cai na floresta" – made by Sky 🌲
> "Mas duas notificações é como eco que confunde a floresta" – made by Sky 🦜✨
