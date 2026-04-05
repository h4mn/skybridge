# Design: Paper Backlog 2026.03.27

## Contexto

O módulo `paper-trading` passou pela migração de estado (`paper-state-migration`) resolvendo:
- ✅ PaperStatePort como dono único do JSON
- ✅ Commands/Queries no DDD
- ✅ Facades API e MCP funcionais

Porém, três gaps permanecem:
1. Sistema 100% reativo — sem componente que "vive"
2. Quantidade como `int` — não suporta frações
3. Câmbio 1:1 — PnL inflado em multi-moeda

---

## Decisões

### D1: Orchestrator + Workers

**Decisão:** Criar `PaperOrchestrator` que coordena workers especializados.

**Estrutura:**
```
facade/sandbox/
├── orchestrator.py          # PaperOrchestrator
├── workers/
│   ├── __init__.py
│   ├── base.py              # Worker base class
│   ├── strategy_worker.py   # Modelagem de estratégias
│   ├── backtest_worker.py   # Simulações históricas
│   └── position_worker.py   # Gerenciamento de posições
└── README.md
```

**Interface:**
```python
class Worker(Protocol):
    """Worker que roda sob o orchestrator."""
    name: str

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def tick(self) -> None: ...  # chamado a cada ciclo

class PaperOrchestrator:
    """Coordena workers e mantém o sistema vivo."""

    def __init__(self, interval_seconds: float = 10.0):
        self._workers: dict[str, Worker] = {}
        self._interval = interval_seconds
        self._running = False

    def register(self, worker: Worker) -> None: ...
    async def run(self) -> None: ...  # loop principal
    async def shutdown(self) -> None: ...
```

**Workers Iniciais:**

| Worker | Responsabilidade | Fase |
|--------|------------------|------|
| `PositionWorker` | Atualizar PnL, verificar ordens limite | 1 |
| `StrategyWorker` | Avaliar condições, sugerir ações | 2 |
| `BacktestWorker` | Rodar simulação com dados históricos | 3 |

**Alternativas Consideradas:**

| Alternativa | Veredito |
|-------------|----------|
| Background thread | ❌ GIL, difícil debug |
| asyncio tasks direto | ❌ Sem coordenação |
| Worker pattern com orchestrator | ✅ Testável, extensível |

---

### D2: Quantity — Value Object Contextual

**Decisão:** Criar `Quantity` como Value Object com precisão por contexto.

**Domain Model:**
```python
@dataclass(frozen=True)
class Quantity:
    """Quantidade com precisão contextual."""
    value: Decimal
    precision: int          # casas decimais
    min_tick: Decimal       # menor unidade negociável
    asset_type: AssetType   # STOCK, CRYPTO, FOREX

    def __post_init__(self):
        # Validar se value está alinhado com precision e min_tick
        ...

    def is_valid_for(self, ticker: str) -> bool:
        """Verifica se a quantidade é válida para o ticker."""
        ...

    def adjust_to_tick(self) -> "Quantity":
        """Ajusta para o tick mais próximo."""
        ...

class AssetType(Enum):
    STOCK = "stock"         # Ações (lotes/inteiro)
    STOCK_FRACTION = "stock_fraction"  # Fracionário
    CRYPTO = "crypto"       # Cripto (alta precisão)
    FOREX = "forex"         # Câmbio
```

**Service para Regras:**
```python
class QuantityRules:
    """Service que conhece regras por ticker/corretora."""

    @staticmethod
    def for_ticker(ticker: str, exchange: str = "B3") -> QuantitySpec:
        """
        Retorna especificação de quantidade para o ticker.

        Exemplos:
        - PETR4.SA (B3) → lote 100, precision 0
        - PETR4F.SA (fracionário) → lote 1, precision 0
        - BTC-USD (crypto) → lote 1, precision 8
        """
        ...

@dataclass(frozen=True)
class QuantitySpec:
    """Especificação de quantidade para um contexto."""
    min_quantity: Decimal
    max_quantity: Decimal
    min_tick: Decimal
    precision: int
    lot_size: int  # 1 para fracionário/cripto
```

**Mapeamento por Tipo:**

| Ticker | Tipo | Precision | Min Tick | Lote |
|--------|------|-----------|----------|------|
| PETR4.SA | STOCK | 0 | 1 | 100 |
| PETR4F.SA | STOCK_FRACTION | 0 | 1 | 1 |
| BTC-USD | CRYPTO | 8 | 0.00000001 | 1 |
| ETH-USD | CRYPTO | 18 | 1e-18 | 1 |
| EUR/USD | FOREX | 5 | 0.00001 | 1000 |

---

### D3: Currency/Money — Sistema Multi-Moeda

**Decisão:** Criar sistema de Money com Currency enum e conversor.

**Domain Model:**
```python
class Currency(Enum):
    """Moedas suportadas."""
    BRL = "BRL"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    BTC = "BTC"
    ETH = "ETH"

    @property
    def is_fiat(self) -> bool:
        return self in (Currency.BRL, Currency.USD, Currency.EUR, Currency.GBP)

    @property
    def is_crypto(self) -> bool:
        return self in (Currency.BTC, Currency.ETH)

@dataclass(frozen=True)
class Money:
    """Value Object para valor monetário com moeda."""
    amount: Decimal
    currency: Currency

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise CurrencyMismatchError(self.currency, other.currency)
        return Money(self.amount + other.amount, self.currency)

    def convert_to(self, target: Currency, rate: Decimal) -> "Money":
        """Converte usando taxa fornecida."""
        if self.currency == target:
            return self
        return Money(self.amount * rate, target)

    def format(self) -> str:
        """Formata para exibição."""
        ...
```

