# Design: Paper CashBook

## Contexto

O módulo `paper-trading` já possui infraestrutura de moeda:
- `Currency` enum (BRL, USD, EUR, GBP, BTC, ETH)
- `Money` Value Object (amount + currency)
- `CurrencyConverterPort` + `YahooCurrencyAdapter`

Porém, o `PaperBroker` usa `saldo: Decimal` sem noção de moeda. Isso causa o GAP-2.

## Decisões

### D1: CashBook como Agregado de Caixa

**Decisão:** Criar `CashBook` que mantém múltiplas moedas com conversão para base.

**Estrutura:**
```python
@dataclass
class CashEntry:
    """Entrada de caixa em uma moeda específica."""
    currency: Currency
    amount: Decimal
    conversion_rate: Decimal  # Taxa para base_currency

    @property
    def value_in_base_currency(self) -> Decimal:
        return self.amount * self.conversion_rate


@dataclass
class CashBook:
    """Livro de caixa multi-moeda."""
    base_currency: Currency
    _entries: dict[Currency, CashEntry]

    @property
    def total_in_base_currency(self) -> Decimal:
        return sum(e.value_in_base_currency for e in self._entries.values())

    def get(self, currency: Currency) -> CashEntry:
        """Retorna entrada de uma moeda (0 se não existir)."""
        return self._entries.get(currency, CashEntry(currency, Decimal(0), Decimal(0)))

    def add(self, currency: Currency, amount: Decimal, rate: Decimal) -> None:
        """Adiciona valor a uma moeda."""
        if currency in self._entries:
            self._entries[currency].amount += amount
            self._entries[currency].conversion_rate = rate
        else:
            self._entries[currency] = CashEntry(currency, amount, rate)

    def subtract(self, currency: Currency, amount: Decimal) -> None:
        """Subtrai valor de uma moeda."""
        if currency not in self._entries:
            raise InsufficientFundsError(currency, amount, Decimal(0))
        if self._entries[currency].amount < amount:
            raise InsufficientFundsError(currency, amount, self._entries[currency].amount)
        self._entries[currency].amount -= amount

    def convert(
        self,
        amount: Decimal,
        from_currency: Currency,
        to_currency: Currency,
        rate: Decimal
    ) -> Decimal:
        """Converte valor entre moedas usando taxa fornecida."""
        if from_currency == to_currency:
            return amount
        return amount * rate
```

**Racional:**
- Segue padrão QuantConnect LEAN (`CashBook` + `Cash`)
- Permite múltiplas moedas sem complexidade
- Taxa de conversão atualizável em tempo real

---

### D2: PaperBroker usa CashBook

**Decisão:** Substituir `saldo: Decimal` por `cashbook: CashBook`.

**Antes:**
```python
class PaperBroker:
    def __init__(self, feed, saldo_inicial: Decimal):
        self.saldo = saldo_inicial
        # ...

    async def enviar_ordem(self, ticker, lado, quantidade):
        valor_total = preco * quantidade
        if valor_total > self.saldo:  # BUG: moedas diferentes
            raise SaldoInsuficienteError(...)
        self.saldo -= valor_total
```

**Depois:**
```python
class PaperBroker:
    def __init__(
        self,
        feed: DataFeedPort,
        converter: CurrencyConverterPort,
        cashbook: CashBook,
    ):
        self._feed = feed
        self._converter = converter
        self.cashbook = cashbook
        # ...

    async def enviar_ordem(self, ticker, lado, quantidade):
        cotacao = await self._feed.obter_cotacao(ticker)
        asset_currency = self._infer_currency(ticker)  # USD para BTC-USD
        preco = cotacao.preco
        valor_total = preco * quantidade

        # Obtém taxa de conversão para base
        rate = await self._converter.get_rate(asset_currency, self.cashbook.base_currency)
        valor_em_base = valor_total * rate

        # Verifica saldo total convertido
        if valor_em_base > self.cashbook.total_in_base_currency:
            raise SaldoInsuficienteError(...)

        # Tenta debitar da moeda do ativo primeiro
        try:
            self.cashbook.subtract(asset_currency, valor_total)
        except InsufficientFundsError:
            # Converte de base_currency para asset_currency
            self.cashbook.subtract(self.cashbook.base_currency, valor_em_base)
            self.cashbook.add(asset_currency, valor_total, rate)

        # ... resto da lógica
```

