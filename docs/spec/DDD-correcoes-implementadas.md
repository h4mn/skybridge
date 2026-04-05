# Correções DDD Implementadas (2026-03-30)

## Resumo

Implementadas 3 correções críticas para alinhar o código do Discord MCP com a arquitetura DDD definida na SPEC010.

## Correção 1: Fixar `HandleButtonClickCommand.from_discord_interaction`

**Problema:** O método tentava acessar `interaction.data.custom_id` como atributo, mas `interaction.data` é um dicionário.

**Arquivo:** `src/core/discord/application/commands/handle_button_click.py`

**Mudança:**
```python
# ANTES (errado):
custom_id = getattr(interaction.data, 'custom_id', None)

# DEPOIS (correto):
data = interaction.data if hasattr(interaction, 'data') else {}
custom_id = data.get('custom_id') if isinstance(data, dict) else None
```

---

## Correção 2: Atualizar `server.py` para usar `presentation/tools`

**Problema:** `server.py` importava de `.tools.send_buttons` (estrutura antiga) em vez de `.presentation.tools.send_buttons` (estrutura DDD).

**Arquivo:** `src/core/discord/server.py`

**Mudanças:**

1. **Import atualizado:**
```python
# REMOVIDO:
from .tools.send_buttons import handle_send_buttons, TOOL_DEFINITION as SEND_BUTTONS_DEF, set_mcp_server

# ADICIONADO:
from .application.services.discord_service import DiscordService, get_discord_service
from .presentation.tools.send_buttons import handle_send_buttons, TOOL_DEFINITION as SEND_BUTTONS_DEF
```

2. **DiscordMCPServer com DiscordService:**
```python
class DiscordMCPServer:
    def __init__(self):
        # ...
        self._discord_service = get_discord_service(self.discord_client)
```

3. **call_tool adaptado:**
```python
ddd_handlers = {"send_buttons"}  # Handlers que usam DiscordService

if name in ddd_handlers:
    result = await handler(self._discord_service, arguments)
else:
    result = await handler(self.discord_client, arguments)
```

4. **Removido set_mcp_server:** Não é mais necessário pois o fluxo DDD usa `MCPButtonAdapter` que já tem acesso ao server.

---

## Correção 3: Refatorar `DiscordService.create_view()`

**Problema:** Botões discord.py SEMPRE precisam de callback. Sem callback, a interação falha com "Esta interação falhou".

**Arquivo:** `src/core/discord/application/services/discord_service.py`

**Mudança:**
```python
# ADICIONADO: View customizada com callback genérico
class DDDView(discord.ui.View):
    async def _handle_button_click(self, interaction: discord.Interaction):
        """Callback genérico para todos os botões.

        Apenas faz defer para evitar timeout.
        O processamento real é feito pelo on_interaction_create global.
        """
        await interaction.response.defer()

# CADA BOTÃO recebe o callback:
button = discord.ui.Button(...)
button.callback = view._handle_button_click
view.add_item(button)
```

---

## Arquitetura Resultante

```
MCP Tool Call (send_buttons)
    ↓
presentation/tools/send_buttons.py (handler DDD)
    ↓
application/services/discord_service.send_buttons()
    ↓
Cria View com botões (cada botão tem callback genérico)
    ↓
Envia para Discord
    ↓
Usuário clica no botão
    ↓
discord.py invoca callback local (DDDView._handle_button_click)
    ↓
Callback faz defer() para evitar timeout
    ↓
PARALELAMENTE: on_interaction_create global é chamado
    ↓
infrastructure/mcp_button_adapter.py (MCPButtonAdapter)
    ↓
application/commands/handle_button_click.py (Command)
    ↓
application/handlers/button_click_handler.py (Handler)
    ↓
domain/events/button_clicked.py (Domain Event)
    ↓
MCPButtonAdapter envia notificação para Claude Code
```

---

## Status das Camadas DDD

| Camada | Componente | Status |
|--------|-----------|--------|
| **Domain** | `button_clicked.py` (Event) | ✅ OK |
| **Domain** | `handle_button_click.py` (Command) | ✅ Corrigido |
| **Application** | `button_click_handler.py` (Handler) | ✅ OK |
| **Infrastructure** | `mcp_button_adapter.py` (Adapter) | ✅ OK |
| **Presentation** | `send_buttons.py` (Tool) | ✅ OK |
| **Application** | `discord_service.py` (Service) | ✅ Refatorado |
| **Server** | `server.py` (Main) | ✅ Atualizado |

---

## Próximos Passos

1. **Testar integração:** Enviar botões e clicar para verificar notificações MCP
2. **Migrar outros tools:** Atualizar `reply`, `fetch_messages`, etc. para usar `presentation/tools`
3. **Remover estrutura antiga:** Deletar `src/core/discord/tools/` quando migração completa
4. **Adicionar testes:** Testes unitários para `HandleButtonClickCommand.from_discord_interaction`

---

> "Fronteira explícita hoje é liberdade de refatorar amanhã." – made by Sky ✨
