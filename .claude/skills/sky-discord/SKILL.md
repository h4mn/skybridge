---
name: sky-discord
description: Guia completo para interação via Discord MCP - comportamento social, componentes interativos, e melhores práticas de código e comunicação. Use ao interagir em canais Discord, criar bots com UI, ou enviar mensagens via MCP.
---

# Sky Discord - Guia Completo

Guia unificado para interação eficaz via Discord MCP, combinando comportamento social com implementação técnica de componentes interativos.

---

## 📋 Índice Rápido

1. **Comportamento Social** - Tom, formatação, threads
2. **Formatação Markdown** - Regras críticas, tabelas em embeds
3. **Tools MCP** - Quando usar reply, react, embed, etc.
4. **Componentes Interativos** - Botões, menus, views
5. **Padrões de Código** - DDD, handlers, decorators
6. **Casos de Uso** - Exemplos práticos completos

---

## 1. Comportamento Social

### 1.1 Tom e Voz

**Como soar:**
- Amigável mas profissional
- Conciso (Discord é chat, não email)
- Usar emojis com moderação (1-2 por mensagem)
- Evitar jargão técnico excessivo

**Como NÃO soar:**
- Robótico ou excessivamente formal
- Prolixo (parágrafos enormes)
- Emoji spam

### 1.2 Thread Hygiene

**Regra:** Detectar mudança de assunto e sugerir nova thread.

**Quando aplicar:**
- Conversa diverge do título/original da thread
- Mais de 3 mensagens sobre assunto diferente
- Usuário menciona "outro assunto" ou similar

**Ação:**
```
1. Perceber a divergência
2. Sugerir: "Percebi que mudamos de X para Y. Quer que eu crie uma thread separada?"
3. Se confirmar: criar thread, migrar resumo, avisar na thread original
```

**Anti-pattern:** Deixar thread de "Arquitetura" virar "Discord MCP improvements".

### 1.3 Anti-Patterns de Comunicação

| Evitar | Por que |
|--------|---------|
| Thread hijacking | Desorganiza discussão |
| Mensagens gigantes | Dificulta leitura no mobile |
| Ignorar reações | Perde feedback do usuário |
| Responder no canal errado | Confunde contexto |
| Formatação quebrada | Prejudica legibilidade |

---

## 2. Formatação Markdown (CRÍTICO)

### 2.1 Regra de Ouro: Tabelas em Embeds

⚠️ **O Discord NÃO renderiza tabelas markdown em mensagens comuns!**

**ERRADO:**
```python
# Isso não funciona no Discord
content = """
| Ativo | Preço |
|-------|-------|
| BTC | 45000 |
"""
await reply(chat_id, text=content)  # Tabela quebrada
```

**CORRETO:**
```python
# Use send_embed para tabelas
await send_embed(
    chat_id=chat_id,
    title="📊 Preços",
    fields=[
        {"name": "BTC", "value": "$45,000", "inline": True},
        {"name": "ETH", "value": "$3,200", "inline": True},
    ]
)
```

**Quando usar cada formato:**

| Formato | Usar para | Tool MCP |
|---------|-----------|-----------|
| `reply(text=...)` | Texto simples, listas, code blocks | Mensagens normais |
| `send_embed(fields=...)` | **Tabelas**, dados estruturados | Tabelas sempre |
| `edit_message` | Correções rápidas | Atualizações |

### 2.2 Regras Gerais de Markdown

**Sempre fazer:**
- Fechar code blocks com ```
- Títulos fora de code blocks
- Listas com `-` ou `1.` consistente
- **Tabelas → SEMPRE em embed**

**Checklist antes de enviar:**
- [ ] Todos os ``` estão fechados?
- [ ] Títulos estão fora de code blocks?
- [ ] **Tabelas estão em embed?**
- [ ] Formatação está alinhada?

### 2.3 Padrão Artigo - Tabelas Separadas

**Quando:** Textos longos com múltiplas tabelas (artigos, relatórios, documentação).

**Regra:** Separar texto das tabelas, como em artigos acadêmicos.

**Estrutura:**

**Mensagem 1 - Texto principal:**
```
## Análise de Preços

O mercado apresentou comportamento diversificado nesta semana.
BTC liderou as altas com 15% (ver 📊 Tabela 1).

ETH acompanhou o movimento, porém com menor volatilidade.

Para detalhes completos, consulte as tabelas abaixo.
```

**Mensagem 2 - Tabela 1 (embed):**
```python
await send_embed(
    chat_id=chat_id,
    title="📊 Tabela 1: Criptoativos - Semanal",
    fields=[...]
)
```

**Mensagem 3 - Tabela 2 (embed):**
```python
await send_embed(
    chat_id=chat_id,
    title="📊 Tabela 2: Variação Percentual",
    fields=[...]
)
```

