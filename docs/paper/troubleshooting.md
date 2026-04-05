# Troubleshooting — Paper Trading

## Problemas Comuns

### Erro: "ModuleNotFoundError: No module named 'yfinance'"

**Causa:** Dependência não instalada.

**Solução:**
```bash
pip install yfinance
```

---

### Erro: "CurrencyMismatchError: Cannot add Money with different currencies"

**Causa:** Tentativa de somar `Money` com moedas diferentes.

**Solução:** Use `CurrencyConverter.convert()` antes de operar:
```python
from src.core.paper.domain.money import Money
from src.core.paper.domain.currency import Currency

usd = Money(100, Currency.USD)
brl = Money(500, Currency.BRL)

# ERRADO - lança CurrencyMismatchError
# total = usd + brl

# CORRETO - converter primeiro
from src.core.paper.adapters.currency.yahoo_currency_adapter import YahooCurrencyAdapter

converter = YahooCurrencyAdapter()
brl_converted = await converter.convert(usd, Currency.BRL)
total = brl_converted + brl  # Agora funciona
```

---

### Erro: "Rate limit exceeded" ao buscar cotações

**Causa:** Yahoo Finance limita requisições excessivas.

**Solução:** O `YahooCurrencyAdapter` já possui cache com TTL de 5 minutos. Aguarde ou reduza frequência de chamadas.

---

### Orchestrator não responde ao Ctrl+C

**Causa:** Handler de sinal não registrado (comum no Windows).

**Solução:** O script `run_orchestrator.py` trata isso. Use:
```bash
python -m src.core.paper.facade.sandbox.run_orchestrator
```

---

### Quantity inválida para ticker

**Causa:** Quantidade não atende às regras do ticker.

**Solução:** Use `QuantityRules.for_ticker()` para validar:
```python
from src.core.paper.services.quantity_rules import QuantityRules

spec = QuantityRules.for_ticker("PETR4.SA", "B3")
# spec.lot_size = 100 (lote padrão)
# spec.precision = 0
```

---

## Multi-Currency Issues

### Saldo USD aumenta ao comprar ativo em USD

**Sintoma:** Após comprar AAPL (USD), o saldo USD aumenta em vez de diminuir.

**Causa:** Bug corrigido em `paper_broker.py` linha 145 - código adicionava USD ao cashbook durante conversão BRL→USD.

**Solução:** Certifique-se que está usando a versão corrigida do código. O comportamento correto é:
- Com saldo USD suficiente: débita USD
- Sem saldo USD: debita BRL (valor convertido) sem adicionar USD

**Verificação:**
```bash
# Ver comportamento do cashbook
curl "http://localhost:8001/api/v1/paper/portfolio/" | jq '.cashbook'
```

---

### Cashbook com keys "orphaned" fora de entries

**Sintoma:** paper_state.json mostra chaves "BRL"/"USD" diretamente em cashbook, não dentro de "entries".

**Causa:** Múltiplos processos escrevendo no arquivo simultaneamente (processos zombie).

**Solução:**
```bash
# 1. Matar processos zombie
pkill -f "uvicorn.*paper"
pkill -f "python.*paper"

# 2. Limpar cashbook manualmente se necessário
# Editar paper_state.json e mover moedas para cashbook.entries

# 3. Verificar apenas 1 processo rodando
ps aux | grep paper
```

**Prevenção:** O `to_dict()` do CashBook agora limpa keys órfãs automaticamente.

---

### Conversão com taxa incorreta

**Sintoma:** Débito maior que esperado ao comprar ativo USD.

**Causa:** Cache do YahooCurrencyAdapter com taxa expirada.

**Solução:**
```python
# Limpar cache (TTL 5 min)
# Aguarde 5 minutos ou reinicie o servidor
pkill -f "uvicorn.*paper"
uvicorn src.core.paper.facade.api.app:app --port 8001
```

**Verificação da taxa:**
```bash
curl "http://localhost:8001/api/v1/paper/mercado/cotacao/USD-BRL=X"
```

---

### Depósito em moeda não suportada

**Sintoma:** Erro ao depositar EUR, CAD, ou outras moedas.

**Causa:** Currency enum não inclui a moeda desejada.

**Solução temporária:** Adicione moeda ao `Currency` enum:
```python
# src/core/paper/domain/currency.py
class Currency(str, Enum):
    BRL = "BRL"
    USD = "USD"
    EUR = "EUR"  # Adicionar moeda desejada
    # ...
```

---

### Saldo não aparece no portfolio

**Sintoma:** Campo `cashbook` vazio ou null no response de `/portfolio`.

**Causa:** `ConsultarPortfolioHandler` não lê do broker.cashbook.

**Verificação:**
```bash
# Ver se handler está lendo cashbook
grep "broker.cashbook" src/core/paper/application/handlers/consultar_portfolio_handler.py
```

**Solução:** O handler deve incluir:
```python
# No handler
cashbook_entries = []
for currency, entry in broker.cashbook._entries.items():
    cashbook_entries.append(CashbookEntryResponse(
        currency=currency.value,
        amount=float(entry.amount),
        conversion_rate=float(entry.conversion_rate),
        value_in_base_currency=float(entry.value_in_base_currency),
    ))
```

---

## Logs e Debug

### Habilitar logs detalhados

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verificar estado do PaperState

```bash
cat paper_state.json | python -m json.tool
```

---

> "Testes são a especificação que não mente" – made by Sky 🚀
