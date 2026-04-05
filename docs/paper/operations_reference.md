# Operations Reference — Paper Trading

## API Endpoints

### Portfolio

#### `GET /portfolio`

Retorna o portfolio completo com PnL calculado.

**Parâmetros:**
| Nome | Tipo | Descrição |
|------|------|-----------|
| `base_currency` | string | Moeda para consolidação (BRL, USD, EUR, GBP, BTC, ETH) |

**Exemplo:**
```bash
curl "http://localhost:8001/portfolio?base_currency=USD"
```

**Resposta:**
```json
{
  "id": "default",
  "nome": "Portfolio Principal",
  "saldo_inicial": 100000.0,
  "saldo_atual": 105000.0,
  "pnl": 5000.0,
  "pnl_percentual": 5.0,
  "currency": "USD"
}
```

---

#### `GET /posicoes`

Lista posições abertas marcadas a mercado.

**Resposta:**
```json
[
  {
    "ticker": "PETR4.SA",
    "quantidade": 100,
    "preco_medio": 35.0,
    "preco_atual": 38.0,
    "custo_total": 3500.0,
    "valor_atual": 3800.0,
    "pnl": 300.0,
    "pnl_percentual": 8.57
  }
]
```

---

### Cotações

#### `GET /cotacao/{ticker}`

Retorna cotação atual via Yahoo Finance.

**Tickers suportados:**
- B3: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`
- Cripto: `BTC-USD`, `ETH-USD`, `SOL-USD`
- EUA: `AAPL`, `MSFT`, `TSLA`

---

### Ordens

#### `POST /ordem`

Executa ordem de compra ou venda.

**Body:**
```json
{
  "ticker": "PETR4.SA",
  "lado": "COMPRA",
  "quantidade": 100
}
```

---

## Orchestrator

### Executar

```bash
python -m src.core.paper.facade.sandbox.run_orchestrator
```

### Uso Programático

```python
from src.core.paper.facade.sandbox.orchestrator import PaperOrchestrator
from src.core.paper.facade.sandbox.workers import PositionWorker

orchestrator = PaperOrchestrator(interval_seconds=10.0)
orchestrator.register(PositionWorker(
    portfolio_id="main",
    tickers=["PETR4.SA", "BTC-USD"],
    on_pnl_change=lambda pnl, pct: print(f"PnL: {pnl}"),
))

await orchestrator.run()
```

---

## Conversão de Moedas

### Taxa de Câmbio

```python
from src.core.paper.adapters.currency.yahoo_currency_adapter import YahooCurrencyAdapter
from src.core.paper.domain.currency import Currency

adapter = YahooCurrencyAdapter()
rate = await adapter.get_rate(Currency.USD, Currency.BRL)
# rate ≈ 5.23
```

### Converter Valor

```python
from src.core.paper.domain.money import Money

usd = Money(100, Currency.USD)
brl = await adapter.convert(usd, Currency.BRL)
# brl.amount ≈ 523.51
```

---

## Quantity Rules

### Regras por Ticker

```python
from src.core.paper.services.quantity_rules import QuantityRules

# B3 - Lote padrão
spec_b3 = QuantityRules.for_ticker("PETR4.SA", "B3")
# lot_size=100, precision=0

# Cripto - Alta precisão
spec_crypto = QuantityRules.for_ticker("BTC-USD", "CRYPTO")
# lot_size=1, precision=8
```

---

> "Antes de automatizar, precisa estar vivo" – made by Sky 🚀
