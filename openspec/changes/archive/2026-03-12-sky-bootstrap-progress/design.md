# Design: Bootstrap com Barra de Carregamento

## Context

### Estado Atual

O `sky.cmd` inicia o Sky Chat através do `scripts/sky_textual.py`, que:

1. Configura variáveis de ambiente (`USE_RAG_MEMORY=true`, etc.)
2. Carrega `.env` (se existir)
3. Instancia `SkyApp()` e chama `app.run()`

**Problema:** A inicialização da `SkyApp` aciona lazy load de componentes pesados de forma síncrona:

- `get_embedding_client()` → `_get_model()` → `SentenceTransformer(model)` **(~5-15s na primeira vez)**
- `get_vector_store()` → `_init_db()` → SQLite setup **(~1-2s)**
- `get_collection_manager()` → criação de coleções **(~100ms)**

Total estimado: **6-17 segundos** de tela preta sem feedback.

### Restrições

- Não pode alterar a arquitetura RAG existente
- Deve ser backward compatible (funcionar sem RAG se desabilitado)
- Windows batch (`sky.cmd`) é o ponto de entrada principal
- Projeto já usa `rich` e `textual` para UI

## Goals / Non-Goals

**Goals:**
- Mostrar barra de progresso durante inicialização dos componentes
- Identificar visualmente qual componente está sendo carregado
- Exibir tempo decorrido para diagnosticar gargalos
- Suportar cancelamento pelo usuário (Ctrl+C)
- Manter compatibilidade com atalhos existentes (`sky.cmd`, `sky.cmd sonnet`, etc.)

**Non-Goals:**
- Otimizar o tempo de carregamento (isso é outro projeto)
- Paralelizar carregamento de componentes (risco de race conditions)
- Alterar a arquitetura de singletons existentes
- Criar sistema de plugins genérico

## Decisions

### 1. Rich Console Progress Bar vs Textual Loading Screen

**Decisão:** Usar `rich.progress` no console antes de iniciar Textual.

**Racional:**
- Textual ainda não está inicializado durante o bootstrap pesado
- Rich já é usado no projeto
- Console output funciona mesmo se Textual falhar
- Permite ver logs de erro se algo der errado

**Alternativa rejeitada:** Tela de loading do Textual
- Requer inicializar Textual antes dos componentes pesados
- Adiciona overhead adicional
- Mais complexo de implementar corretamente

### 2. Instrumentação Decorator vs Context Manager

**Decisão:** Usar **context manager** para medir estágios.

**Racional:**
```python
with BootstrapStage("Carregando modelo de embedding..."):
    model = SentenceTransformer(model_name)
```

**Alternativa rejeitada:** Decorator `@instrumented`
- Mais complexo para aplicar em singletons existentes
- Difícil de adaptar para código legado
- Context manager é mais pythonico para operações demoradas

### 3. Orquestração Centralizada vs Distribuída

**Decisão:** **Orquestração centralizada** em `core/sky/bootstrap/`.

**Racional:**
- Ponto único de verdade para ordem de carregamento
- Fácil de testar e modificar
- Isola código de bootstrap da lógica de negócio
- **Sky é auto-contida** - pode mover `core/sky/` para outro projeto

**Alternativa rejeitada:** Instrumentar cada componente individualmente
- Dificulta entender o fluxo completo
- Mais acoplado à implementação
- Difícil de manter ordem garantida

### 4. Ponto de Entrada: Script Python vs Wrapper Batch

**Decisão:** **Script Python intermediário** (`scripts/sky_bootstrap.py`).

**Racional:**
- `sky.cmd` → `sky_bootstrap.py` → `sky_textual.py`
- Permite mostrar progresso mesmo antes de importar componentes pesados
- Fácil fallback para comportamento antigo

**Fluxo:**
```batch
REM sky.cmd
python scripts\sky_bootstrap.py %*
```

```python
# sky_bootstrap.py
from core.sky.bootstrap import run
run()  # Mostra barra de progresso
# Depois chama SkyApp().run()
```

## Arquitetura Proposta

