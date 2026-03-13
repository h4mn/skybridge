# Bootstrap do Sky Chat

Sistema de carregamento progressivo com feedback visual.

## Estrutura

```
bootstrap/
├── __init__.py       # Imports públicos: run, Stage, Progress
├── bootstrap.py      # run() - orquestrador principal
├── stage.py          # Stage - configuração de estágio
└── progress.py       # Progress - barra de progresso
```

## Uso Básico

```python
from core.sky.bootstrap import run

app = run()  # Mostra barra de progresso
app.run()
```

## Adicionando Novos Estágios

### 1. Definir o estágio

Em `bootstrap.py`, adicione à função `_get_stages()`:

```python
def _get_stages(use_rag: bool) -> list[Stage]:
    stages = [
        Stage("environment", "Configurando ambiente...", weight=0.1),
        # ... estágios existentes ...
        Stage("meu_novo", "Minha Nova Coisa...", weight=1.0),  # ← Aqui
    ]
    return stages
```

### 2. Implementar a função do estágio

```python
def _stage_meu_novo(progress: Progress) -> None:
    """Estágio: Minha Nova Coisa."""
    from meu_modulo import carregar_algo_pesado

    # Força carregamento
    carregar_algo_pesado()
```

### 3. Conectar ao orquestrador

Em `bootstrap.py`, na função `run()`, adicione ao dicionário `stage_functions`:

```python
stage_functions = {
    # ... estágios existentes ...
    "meu_novo": _stage_meu_novo,  # ← Aqui
}
```

## Configuração de Estágios

### Peso (weight)

Define o peso relativo do estágio para cálculo de progresso total:

- `0.1` - Muito rápido (< 1s)
- `1.0` - Rápido (1-3s)
- `10.0` - Lento (5-15s)

### Descrição Dinâmica

Use os métodos helper de `Stage` para adicionar informação dinâmica à descrição:

```python
# Tamanho de arquivo/banco
stage = stage.with_size_info(size_mb=124.5)
# Resultado: "Inicializando banco... (124.5 MB)"

# Lista de itens
stage = stage.with_collections_info(["identity", "shared-moments"])
# Resultado: "Configurando coleções... (identity, shared-moments)"

# Banco vazio
stage = stage.with_size_info(None)
# Resultado: "Inicializando banco... (novo)"
```

## Cores e Tema

As cores são definidas em `Progress`:

```python
SPINNER_STYLE = "dots.blue"     # Spinner azul
BAR_STYLE = "bar.blue"          # Barra azul
TEXT_STYLE = "progress.description"  # Texto padrão
TIME_STYLE = "progress.elapsed"       # Tempo decorrido
```

Para personalizar, modifique `progress.py`.

## Hooks e Extensões

O sistema de bootstrap foi desenhado para ser extensível:

- **Context managers**: Cada estágio pode usar context managers para medição
- **Error handling**: Erros em estágios são tratados individualmente
- **Logging**: Use `rich.console.print()` para output durante estágios

## Exemplo Completo

```python
# Novo estágio com medição de tempo
def _stage_meu_novo(progress: Progress) -> None:
    import time

    from meu_modulo import carregar_algo_pesado

    start = time.time()

    # Carrega componente
    carregar_algo_pesado()

    elapsed = time.time() - start
    if elapsed > 3.0:
        progress._console.print(
            f"[yellow]Aviso: estágio demorou {elapsed:.1f}s[/yellow]"
        )
```
