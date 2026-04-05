# SPEC014 - Discord UI Views Pattern

## Status
✅ **VALIDADO** - Padrão testado e funcionando em produção

## Problema: "Esta interação falhou"

Ao clicar em botões do Discord, aparecia a mensagem de erro "This interaction failed".

### Causas Identificadas

1. **`on_interaction_create` manual CONFLITA com `discord.ui.View`**
   - `discord.ui.View` tem seu próprio sistema de handlers internos
   - Quando você registra `on_interaction_create` manualmente, ele nunca é chamado
   - A View processa as interações antes do handler manual

2. **View expira em 180 segundos (padrão)**
   - Botões ficam órfãos após o timeout
   - Cliques em botões órfãos geram "Esta interação falhou"

3. **Resposta deve ser em 3 segundos**
   - Discord exige resposta rápida
   - Se o handler demorar, a interação falha

## Solução: discord.ui.View com @discord.ui.button

### Padrão Validado

```python
from discord import ui
import discord

class ConfirmationView(discord.ui.View):
    """View customizada para confirmacao de ordem."""

    def __init__(self):
        super().__init__(timeout=None)  # NUNCA expira

    @discord.ui.button(
        label="Confirmar",
        style=discord.ButtonStyle.success,
        custom_id="ordem_confirm"
    )
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handler do botao Confirmar."""
        await interaction.response.send_message(
            f"[OK] **{interaction.user.name}** confirmou a ordem!"
        )

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.danger,
        custom_id="ordem_cancel"
    )
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handler do botao Cancelar."""
        await interaction.response.send_message(
            f"[X] **{interaction.user.name}** cancelou a ordem!"
        )
```

### Enviando a View

```python
view = ConfirmationView()
await channel.send(embed=embed, view=view)
```

## Boas Práticas

### 1. Sempre usar `timeout=None` para botões persistentes

```python
# ❌ Ruim - expira em 180s
view = discord.ui.View()

# ✅ Bom - nunca expira
view = discord.ui.View(timeout=None)
```

### 2. Usar `interaction.response.send_message()` para responder

```python
# ✅ Certo - resposta imediata
async def button_handler(self, interaction, button):
    await interaction.response.send_message("OK!")

# ❌ Errado - delay pode causar timeout
async def button_handler(self, interaction, button):
    await asyncio.sleep(5)  # Muito lento!
    await interaction.response.send_message("OK!")
```

### 3. Para processamento demorado, use `defer()`

```python
async def button_handler(self, interaction, button):
    # Avisa que vai demorar
    await interaction.response.defer()

    # Processamento demorado
    result = await long_running_task()

    # Resposta final
    await interaction.followup.send(f"Resultado: {result}")
```

### 4. Nunca misturar `on_interaction_create` com `discord.ui.View`

```python
# ❌ ERRADO - NUNCA faça isso
class MyBot(discord.Client):
    async def on_interaction_create(self, interaction):
        # Este handler NUNCA será chamado se usar discord.ui.View
        pass

# ✅ CERTO - Use decorators na View
class MyView(discord.ui.View):
    @discord.ui.button(...)
    async def my_button(self, interaction, button):
        # Este SIM será chamado
        pass
```

## Estilos de Botão

```python
discord.ButtonStyle.success  # Verde (1)
discord.ButtonStyle.danger   # Vermelho (4)
discord.ButtonStyle.primary  # Azul/cinza (2)
discord.ButtonStyle.secondary  # Cinza (2)
discord.ButtonStyle.link     # URL (5) - requer url=, não custom_id
```

## Referências

- [Discord Interactions](https://docs.discord.com/developers/interactions/receiving-and-responding)
- [discord.ui.Button](https://discordpy.readthedocs.io/en/stable/api.html#discord.ui.Button)
- [discord.ui.View](https://discordpy.readthedocs.io/en/stable/api.html#discord.ui.View)

## Exemplo Completo: bot_continuo.py

```python
# src/core/discord/facade/sandbox/bot_continuo.py

class ConfirmationView(discord.ui.View):
    """View customizada para confirmacao de ordem."""

    def __init__(self):
        super().__init__(timeout=None)  # Nunca expira

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.success, custom_id="ordem_confirm")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"[OK] **{interaction.user.name}** confirmou a ordem!"
        )
        logger.info(f"Botao Confirmar clicado por {interaction.user.name}")

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, custom_id="ordem_cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"[X] **{interaction.user.name}** cancelou a ordem!"
        )
        logger.info(f"Botao Cancelar clicado por {interaction.user.name}")
```

## Testado em Produção

- ✅ Canal: Discord Redesign (1487929503073173727)
- ✅ Bot: SkyBridge#2839
- ✅ Data: 2026-03-30
- ✅ Resultado: Botões respondendo perfeitamente

---

> "A persistência vence a resistência" – made by Sky 💪
