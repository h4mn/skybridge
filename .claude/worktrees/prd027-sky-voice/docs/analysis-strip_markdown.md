# Análise do Código Fonte: strip_markdown

## Instalação

**Local**: `B:\Programas\Python\Python311\Lib\site-packages\strip_markdown\`

**Data da análise**: 2025-03-15

---

## Estrutura de Arquivos

```
strip_markdown/
├── __init__.py           (1 linha)   - Wrapper que exporta tudo
├── __main__.py           (23 linhas) - CLI para conversão de arquivos
└── strip_markdown.py     (51 linhas) - Implementação principal
```

**Total**: 75 linhas de código Python

---

## Arquivo Principal: strip_markdown.py

### Linhas 1-6: Imports

```python
from typing import *
from pathlib import Path
import os

import markdown          # Dependência: python-markdown
from bs4 import BeautifulSoup  # Dependência: beautifulsoup4
```

**Dependências**:
- `markdown` (python-markdown)
- `bs4` (beautifulsoup4)

### Linhas 8-9: Exceção customizada

```python
class MarkdownError(Exception):
    pass
```

### Linhas 11-14: Função Principal

```python
def strip_markdown(md: str) -> str:
    html = markdown.markdown(md)                          # Passo 1: MD → HTML
    soup = BeautifulSoup(html, features='html.parser')   # Passo 2: Parse HTML
    return soup.get_text()                                # Passo 3: Extrai texto
```

**Lógica**:
1. Converte markdown para HTML usando `markdown.markdown()`
2. Parseia HTML com BeautifulSoup
3. Extrai apenas o texto com `get_text()`

### Linhas 16-35: Função para arquivos

```python
def strip_markdown_file(markdown_fn: str, text_fn: Optional[str]=None):
    # Lê arquivo markdown
    # Converte com strip_markdown()
    # Salva como .txt (mesmo nome se não especificado)
```

### Linhas 37-51: Helpers de I/O

```python
def _read_file(filename: str) -> Optional[str]:
    # Lê arquivo com tratamento de erro

def _write_file(filename: str, text: str) -> bool:
    # Escreve arquivo com tratamento de erro
```

---

## Análise por Componentes

### 1. Conversão Markdown → HTML

```python
html = markdown.markdown(md)
```

**O que `markdown.markdown()` faz**:
- Headers (`# Título`) → `<h1>Título</h1>`
- Bold (`**texto**`) → `<strong>texto</strong>`
- Italic (`*texto*`) → `<em>texto</em>`
- Code (`` `código` ``) → `<code>código</code>`
- Code blocks (```...```) → `<pre><code>...</code></pre>`
- Links (`[texto](url)`) → `<a href="url">texto</a>`
- Listas, tabelas, etc.

### 2. Parse HTML com BeautifulSoup

```python
soup = BeautifulSoup(html, features='html.parser')
```

**Cria árvore DOM**:
```
<html>
  <body>
    <h1>Título</h1>
    <p>Texto <strong>negrito</strong></p>
    <pre><code>def x():</code></pre>
  </body>
</html>
```

### 3. Extração de Texto

```python
return soup.get_text()
```

**O que `get_text()` faz**:
- Percorre a árvore DOM
- Extrai apenas o conteúdo textual
- Remove todas as tags HTML
- Adiciona quebras de linha entre elementos de bloco

**Resultado**:
```
Título
Texto negrito
def x():
```

---

## Fluxo Completo

```
ENTRADA:
```python
# Código
def hello():
    print("**Oi**")
```

PASSO 1 (markdown.markdown):
<pre><code># Código
def hello():
    print("**Oi**")
</code></pre>

PASSO 2 (BeautifulSoup):
Árvore DOM com <pre>, <code>, texto

PASSO 3 (get_text):
# Código
def hello():
    print("**Oi**")
```

**Observação**: Blocos de código **NÃO** são removidos, apenas as tags HTML.

---

## Tamanho e Complexidade