**Port para Conversão:**
```python
class CurrencyConverterPort(Protocol):
    """Port para conversão de moedas."""

    async def get_rate(self, from_currency: Currency, to_currency: Currency) -> Decimal:
        """Retorna taxa de câmbio atual."""
        ...

    async def convert(self, money: Money, to: Currency) -> Money:
        """Converte Money para outra moeda."""
        ...
```

**Adapter Yahoo Finance:**
```python
class YahooCurrencyAdapter(CurrencyConverterPort):
    """Usa Yahoo Finance para taxas de câmbio."""

    # Mapeamento de pares
    PAIRS = {
        (Currency.USD, Currency.BRL): "BRL=X",
        (Currency.EUR, Currency.BRL): "EURBRL=X",
        (Currency.EUR, Currency.USD): "EURUSD=X",
        (Currency.GBP, Currency.USD): "GBPUSD=X",
        # Cripto via tickers normais
        (Currency.BTC, Currency.USD): "BTC-USD",
        (Currency.ETH, Currency.USD): "ETH-USD",
    }
```

**Portfolio Multi-Moeda:**
```python
@dataclass
class PortfolioView:
    """Visão consolidada do portfolio em múltiplas moedas."""

    positions: list[PositionView]
    base_currency: Currency

    @property
    def total_by_currency(self) -> dict[Currency, Money]:
        """Total por moeda sem conversão."""
        ...

    async def total_converted(
        self,
        converter: CurrencyConverterPort,
        target: Currency
    ) -> Money:
        """Soma todas as posições convertidas para target."""
        ...

@dataclass
class PositionView:
    """Posição com valor marcado a mercado."""
    ticker: str
    quantity: Quantity
    market_price: Money  # preço atual na moeda do ativo
    market_value: Money  # quantity * market_price
    cost_basis: Money    # custo de aquisição
    pnl: Money           # lucro/prejuízo
```

**Exemplo de Uso:**
```python
# Portfolio com BTC-USD + PETR4-BRL
portfolio = PortfolioView(
    positions=[
        PositionView(
            ticker="BTC-USD",
            quantity=Quantity(Decimal("0.5"), ...),
            market_price=Money(Decimal("85000"), Currency.USD),
            ...
        ),
        PositionView(
            ticker="PETR4.SA",
            quantity=Quantity(100, ...),
            market_price=Money(Decimal("49.26"), Currency.BRL),
            ...
        ),
    ],
    base_currency=Currency.BRL
)

# Consolidar em BRL
total_brl = await portfolio.total_converted(converter, Currency.BRL)
# R$ 42.500,00 (BTC) + R$ 4.926,00 (PETR4) = R$ 47.426,00

# Ou em USD
total_usd = await portfolio.total_converted(converter, Currency.USD)
# U$ 8.500,00 (BTC) + U$ 985,20 (PETR4) = U$ 9.485,20
```

---

## Estrutura de Arquivos

```
src/core/paper/
├── domain/
│   ├── quantity.py              # Quantity VO + AssetType enum
│   ├── money.py                 # Money VO + Currency enum
│   └── portfolio_view.py        # PositionView + PortfolioView
├── ports/
│   └── currency_converter_port.py
├── adapters/
│   └── currency/
│       └── yahoo_currency_adapter.py
├── services/
│   └── quantity_rules.py        # Service de regras por ticker
└── facade/sandbox/
    ├── orchestrator.py
    └── workers/
        ├── base.py
        ├── position_worker.py
        ├── strategy_worker.py
        └── backtest_worker.py
```

---

## Fases

### Fase 1: Quantity + Money (Domain)
- Criar `Quantity` VO
- Criar `Money` VO + `Currency` enum
- Criar `QuantityRules` service
- Testes unitários

### Fase 2: Currency Converter
- Criar `CurrencyConverterPort`
- Implementar `YahooCurrencyAdapter`
- Integrar com `ConsultarPortfolioHandler`
- Testes com API real

### Fase 3: Portfolio Multi-Moeda
- Criar `PositionView` e `PortfolioView`
- Atualizar handlers para usar Money
- Endpoint com parâmetro `base_currency`
- Smoke test: BTC-USD + PETR4-BRL consolidados

### Fase 4: Orchestrator + Workers (Sandbox)
- Criar `PaperOrchestrator`
- Criar `PositionWorker`
- Criar `StrategyWorker` (stub)
- Criar `BacktestWorker` (stub)
- Experimento no sandbox

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Breaking change em Quantity | Migration layer temporária |
| Rate limit Yahoo para câmbio | Cache 5min TTL |
| Complexidade do Orchestrator | Fase 4 isolada no sandbox |
| Precisão de cripto variável | `QuantityRules` extensível |

---

## Open Questions

1. **Quantidade negativa** — Permitir short? Como modelar?
2. **Cache de câmbio** — Redis ou em memória?
3. **Orchestrator persistence** — Salvar estado entre restarts?

> "Antes de automatizar, precisa estar vivo" – made by Sky 🚀