```
sky.cmd
    ↓
scripts/sky_bootstrap.py
    ↓
core/sky/bootstrap/__init__.py
    ├── Stage (context manager)
    ├── Progress (rich progress bar)
    └── run() (orquestrador)
    ↓
[Estágios]
    1. Ambiente ✓
    2. Embedding Model ████████░░  (5-15s)
    3. Vector DB ✓
    4. Collections ✓
    5. Textual UI ✓
    ↓
core/sky/chat/textual_ui.py (SkyApp)
```

### Componentes

```python
# core/sky/bootstrap/__init__.py
from .bootstrap import run
from .stage import Stage
from .progress import Progress

__all__ = ["run", "Stage", "Progress"]
```

```python
# core/sky/bootstrap/stage.py
from dataclasses import dataclass

@dataclass
class Stage:
    """Configuração de um estágio de bootstrap."""
    name: str
    description: str
```

```python
# core/sky/bootstrap/progress.py
from rich.progress import Progress, BarColumn, TimeElapsedColumn

class Progress:
    """Gerencia barra de progresso do bootstrap."""

    def __init__(self):
        self._stages: list[Stage] = []
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        )

    def add_stage(self, stage: Stage):
        """Adiciona um estágio ao bootstrap."""
        self._stages.append(stage)

    def run_stage(self, fn, *args, **kwargs):
        """Executa um estágio mostrando progresso."""
        # ...
```

## Implementação por Estágio

### Estágio 1: Ambiente
- Verificar PYTHONPATH
- Carregar .env
- Validar variáveis de ambiente

### Estágio 2: Embedding Model
- Importar `sentence_transformers`
- Carregar `SentenceTransformer(model_name)`
- Cache em `~/.cache/huggingface/hub/`

### Estágio 3: Vector DB
- Conectar ao SQLite (`sky_memory.db`)
- Criar tabelas virtuais sqlite-vec
- Verificar integridade
- **Calcular tamanho do banco em MB**
- **Mostrar: "Inicializando banco vetorial... (X MB)" ou "(novo)"**

### Estágio 4: Collections
- Inicializar CollectionManager
- Listar coleções existentes (identity, shared-moments, teachings, operational)
- Criar coleções padrão se não existirem
- Carregar configurações
- **Mostrar: "Configurando coleções... (identity, shared-moments, teachings, operational)"**

### Estágio 5: Textual UI
- Importar SkyApp
- Inicializar app
- Chamar `app.run()`

## Risks / Trade-offs

| Risk | Mitigação |
|------|-----------|
| **Modelo não cacheado** → Primeira execução pode demorar muito | Detectar e avisar usuário para baixar modelo antes |
| **SQLite corrompido** → Falha no estágio 3 | Tratamento de erro com mensagem amigável |
| **Rich não instalado** → Falha no bootstrap | Verificar dependência no topo ou fazer fallback |
| **Erro no meio do bootstrap** → Estado inconsistente | Implementar rollback/cleanup em caso de erro |

## Trade-offs

1. **Complexidade adicional** vs **Melhor UX**
   - Aceito: UX durante inicialização justifica complexidade modesta

2. **Tempo extra de boot** (~100-200ms) vs **Feedback visual**
   - Aceito: Custo marginal vs benefício de saber o que está acontecendo

3. **Acoplamento ao Rich** vs **Independência de UI**
   - Aceito: Rich já é dependência do projeto

## Open Questions

1. **Devemos mostrar progresso DENTRO do carregamento do modelo SentenceTransformer?**
   - SentenceTransformer não expõe callback de progresso facilmente
   - Decisão: Não por enquanto (estágio é "tudo ou nada")

2. **Devemos permitir pular o bootstrap com flag `--no-bootstrap`?**
   - Útil para debug/testes
   - Decisão: Sim, adicionar flag

3. **Devemos persistir tempos de boot para análise?**
   - Útil para identificar regressões de performance
   - Decisão: Não por agora (out of scope), mas deixar porta aberta

## Plano de Testes

1. **Teste unitário**: `BootstrapProgress` com estágios mockados
2. **Teste de integração**: Bootstrap completo com componentes reais
3. **Teste de fallback**: Comportamento com `--no-bootstrap`
4. **Teste de erro**: Falha em cada estágio individualmente

## Métricas de Sucesso

- Tempo até primeira mensagem visual: < 1s (hoje: 0s, mas é tela preta)
- Usuário consegue identificar qual componente está demorando: SIM
- Possibilidade de cancelar com Ctrl+C: SIM
- Overhead de performance: < 200ms
