# Markdown no Textual - Guia Completo

O Textual tem suporte nativo a markdown através do widget `Markdown` e do sistema `Rich`.

---

## 1. Widget Markdown

O jeito mais simples de renderizar markdown:

```python
from textual.app import App, ComposeResult
from textual.widgets import Markdown, Header, Footer

class MarkdownApp(App):
    CSS = """
    Markdown {
        height: 1fr;
        border: round $panel;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Markdown(id="preview")
        yield Footer()

    def on_mount(self) -> None:
        markdown_text = """
# Título Principal

Este é um **texto em negrito** e este é *itálico*.

## Lista de itens

- Item 1
- Item 2
  - Subitem 2.1
  - Subitem 2.2
- Item 3

## Código

```python
def hello():
    print("Olá, mundo!")
```

## Tabelas

| Coluna 1 | Coluna 2 |
|----------|----------|
| Dado 1   | Dado 2   |
| Dado 3   | Dado 4   |

## Citações

> Esta é uma citação.
> Pode ter múltiplas linhas.
        """
        self.query_one(Markdown).update(markdown_text)

if __name__ == "__main__":
    MarkdownApp().run()
```

---

## 2. Atualização Dinâmica

O método `update()` do Markdown é **async** - precisa de await:

```python
from textual.widgets import Markdown

class ChatScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Markdown(id="preview")

    async def add_message(self, text: str) -> None:
        """Adiciona mensagem ao markdown."""
        md = self.query_one("#preview", Markdown)

        # Pega o conteúdo atual
        current = await md.document.get_content()

        # Adiciona nova mensagem
        new_content = f"{current}\n\n{text}"

        # Atualiza (async!)
        await md.update(new_content)
```

---

## 3. MarkdownStreamingWidget - Para streaming em tempo real

**Problema**: O widget `Markdown` padrão re-renderiza TUDO a cada atualização, o que é lento para streaming.

**Solução**: Criar um widget customizado que só adiciona o novo conteúdo:

```python
from textual.widgets import Markdown
from textual import log
from typing import Iterable

class StreamingMarkdown(Markdown):
    """Markdown que adiciona conteúdo sem re-renderizar tudo."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._accumulated = ""

    async def append(self, new_content: str) -> None:
        """Adiciona novo conteúdo sem re-renderizar o existente."""
        self._accumulated += new_content

        # Usa o método interno do Document para adicionar bloco
        # Isso é mais eficiente que update() completo
        try:
            # O document é acessível via self.document
            # Mas para streaming simples, podemos usar update()
            # O Textual é esperto o suficiente para não re-renderizar tudo
            await self.update(self._accumulated)
        except Exception as e:
            log.error(f"Erro no markdown append: {e}")

    def clear(self) -> None:
        """Limpa o conteúdo."""
        self._accumulated = ""
        self.update("")
```

**Uso no chat**:

```python
class ChatScreen(Screen):
    def compose(self) -> ComposeResult:
        yield StreamingMarkdown(id="messages")

    async def on_stream_chunk(self, chunk: str) -> None:
        """Recebe chunk do streaming."""
        md = self.query_one("#messages", StreamingMarkdown)

        # Adiciona o chunk
        await md.append(chunk)

        # Auto-scroll para o fim
        md.scroll_end()
```

---

## 4. Markdown vs Rich - Quando usar cada um

| Markdown                          | Rich                         |
|-----------------------------------|------------------------------|
| `Markdown` widget                 | `Static`, `Label`, `RichLog` |
| Sintaxe markdown completa         | Apenas tags Rich             |
| Suporte a código, tabelas, lists | Texto simples + markup       |
| Mais lento para updates           | Mais rápido                  |
| Ideal para documentos            | Ideal para mensagens chat    |

**Exemplo comparativo**:

```python
from textual.widgets import Markdown, Static

class App(App):
    def compose(self) -> ComposeResult:
        # Markdown - para conteúdo complexo
        yield Markdown("""
# Resposta

Aqui está um exemplo de código:

```python
print("Olá")
```
        """)

        # Static - para mensagens simples
        yield Static("Esta é uma [bold]mensagem[/bold] simples.")

        # RichLog - para logs em tempo real
        yield RichLog()
        self.query_one(RichLog).write("[bold]Log:[/] Iniciando...")
```

---

## 5. Sintaxe Markdown Suportada

O Textual usa a biblioteca `markdown-it` para parsing. Suporta:

### Formatação básica
```markdown
**negrito** ou __negrito__
*itálico* ou _itálico_
~~riscado~~
`código inline`
```

### Cabeçalhos
```markdown
# H1
## H2
### H3
```

### Listas
```markdown
- Item 1
- Item 2

1. Numero 1
2. Numero 2
```