| Métrica | Valor |
|---------|-------|
| **Linhas totais** | 75 |
| **Linhas de lógica** | ~30 |
| **Funções** | 4 (strip_markdown, strip_markdown_file, _read, _write) |
| **Classes** | 1 (Exception) |
| **Dependências** | 2 (markdown, bs4) |
| **Complexidade** | BAIXA |

---

## Puntos de Extensão

Se quiséssemos adicionar parametrização, onde modificar:

### Opção 1: Adicionar parâmetros para seletivamente remover elementos

```python
def strip_markdown(md: str, remove_code: bool = False, remove_links: bool = False) -> str:
    html = markdown.markdown(md)
    soup = BeautifulSoup(html, features='html.parser')

    # Remove elementos específicos ANTES de get_text()
    if remove_code:
        for code in soup.find_all('code'):
            code.decompose()  # Remove da árvore

    if remove_links:
        for link in soup.find_all('a'):
            link.decompose()

    return soup.get_text()
```

### Opção 2: Permitir manter elementos específicos

```python
def strip_markdown(md: str, keep: list[str] = None) -> str:
    """Keep é uma lista de tags para manter (ex: ['code', 'pre'])."""
    html = markdown.markdown(md)
    soup = BeautifulSoup(html, features='html.parser')

    if keep:
        # Remove tudo EXCETO as tags especificadas
        for tag in soup.find_all(True):
            if tag.name not in keep:
                tag.replace_with(tag.get_text())

    return soup.get_text()
```

---

## Conclusão

### Pontos Fortes

- ✅ **Extremamente simples** (75 linhas)
- ✅ **Fácil de entender** (3 passos claros)
- ✅ **Sem bugs ocultos** (código minimalista)
- ✅ **Dependências estáveis** (markdown, bs4)

### Pontos Fracos

- ❌ **Não parametrizável** (tudo ou nada)
- ❌ **Sem controle granular** (não pode escolher o que remover)
- ❌ **Blocos de código mantidos** (remove ``` mas mantém conteúdo)

### Para seu Caso (TTS)

**Se usar strip_markdown como está**:
- Remove formatação (bold, italic, headers, etc.) ✅
- Mantém conteúdo de código ⚠️

**Solução híbrida**:
1. Usa strip_markdown para remover formatação
2. Regex simples pós-processamento para remover código

```python
import strip_markdown
import re

def clean_for_tts(markdown: str) -> str:
    # Passo 1: Remove formatação (lib estável)
    text = strip_markdown.strip_markdown(markdown)

    # Passo 2: Remove blocos de código
    # (heurística simples para detectar/remove)
    lines = []
    in_code = False
    for line in text.split('\n'):
        if line.strip() in ['python', 'javascript', 'def ', 'class ']:
            in_code = True
            continue
        if in_code and line.strip().startswith('Espero'):
            in_code = False
            continue
        if not in_code:
            lines.append(line)

    return '\n'.join(lines).strip()
```

---

## Alternativa: Fork Simples

Como strip_markdown tem apenas 75 linhas, é trivial criar um fork com as opções que você precisa:

```python
# strip_markdown_custom.py
from typing import Optional
import markdown
from bs4 import BeautifulSoup

def strip_markdown(
    md: str,
    keep_code: bool = False,
    keep_links: bool = False,
    keep_formatting: bool = False
) -> str:
    """Strip markdown with options."""
    html = markdown.markdown(md)
    soup = BeautifulSoup(html, features='html.parser')

    # Remove elementos conforme parâmetros
    if not keep_code:
        for code in soup.find_all(['code', 'pre']):
            code.decompose()

    if not keep_links:
        for link in soup.find_all('a'):
            link.replace_with(link.get_text())

    if not keep_formatting:
        for tag in soup.find_all(['strong', 'em', 'b', 'i']):
            tag.replace_with(tag.get_text())

    return soup.get_text()
```

**Vantagens**:
- Controle total
- Código simples (baseado em lib existente)
- Sem dependência de versões externas

> "Simplicidade é o máximo de sofisticação" – Sky 🎯
