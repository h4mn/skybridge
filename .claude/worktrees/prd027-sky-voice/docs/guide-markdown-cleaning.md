# Limpeza de Markdown para TTS - Opções e Arquitetura

## Problema

Ter dois fluxos:
1. **Markdown original** → Widget (visual bonito)
2. **Markdown limpo** → TTS (sem formatação)

## Bibliotecas Encontradas

### 1. strip_markdown

```python
import strip_markdown

text = strip_markdown.strip_markdown(markdown)
```

**Características**:
- ✅ Simples, estável, mantida por terceiros
- ❌ **NÃO parametrizável** - remove tudo
- ❌ Mantém conteúdo de blocos de código (remove apenas ```)

**Comportamento**:
```
ENTRADA:
```python
def hello():
    print("Oi")
```

SAÍDA:
python
def hello():
    print("Oi")
```

### 2. python-markdown + extensão plain_text

```python
import markdown

md = markdown.Markdown(extensions=['plain_text'])
text = md.convert('# Hello\n**Bold**')
```

**Características**:
- ✅ Biblioteca estável e madura
- ❌ **NÃO parametrizável** - extensão plain_text remove tudo
- ✅ Mais controle se usar parser manual

### 3. Manual (regex) - sua opção atual

```python
def _clean_text_for_speech(self, text: str) -> str:
    import re
    text = re.sub(r'`([^`]+)`', r'\1', text)        # code inline
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)   # bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)       # italic
    return text.strip()
```

**Características**:
- ✅ Controle total sobre o que remover
- ❌ Imprevisível (edge cases)
- ❌ Manutenção manual

---

## Resposta: Nenhuma biblioteca é perfeitamente parametrizável

As bibliotecas encontradas **NÃO** permitem configuração do tipo:
- "Remove bold mas mantém código"
- "Remove tudo exceto listas"

Elas são "tudo ou nada".

---

## Arquitetura Proposta

### Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMING (Claude API)                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │   CHUNK DE MARKDOWN     │
              │  (texto com formatação) │
              └─────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌──────────────────────┐      ┌──────────────────────┐
│   FLUXO 1: VISUAL   │      │   FLUXO 2: TTS      │
└──────────────────────┘      └──────────────────────┘
            │                               │
            ▼                               ▼
   ┌─────────────────┐            ┌──────────────────┐
   │ Markdown Widget │            │  Limpador Markdown│
   │ (mostra bonito) │            │  (remove formata-│
   │                 │            │   ção)            │
   └─────────────────┘            └──────────────────┘
                                          │
                                          ▼
                                 ┌──────────────────┐
                                 │  Opcional:       │
                                 │  Remove Bloco    │
                                 │  de Código?      │
                                 └──────────────────┘
                                          │
                                          ▼
                                 ┌──────────────────┐
                                 │    Kokoro TTS    │
                                 └──────────────────┘
```

### Código Proposto

```python
class ChatScreen(Screen):
    def _clean_text_for_speech(self, text: str) -> str:
        """Remove formatação markdown para TTS.

        Estratégia:
        1. Usa strip_markdown (lib estável)
        2. Remove blocos de código se configurado
        """
        import strip_markdown
        import re

        # Passo 1: Remove formatação markdown
        text = strip_markdown.strip_markdown(text)

        # Passo 2: Remove blocos de código (opcional)
        if self._remove_code_blocks_from_tts:
            # Remove tudo entre "python" e "Espero que ajude"
            # Pode ser mais sofisticado com regex para blocos
            text = re.sub(r'\npython\n.*?Espero que ajude!', '', text, flags=re.DOTALL)

        return text.strip()
```

---

## Opções de Parametrização

### Opção A: strip_markdown + Regex pós-processamento

