# Sandbox Facade

Área de experimentos e validação da arquitetura DDD do Paper Trading.

> **Nota:** Este é um playground para testes. Para produção, use a API oficial
> em `facade/api/` ou as ferramentas MCP em `facade/mcp/`.

## Como Executar

### API Sandbox

```bash
# Na raiz do projeto
uvicorn src.core.paper.facade.sandbox.facade:app --reload --port 8000
```

### Orchestrator (Sistema "Vivo")

```bash
# Executa orchestrator com workers
python -m src.core.paper.facade.sandbox.run_orchestrator

# Ctrl+C para shutdown graceful
```

## Endpoints API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Hello World |
| GET | `/health` | Health check |
| GET | `/portfolio` | Consulta portfolio padrão |
| GET | `/portfolio?base_currency=USD` | Portfolio consolidado em USD |

## Fluxo Demonstrado

```
GET /portfolio
    ↓
SandboxFacade (facade.py)
    ↓
ConsultarPortfolioQuery (application/queries/)
    ↓
ConsultarPortfolioHandler (application/handlers/)
    ↓
JsonFilePaperBroker (adapters/brokers/)
    ↓
PaperStatePort → paper_state.json
```

## PaperOrchestrator

O **Orchestrator** coordena workers que mantêm o paper trading "vivo":

```
PaperOrchestrator
    ├── PositionWorker   → Atualiza cotações, verifica ordens limite
    ├── StrategyWorker   → Avalia condições, sugere ações (stub)
    └── BacktestWorker   → Simulações históricas (stub)
```

### Uso Programático

```python
from src.core.paper.facade.sandbox.orchestrator import PaperOrchestrator
from src.core.paper.facade.sandbox.workers import (
    PositionWorker,
    StrategyWorker,
    BacktestWorker,
)

# Cria orchestrator
orchestrator = PaperOrchestrator(interval_seconds=10.0)

# Adiciona workers
orchestrator.register(PositionWorker(
    portfolio_id="main",
    tickers=["PETR4.SA", "BTC-USD"],
    on_pnl_change=lambda pnl, pct: print(f"PnL: {pnl} ({pct}%)"),
))

orchestrator.register(StrategyWorker(
    strategy_name="momentum",
    on_suggestion=lambda ticker, action: print(f"{action} {ticker}"),
))

# Executa (bloqueante)
await orchestrator.run()

# Shutdown graceful
await orchestrator.shutdown()
```

### Interface Worker

```python
from src.core.paper.facade.sandbox.workers.base import Worker, BaseWorker

class MeuWorker(BaseWorker):
    def __init__(self):
        super().__init__(name="meu_worker")

    async def _do_tick(self) -> None:
        # Lógica executada a cada ciclo
        ...
```

## Exemplo de Resposta

```json
// GET /portfolio?base_currency=BRL
{
  "id": "uuid-gerado",
  "nome": "Portfolio Principal",
  "saldo_inicial": 100000.0,
  "saldo_atual": 105000.0,
  "pnl": 5000.0,
  "pnl_percentual": 5.0,
  "currency": "BRL"
}
```

## Documentação Interativa

Após iniciar o servidor, acesse:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

> "Antes de automatizar, precisa estar vivo" – made by Sky 🚀