**Racional:**
- Preserva moeda original do ativo
- Conversão só quando necessário
- Saldo total sempre disponível em base_currency

---

### D3: PaperState com base_currency

**Decisão:** Adicionar `base_currency` ao estado e migrar `saldo`.

**Antes:**
```python
@dataclass
class PaperState:
    saldo: Decimal
    saldo_inicial: Decimal
    # ...
```

**Depois:**
```python
@dataclass
class PaperState:
    base_currency: Currency = Currency.BRL
    cashbook: dict[str, dict] = field(default_factory=dict)  # { "BRL": {"amount": 100000, "rate": 1.0} }
    saldo_inicial: Decimal = Decimal("100000")  # Mantido para compat
    # ...

    @property
    def saldo(self) -> Decimal:
        """Compatibilidade: retorna total em base_currency."""
        return sum(e["amount"] * e["rate"] for e in self.cashbook.values())
```

**Migration:**
```python
# No carregamento do JSON
def carregar(self) -> PaperState:
    data = json.load(...)
    if "saldo" in data and "cashbook" not in data:
        # Migration: saldo → cashbook
        data["cashbook"] = {
            "BRL": {"amount": data["saldo"], "rate": 1.0}
        }
    return PaperState(**data)
```

---

### D4: API mostra saldos por moeda

**Decisão:** Endpoint `/portfolio` retorna breakdown por moeda.

**Response:**
```json
{
  "cashbook": {
    "BRL": { "amount": 50000.00, "rate": 1.0, "value_in_base": 50000.00 },
    "USD": { "amount": 1000.00, "rate": 5.7, "value_in_base": 5700.00 }
  },
  "total_cash_in_base_currency": 55700.00,
  "base_currency": "BRL",
  "positions": [...],
  "total_portfolio_value": 120000.00
}
```

---

## Estrutura de Arquivos

```
src/core/paper/
├── domain/
│   ├── cashbook.py           # NOVO: CashBook + CashEntry
│   ├── currency.py           # EXISTENTE
│   └── money.py              # EXISTENTE
├── adapters/
│   ├── brokers/
│   │   ├── paper_broker.py   # MODIFICADO: usa CashBook
│   │   └── json_file_broker.py
│   └── persistence/
│       └── json_file_paper_state.py  # MODIFICADO: migration
├── facade/api/
│   ├── dependencies.py       # MODIFICADO: injeta CashBook
│   └── routes/
│       └── portfolio.py      # MODIFICADO: response com cashbook
└── ports/
    └── currency_converter_port.py  # EXISTENTE
```

---

## Fases

### Fase 1: Domain — CashBook
- Criar `CashEntry` e `CashBook`
- Criar `InsufficientFundsError`
- Testes unitários

### Fase 2: Integration — PaperBroker
- Injetar `CurrencyConverterPort` no broker
- Substituir `saldo` por `cashbook`
- Converter moeda em `enviar_ordem()`
- Testes de integração

### Fase 3: Persistence — PaperState
- Adicionar `base_currency` ao estado
- Migration de `saldo` para `cashbook`
- Testes de persistência

### Fase 4: API — Endpoints
- Atualizar response de `/portfolio`
- Adicionar query param `base_currency`
- Smoke tests

### Fase 5: Validação — Discord MCP
- Testar compra BTC-USD com saldo BRL
- Verificar saldos por moeda
- Validar conversão correta

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Breaking change no JSON | Migration automática no load |
| Taxa de câmbio desatualizada | Cache com TTL 5min (já existe) |
| Complexidade no broker | Manter lógica simples: debita moeda do ativo primeiro |

---

## Open Questions

1. **Ordens limite** — Como converter preço limite quando moedas diferentes?
2. **Short selling** — Como modelar posição negativa no CashBook?
3. **Dividendos** — Em qual moeda creditar?

> "Moeda é o sangue do trading" – made by Sky 🚀