**Vantagens:**
- Texto fica limpo e legível
- Cada tabela pode ser consumida independentemente
- Mobile-friendly (embeds são compactos)
- Fácil referenciar ("ver Tabela 1", "conforme Tabela 2")

**Dica de formatação - Tabelas em Embed:**

Para criar tabelas visuais no Discord usando fields:

```python
# Padrão: 3 colunas contínuas
fields=[
    # Cabeçalho
    {"name": "📋", "value": "", "inline": True},
    {"name": "**Tag**", "value": "", "inline": True},
    {"name": "**ID**", "value": "", "inline": True},
    
    # Linhas de dados (name vazio = usa valor como coluna)
    {"name": "", "value": "🐛", "inline": True},
    {"name": "", "value": "Bugs", "inline": True},
    {"name": "", "value": "`ID`", "inline": True},
]
```

**Resultado visual:**
```
📋  |  **Tag**  |  **ID**
🐛  |  Bugs     |  `ID`
📊  |  Relatórios |  `ID`
```

**Dica:** Use `name` vazio e `value` com conteúdo para criar colunas sem rótulo de field!

**Referências no texto:**
- `📊 Tabela 1` ou `(ver Tabela 1 abaixo)`
- `Conforme mostrado na 📊 Tabela 2`
- `Ver resumo na 📊 Tabela 3`

---

## 3. Tools MCP

### 3.1 Mensagens

**`reply`** - Resposta principal
- Responder no mesmo canal/thread da mensagem recebida
- Usar `reply_to` apenas quando responder a mensagem específica (não a mais recente)
- Aceita `files: ["/abs/path.png"]` para anexos (máx 10, 25MB cada)

**`edit_message`** - Atualizações intermediárias
- Usar para correções rápidas de formatação
- NÃO usar para mudar completamente o conteúdo
- **Vantagem:** não dispara notificação push

**`fetch_messages`** - Histórico
- Usar para contexto/histórico
- API de busca do Discord não está disponível para bots
- **Sempre pedir permissão** antes de buscar muito histórico

### 3.2 Interação Visual

**`react`** - Feedback rápido
- Usar para reconhecimento visual (✅, 👍, 🔥)
- **NÃO usar react como resposta principal**

**`send_embed`** - Mensagens estruturadas
- **OBRIGATÓRIO para tabelas**
- Usar para mensagens com campos, cores, footers
- Ideal para relatórios, resumos, dados estruturados

### 3.3 Componentes Interativos

**`send_buttons`** - Ações com botões
- Botões com `id`, `label`, `style` (primary/success/danger/secondary)
- Útil para confirmações, escolhas binárias, workflows guiados
- **Obs:** Botões persistem (timeout=None), desabilitar após interação se necessário

**`send_menu`** - Dropdown de seleção
- Usuário seleciona uma opção entre várias
- Menu persiste (timeout=None)
- Ideal para escolher entre múltiplas opções

**`send_progress`** - Barras de progresso
- Mostrar progresso visual com porcentagem e status
- Usar `tracking_id` para atualizar a mesma mensagem
- Criar na primeira chamada, updates subsequentes usam mesmo ID

**`update_component`** - Atualizar componentes
- Atualizar progress bars, desabilitar botões após interação
- Para progress updates com tracking_id, preferir `send_progress`

### 3.4 Threads

**`create_thread`** - Nova thread
- Criar quando assunto merece discussão separada
- Nomear claramente com **emoji + título**
- `auto_archive_duration`: 60=1h, 1440=24h, 4320=3d, 10080=7d

**`list_threads`** - Listar threads
- Listar threads ativas no canal
- Usar `include_archived: true` para ver também as arquivadas

**`rename_thread`** - Renomear thread
- Usar para organizar ou atualizar propósito da thread

**`archive_thread`** - Arquivar thread
- Threads arquivadas ficam ocultas mas podem ser desarquivadas

### 3.5 Anexos

**`download_attachment`** - Baixar arquivos
- Baixar apenas quando necessário
- Confirmar recebimento ao usuário

---

## 4. Componentes Interativos (discord.py)

### 4.1 Nomes de Event Handlers (CRÍTICO)

| Tipo de Bot | Nome do Handler | Nota |
|-------------|-----------------|------|
| `Client` | `on_interaction` | **NÃO** é `on_interaction_create` |
| `commands.Bot` | `on_interaction_create` | Subclasse Bot |

**⚠️ Erro comum:** Usar `on_interaction_create` com `Client` = handler nunca dispara.

### 4.2 Caso 1: Botões Simples (Hello World)

**Quando:** Protótipos rápidos, ações simples, bots de arquivo único.

