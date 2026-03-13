# Bootstrap do Sky Chat

Sistema de carregamento progressivo com feedback visual para inicialização do Sky Chat.

## Arquitetura

```
sky.cmd
    ↓
scripts/sky_bootstrap.py
    ↓
core/sky/bootstrap/
    ├── __init__.py
    ├── bootstrap.py         # run() - orquestrador principal
    ├── stage.py             # Stage - configuração de estágio
    └── progress.py          # Progress - barra de progresso
    ↓
[Estágios]
    1. Environment ✓
    2. Embedding Model ████████░░ (5-15s)
    3. Vector DB ✓
    4. Collections ✓
    5. Textual UI ✓
    ↓
core/sky/chat/textual_ui.py (SkyApp)
```

## Componentes

### Stage

Classe de dados que representa um estágio de bootstrap.

```python
@dataclass
class Stage:
    name: str           # Identificador único
    description: str    # Descrição amigável para exibir
    weight: float = 1.0 # Peso relativo para cálculo de progresso
```

**Métodos úteis:**
- `with_size_info(size_mb)` - Adiciona informação de tamanho à descrição
- `with_collections_info(collections)` - Adiciona nomes das coleções à descrição

### Progress

Gerencia barra de progresso com tema Sky.

```python
from core.sky.bootstrap import Progress

progress = Progress()
progress.add_stage(Stage("env", "Configurando ambiente..."))

with progress.run():
    # Executa estágios aqui
    ...
```

**Características:**
- Usa Rich para exibição visual
- Tema Sky (azul/ciano)
- Mostra tempo decorrido por estágio
- Mostra tempo total ao final

### run()

Função orquestradora principal do bootstrap.

```python
from core.sky.bootstrap import run

app = run()  # Mostra progresso, retorna SkyApp
app.run()
```

**Comportamento:**
- Detecta `USE_RAG_MEMORY` para incluir/excluir estágios RAG
- Inicializa componentes em ordem de dependência
- Trata erros com mensagens amigáveis
- Retorna `SkyApp` pronta para executar

## Estágios de Bootstrap

| Estágio | Descrição | Quando Executa |
|---------|-----------|----------------|
| Environment | Configurando ambiente... | Sempre |
| Embedding | Carregando modelo de embedding... | Com RAG |
| Vector DB | Inicializando banco vetorial... (X MB) | Com RAG |
| Collections | Configurando coleções... (identity, shared-moments, teachings, operational) | Com RAG |
| Textual | Iniciando interface... | Sempre |

## Uso

### Modo Normal (com Bootstrap)

```batch
REM sky.cmd
python scripts\sky_bootstrap.py
```

### Modo Bypass (sem Bootstrap)

```batch
REM sky.cmd --no-bootstrap
python scripts\sky_bootstrap.py --no-bootstrap
```

Ou direto:

```batch
python scripts\sky_textual.py
```

## Adicionando Novos Estágios

Para adicionar um novo estágio de bootstrap:

1. Defina o estágio em `_get_stages()`:

```python
def _get_stages(use_rag: bool) -> list[Stage]:
    stages = [
        Stage("environment", "Configurando ambiente...", weight=0.1),
        # ... outros estágios ...
        Stage("meu_estagio", "Minha Nova Coisa...", weight=1.0),  # ← Adicione aqui
    ]
    return stages
```

2. Implemente a função do estágio:

```python
def _stage_meu_estagio(progress: Progress) -> None:
    """Estágio X: Minha Nova Coisa."""
    # Seu código aqui
    pass
```

3. Adicione ao mapeamento em `run()`:

```python
stage_functions = {
    # ...
    "meu_estagio": _stage_meu_estagio,
}
```

## Performance

- **Overhead alvo**: < 200ms
- **Tempo até primeira mensagem visual**: < 1s
- **Estágios lentos (>3s)** são destacados automaticamente

## Tratamento de Erros

| Erro | Comportamento |
|------|---------------|
| Modelo não cacheado | Mensagem com instruções de download, exit 1 |
| SQLite corrompido | Mensagem indicando problema, sugere reinit, exit 1 |
| Ctrl+C | Cancela graciosamente, exit 130 |

## Exit Codes

- `0`: Sucesso, Sky Chat iniciado
- `1`: Erro durante bootstrap
- `130`: Cancelado pelo usuário (Ctrl+C)