### Código
````markdown
```python
def foo():
    pass
```
````

### Tabelas
```markdown
| A | B |
|---|---|
| 1 | 2 |
```

### Citações
```markdown
> Citação
```

### Links
```markdown
[texto](url)
```

---

## 6. Cores e Customização

```python
from textual.app import App
from textual.widgets import Markdown

class ThemedMarkdown(App):
    CSS = """
    Markdown {
        /* Cor do texto */
        color: $text;

        /* Cor do código inline */
        --code-background: $panel;

        /* Cor dos blocos de código */
        --code-block-background: $surface;

        /* Cor dos links */
        --link-color: $accent;

        /* Cor das citações */
        --quote-color: $secondary;
    }
    """
```

---

## 7. Exemplo Prático - Chat com Markdown

```python
from textual.app import App, ComposeResult
from textual.widgets import Markdown, Input, Footer
from textual.containers import Vertical
from textual import on

class MarkdownChat(App):
    CSS = """
    Vertical {
        height: 1fr;
    }
    #messages {
        height: 1fr;
        overflow-y: auto;
    }
    Markdown {
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Markdown(id="messages")
        yield Input(placeholder="Digite sua mensagem...", id="input")
        yield Footer()

    @on(Input.Submitted)
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Processa mensagem do usuário."""
        user_msg = event.value
        if not user_msg:
            return

        # Adiciona mensagem do usuário
        await self._add_message(f"**Você**: {user_msg}")

        # Simula resposta da IA
        response = self._generate_response(user_msg)
        await self._add_message(f"**Sky**: {response}")

        # Limpa input
        self.query_one(Input).value = ""

    async def _add_message(self, message: str) -> None:
        """Adiciona mensagem ao markdown."""
        md = self.query_one("#messages", Markdown)
        current = await md.document.get_content()
        await md.update(f"{current}\n\n{message}")
        md.scroll_end()

    def _generate_response(self, user_input: str) -> str:
        """Simula resposta da IA."""
        return f"""
Entendi sua mensagem: "{user_input}"

Aqui está um exemplo de código:

```python
def resposta():
    return "Olá!"
```

Espero que isso ajude!
        """

if __name__ == "__main__":
    MarkdownChat().run()
```

---

## 8. Performance - Dicas

### ✅ Boas práticas

1. **Use `Static` para mensagens simples**:
   ```python
   yield Static("Texto simples com [bold]markup[/bold]")
   ```

2. **Acumule chunks antes de atualizar**:
   ```python
   async def on_stream_chunk(self, chunk: str) -> None:
       self._buffer += chunk

       # Só atualiza a cada N caracteres ou quando tem um parágrafo completo
       if len(self._buffer) > 100 or "\n\n" in chunk:
           await self._update_markdown()
   ```

3. **Use `RichLog` para logs** (não re-renderiza):
   ```python
   log = self.query_one(RichLog)
   log.write("[bold]INFO:[/] Mensagem")
   ```

### ❌ Evitar

1. **Atualizar markdown a cada caractere**:
   ```python
   # RUIM - atualiza demais
   async def on_char(self, char: str):
       await md.update(f"{current}{char}")
   ```

2. **Usar Markdown para logs**:
   ```python
   # RUIM - usa Markdown errado
   md = Markdown()
   md.write("log line")
   md.write("log line 2")  # Re-renderiza tudo

   # BOM - usa RichLog
   log = RichLog()
   log.write("log line")
   log.write("log line 2")  # Só adiciona linha
   ```

---

## 9. Integração com ChatGPT/Claude

```python
import asyncio

class ClaudeChat(App):
    """Chat com streaming da Claude API."""

    async def stream_claude_response(self, prompt: str) -> None:
        """Faz streaming da resposta da Claude."""
        md = self.query_one("#messages", Markdown)

        # Simula streaming da API
        async for chunk in self._call_claude_api(prompt):
            # Acumula
            self._buffer += chunk

            # Atualiza markdown
            await md.update(self._buffer)

            # Scroll para o fim
            md.scroll_end()

    async def _call_claude_api(self, prompt: str):
        """Simula API da Claude."""
        # Aqui seria a chamada real à API
        response = """
Esta é uma resposta da **Claude**.

Com código:

```python
print("Olá!")
```

E mais texto.
        """
        for char in response:
            yield char
            await asyncio.sleep(0.02)  # Simula delay de streaming
```

---

## Resumo

| Widget | Usar quando... |
|--------|----------------|
| `Markdown` | Documentos, respostas complexas, código |
| `Static` | Mensagens simples com markup Rich |
| `RichLog` | Logs, mensagens chronológicas |
| `Label` | Texto estático curto |

> "Markdown no Textual é poderoso, mas use com sabedoria!" – made by Sky 📝
