# Quick Reactions - Sistema de Votação via Emoji

## Visão Geral

Sistema de reações rápidas para votação, feedback e classificação usando emojis do Discord.

## Tools MCP

### 1. `quick_react`

Adiciona reações emoji a uma mensagem Discord.

**Modos de operação:**

- **Poll (votação completa):** Adiciona todos os emojis de uma categoria
- **Single (emoji único):** Adiciona apenas um emoji específico

**Parâmetros:**
```python
quick_react(
    chat_id: str,        # ID do canal
    message_id: str,     # ID da mensagem
    category: str = "vote",  # Categoria (vote, priority, sentiment, binary, tshirt)
    emoji: str = None     # Emoji específico (opcional)
)
```

### 2. `list_quick_reactions`

Lista as categorias e emojis disponíveis.

```python
list_quick_reactions(category: str = None)
```

## Categorias

### `vote` - Votação Simples

| Emoji | Significado |
|-------|-------------|
| 👍 | Concordo / Positivo |
| 👎 | Discordo / Negativo |
| 🤷 | Neutro / Indeciso |
| 🔥 | Prioridade Alta |
| ✅ | Concluído / Feito |

**Uso:** Decisões de grupo, aprovação rápida

### `priority` - Classificação de Prioridade

| Emoji | Significado |
|-------|-------------|
| 🔴 | Crítico / Urgente |
| 🟠 | Alta Prioridade |
| 🟡 | Média Prioridade |
| 🟢 | Baixa Prioridade |
| ⚪ | Backlog |

**Uso:** Triagem de tarefas, roadmap

### `sentiment` - Sentimento/Emoção

| Emoji | Significado |
|-------|-------------|
| 👍 | Positivo |
| ❤️ | Amei |
| 😂 | Engraçado |
| 🤔 | Interessante |
| 😕 | Confuso |
| 😡 | Frustrado |

**Uso:** Feedback qualitativo, pesquisa

### `binary` - Decisão Binária

| Emoji | Significado |
|-------|-------------|
| ✅ | Sim / Aprovo |
| ❌ | Não / Rejeito |
| ❓ | Dúvida |

**Uso:** Aprovação rápida, go/no-go

### `tshirt` - Tamanho de Camiseta

| Emoji | Significado |
|-------|-------------|
| 👕 | Pequeno (S) |
| 👚 | Médio (M) |
| 👔 | Grande (L) |
| 🧥 | Extra Grande (XL) |

**Uso:** Enquetes de tamanho, preferências

## Exemplos

### Criar uma votação rápida

```python
# Bot envia mensagem
msg = await send_embed(
    chat_id="...",
    title="📊 Votação: Usar FastAPI ou Express?",
    description="Reaja com emoji para votar"
)

# Adiciona emojis de votação
await quick_react(
    chat_id="...",
    message_id=msg.id,
    category="binary"  # ✅❌❓
)
```

### Criar enquete de prioridade

```python
msg = await send_embed(
    chat_id="...",
    title="🔥 Qual feature priorizar?",
    description="Reaja para classificar prioridade"
)

await quick_react(
    chat_id="...",
    message_id=msg.id,
    category="priority"  # 🔴🟠🟡🟢⚪
)
```

### Votar em um emoji específico

```python
# Usuário quer votar 👍
await quick_react(
    chat_id="...",
    message_id="...",
    emoji="👍"  # Apenas esse emoji
)
```

## Extensão

Para adicionar nova categoria:

1. Editar `QUICK_REACTIONS` em `quick_react.py`
2. Adicionar entrada no dicionário:

```python
QUICK_REACTIONS = {
    "minha_categoria": {
        "🚀": "Descrição 1",
        "⭐": "Descrição 2",
    },
    # ...
}
```

3. Adicionar descrição em `_get_category_description()`

---

> "Simples é melhor que complexo" – made by Sky 🚀