```python
import asyncio
from discord import Client, Intents, InteractionType
from discord.ui import View, button, Button
from discord import ButtonStyle
from pathlib import Path
from dotenv import dotenv_values

class DebugView(View):
    """View com handler auto-roteado."""

    @button(label="Debug", style=ButtonStyle.primary, custom_id="debug_btn")
    async def debug_button(self, interaction, button):
        # Decorator roteia automaticamente - sem matching manual de custom_id
        await interaction.response.send_message("✅ Debug!", ephemeral=True)


class MiniBot(Client):
    def __init__(self):
        super().__init__(intents=Intents.default())

    async def on_ready(self):
        channel = self.get_channel(1487929503073173727)
        await channel.send("Debug Bot", view=DebugView())

    async def on_interaction(self, interaction):
        # Opcional: loga todas as interações
        if interaction.type == InteractionType.component:
            print(f"Interaction: {interaction.data.get('custom_id')}")


async def main():
    config = dotenv_values(Path.home() / ".claude/channels/discord" / ".env")
    token = config["DISCORD_BOT_TOKEN"]
    await MiniBot().start(token)


if __name__ == "__main__":
    asyncio.run(main())
```

**Pontos chave:**
- Decorator `@button` = roteamento automático por `custom_id`
- `on_interaction` (NÃO `on_interaction_create`) para `Client`
- `ephemeral=True` = só usuário vê resposta

### 4.3 Caso 2: Domain-Driven Design (Paper Trading)

**Quando:** Lógica de negócio, arquitetura orientada a eventos, múltiplos handlers, camadas DDD.

```python
# Camada Infrastructure - Adapter
class MCPButtonAdapter:
    """Converte interações Discord em Commands DDD."""

    def __init__(self, event_publisher):
        self._event_publisher = event_publisher
        self._handler = ButtonClickHandler(event_publisher)

    async def handle_interaction(self, interaction) -> dict:
        # 1. Converte para Command
        command = HandleButtonClickCommand.from_discord_interaction(interaction)

        # 2. Processa via Handler
        result = await self._handler.handle(command)

        # 3. Publica Domain Event
        await self._event_publisher.publish(command.to_event())

        return {"status": "success" if result.is_success else "error"}


# Camada Application - Handler
class ButtonClickHandler(BaseHandler):
    async def handle(self, command: HandleButtonClickCommand) -> HandlerResult:
        if not command.button_custom_id:
            return HandlerResult.error("button_custom_id obrigatório")

        # Lógica de negócio aqui
        event = command.to_event()
        await self._event_publisher.publish(event)

        return HandlerResult.success(data={"button_id": command.button_custom_id})


# Camada Presentation - Bot
class PaperTradingBot(Client):
    def __init__(self, event_publisher):
        super().__init__(intents=Intents.default())
        self.button_adapter = MCPButtonAdapter(event_publisher)

    async def on_interaction(self, interaction):
        if interaction.type != InteractionType.component:
            return

        result = await self.button_adapter.handle_interaction(interaction)

        if result["status"] == "success":
            await interaction.response.send_message("✅ Ordem processada", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {result['message']}", ephemeral=True)
```

**Fluxo:** `Interaction` → `Command` → `Handler` → `Domain Event` → `Response`

### 4.4 Caso 3: UI Complexa (Select Menus + Estado)

**Quando:** Fluxos multi-step, opções dinâmicas, interações com estado.

```python
import discord
from discord.ui import View, Select, Button, button

class TradingView(View):
    """UI de trading multi-step com estado."""

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.selected_asset = None

    @discord.ui.select(
        placeholder="Escolha o ativo...",
        options=[
            discord.SelectOption(label="BTC", value="btc"),
            discord.SelectOption(label="ETH", value="eth"),
        ]
    )
    async def asset_select(self, interaction, select):
        self.selected_asset = select.values[0]
        await interaction.response.send_message(f"Selecionado: {self.selected_asset}", ephemeral=True)

    @button(label="Comprar", style=ButtonStyle.success, row=1)
    async def buy_button(self, interaction, button):
        if not self.selected_asset:
            await interaction.response.send_message("❌ Selecione um ativo primeiro", ephemeral=True)
            return

        # Executa ordem de compra
        await self.bot.execute_order("BUY", self.selected_asset)
        await interaction.response.send_message(f"✅ Comprou {self.selected_asset}", ephemeral=True)

    @button(label="Vender", style=ButtonStyle.danger, row=1)
    async def sell_button(self, interaction, button):
        if not self.selected_asset:
            await interaction.response.send_message("❌ Selecione um ativo primeiro", ephemeral=True)
            return

        await self.bot.execute_order("SELL", self.selected_asset)
        await interaction.response.send_message(f"✅ Vendeu {self.selected_asset}", ephemeral=True)


class TradingBot(discord.Client):
    async def execute_order(self, side, asset):
        # Lógica de negócio para execução de ordem
        print(f"Executando {side} {asset}")

    async def on_ready(self):
        channel = self.get_channel(CHANNEL_ID)
        await channel.send("📊 Painel de Trading", view=TradingView(self))
```