```python
def clean_for_tts(markdown: str, remove_code: bool = True) -> str:
    """Limpa markdown para TTS com opções."""
    import strip_markdown
    import re

    # Passo 1: Remove formatação principal
    text = strip_markdown.strip_markdown(markdown)

    # Passo 2: Pós-processamento específico
    if remove_code:
        # Remove blocos de código (ex: remove linhas com "python", "def", etc)
        lines = []
        in_code_block = False

        for line in text.split('\n'):
            # Detecta início de bloco de código (heurística)
            if line.strip() in ['python', 'javascript', 'bash', 'def ', 'class ', 'function ']:
                in_code_block = True
                continue

            # Detecta fim do bloco
            if in_code_block and line.strip().startswith('Espero'):
                in_code_block = False
                continue

            # Adiciona linha se não está em bloco de código
            if not in_code_block:
                lines.append(line)

        text = '\n'.join(lines)

    return text.strip()
```

### Opção B: python-markdown com processamento manual

```python
import markdown
from bs4 import BeautifulSoup

def clean_for_tts(markdown: str, keep_code: bool = False) -> str:
    """Limpa markdown com controle granular."""
    # Converte para HTML
    md = markdown.Markdown()
    html = md.convert(markdown)

    # Parse HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Remove elementos específicos
    if not keep_code:
        for code in soup.find_all('code'):
            code.decompose()

    for pre in soup.find_all('pre'):
        pre.decompose()

    # Extrai texto
    return soup.get_text()
```

### Opção C: Parser markdown customizado (markdown-it-py)

```python
import markdown_it

def clean_for_tts(markdown: str, rules: dict) -> str:
    """Limpa markdown com regras customizadas."""
    parser = markdown_it.MarkdownIt()

    # Parse para AST
    tokens = parser.parse(markdown)

    # Filtra tokens baseado em regras
    filtered = []
    for token in tokens:
        if token.type == 'paragraph_open':
            continue
        if token.type == 'code_block' and not rules.get('keep_code', True):
            continue
        filtered.append(token)

    # Renderiza como texto plano
    return render_as_text(filtered)
```

---

## Recomendação

### Para seu caso (TTS progressivo):

**Opção A** é a mais simples:

```python
def _clean_text_for_speech(self, text: str) -> str:
    """Remove formatação markdown para TTS.

    Usa strip_markdown (lib estável) + remove blocos de código.
    """
    import strip_markdown
    import re

    # Remove formatação
    text = strip_markdown.strip_markdown(text)

    # Remove blocos de código (heurística simples)
    # Remove linhas que parecem código
    lines = []
    skip = False

    for line in text.split('\n'):
        stripped = line.strip()

        # Detecta início de código (palavras-chave)
        if stripped in ['python', 'javascript', 'bash', 'java', 'def ', 'class ', 'function ', 'const ', 'let ', 'var ']:
            skip = True
            continue

        # Detecta fim (transições para texto normal)
        if skip and stripped and not any(c in stripped for c in '=(){}[],;'):
            skip = False

        if not skip and stripped:
            lines.append(line)

    return '\n'.join(lines).strip()
```

### Vantagens:

- ✅ Usa lib estável (strip_markdown)
- ✅ Controle sobre blocos de código
- ✅ Simples de manter
- ✅ Não precisa manter regex complexos

### Desvantagens:

- ⚠️ Heurística de detecção de código pode falhar
- ⚠️ Pode precisar ajustes ao longo do tempo

---

## Decisão: Qual Opção?

| Opção | Complexidade | Manutenção | Flexibilidade |
|-------|-------------|------------|---------------|
| A: strip_markdown + regex | Baixa | Média | Média |
| B: python-markdown + BS4 | Média | Baixa | Alta |
| C: Parser customizado | Alta | Alta | Muito Alta |
| D: Regex manual (atual) | Média | Alta | Média |

**Para você**: Recomendo **Opção A** - equilíbrio entre simplicidade e controle.

> "Estabilidade + simplicidade = manutenção fácil" – Sky 🎯