**Padrões chave:**
- View mantém estado (`self.selected_asset`)
- Múltiplos componentes compartilham estado
- Validação antes da ação
- Parâmetro `row` para layout

---

## 5. Padrões de Resposta

| Padrão | Código | Quando |
|---------|--------|--------|
| **Imediata** | `interaction.response.send_message()` | Operação rápida (<2s) |
| **Defer + Edit** | `defer() → edit_original_message()` | Operação lenta (>2s) |
| **Modal** | `interaction.response.send_modal()` | Input de formulário |
| **Efêmera** | `ephemeral=True` | Resposta privada |

### Padrão Defer (Operações Lentas)

```python
async def slow_button(self, interaction, button):
    # Confirma imediatamente
    await interaction.response.defer()

    # Faz trabalho lento
    resultado = await consulta_lenta_bd()

    # Edita a mensagem "pensando..."
    await interaction.followup.send(f"Resultado: {resultado}")
```

---

## 6. Modals (Formulários)

```python
from discord.ui import Modal, TextInput

class OrderModal(Modal, title='Nova Ordem'):
    asset = TextInput(label='Ativo (BTC/ETH)', placeholder='BTC')
    quantidade = TextInput(label='Quantidade', placeholder='0.001')

    async def on_submit(self, interaction):
        await interaction.response.send_message(
            f"Ordem: {self.quantidade.value} {self.asset.value}",
            ephemeral=True
        )

class TradingView(View):
    @button(label="Nova Ordem")
    async def new_order(self, interaction, button):
        await interaction.response.send_modal(OrderModal())
```

---

## 7. Erros Comuns

| Erro | Sintoma | Correção |
|------|---------|----------|
| `on_interaction_create` com `Client` | Handler nunca dispara | Use `on_interaction` |
| Esquecer `await` antes da response | "Esta interação falhou" | Sempre `await interaction.response...` |
| Sem resposta enviada | "Esta interação falhou" | Sempre chame `response.send_message()` ou `defer()` |
| Usar strings `custom_id` manualmente | Frágil, propenso a erros | Use decorator `@button` |
| Misturar efêmero/público | UX confusa | Seja consistente, documente comportamento |
| **Tabelas em texto comum** | Tabela quebrada no Discord | Use `send_embed` com fields |

---

## 8. Tipos de Componentes

| Tipo | Usar Quando | Import |
|------|-------------|--------|
| `Button` | Ações simples | `from discord.ui import button, Button` |
| `Select` | Escolha única/múltipla | `from discord.ui import Select` |
| `Modal` | Input de formulário | `from discord.ui import Modal, TextInput` |
| `View` | Container para componentes | `from discord.ui import View` |

---

## 9. Checklist de Resposta

Antes de enviar mensagem em canal Discord:

- [ ] Tom apropriado?
- [ ] Formatação correta?
- [ ] **Tabelas em embed?**
- [ ] Assunto relevante para a thread?
- [ ] Tamanho razoável (não gigante)?
- [ ] Code blocks fechados?

---

## 10. Exemplos Práticos Completos

### Thread Hygiene em ação

```
.dobrador: "Sky, e sobre as features do MCP..."

Sky: "Percebi que mudamos de 'Arquitetura' para 'Discord MCP'.
Quer que eu crie uma thread '🔧 Discord MCP Improvements'
para continuarmos lá? Assim mantemos o histórico organizado."
```

### Formatação correta (com tabela em embed)

```python
# ERRADO - tabela em texto
content = """
### Preços

| Ativo | Preço |
|-------|-------|
| BTC | $45,000 |
| ETH | $3,200 |
"""
await reply(chat_id, text=content)

# CORRETO - tabela em embed
await send_embed(
    chat_id=chat_id,
    title="📊 Preços",
    description="Atualizado agora",
    fields=[
        {"name": "BTC", "value": "$45,000", "inline": True},
        {"name": "ETH", "value": "$3,200", "inline": True},
    ]
)
```

---

## 11. Referência: Eventos discord.py

| Handler | Dispara Quando |
|---------|----------------|
| `on_ready()` | Bot conectado |
| `on_interaction()` | Qualquer interação (Client) |
| `on_interaction_create()` | Qualquer interação (Bot) |
| `on_raw_reaction_add()` | Reação emoji adicionada |
| `on_raw_interaction_delete()` | Mensagem com componentes deletada |

---

> "Boa comunicação Discord combina ética social com código sólido" – made by Sky 🚀
