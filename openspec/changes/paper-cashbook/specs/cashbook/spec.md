# CashBook Specification

## Purpose

Define o agregado `CashBook` para gerenciar múltiplas moedas no paper trading, permitindo operações com ativos em moedas diferentes da base (ex: comprar BTC-USD com saldo em BRL).

---

## Requirements

### Requirement: CashEntry representa saldo em uma moeda

O sistema SHALL definir `CashEntry` com:
- `currency: Currency` — moeda da entrada
- `amount: Decimal` — quantidade disponível
- `conversion_rate: Decimal` — taxa para moeda base

#### Scenario: Calcular valor em moeda base
- **WHEN** CashEntry tem amount=1000, rate=5.7, currency=USD
- **THEN** `value_in_base_currency` = 5700 (em BRL)

#### Scenario: Taxa zero indica moeda não cotada
- **WHEN** CashEntry tem rate=0
- **THEN** `value_in_base_currency` = 0 (não contabiliza)

---

### Requirement: CashBook gerencia múltiplas moedas

O sistema SHALL definir `CashBook` com:
- `base_currency: Currency` — moeda base para consolidação
- `entries: dict[Currency, CashEntry]` — saldos por moeda

#### Scenario: Total em moeda base
- **WHEN** CashBook tem BRL=50000 (rate=1) e USD=1000 (rate=5.7)
- **THEN** `total_in_base_currency` = 50000 + 5700 = 55700

#### Scenario: Obter moeda inexistente
- **WHEN** CashBook não tem entrada para EUR
- **THEN** `get(EUR)` retorna CashEntry(amount=0, rate=0)

---

### Requirement: CashBook suporta adição de valores

O sistema SHALL implementar `add(currency, amount, rate)`.

#### Scenario: Adicionar em moeda existente
- **WHEN** CashBook tem USD=1000 e adiciona USD=500
- **THEN** USD amount = 1500
- **AND** USD rate é atualizada

#### Scenario: Adicionar em moeda nova
- **WHEN** CashBook não tem EUR e adiciona EUR=100
- **THEN** nova entrada criada com amount=100

---

### Requirement: CashBook suporta subtração de valores

O sistema SHALL implementar `subtract(currency, amount)`.

#### Scenario: Subtrair com saldo suficiente
- **WHEN** CashBook tem USD=1000 e subtrai USD=200
- **THEN** USD amount = 800

#### Scenario: Subtrair com saldo insuficiente
- **WHEN** CashBook tem USD=100 e tenta subtrair USD=200
- **THEN** lança `InsufficientFundsError`

#### Scenario: Subtrair de moeda inexistente
- **WHEN** CashBook não tem EUR e tenta subtrair EUR=100
- **THEN** lança `InsufficientFundsError`

---

### Requirement: CashBook converte entre moedas

O sistema SHALL implementar `convert(amount, from, to, rate)`.

#### Scenario: Converter USD para BRL
- **WHEN** amount=100, from=USD, to=BRL, rate=5.7
- **THEN** retorna 570

#### Scenario: Mesma moeda retorna valor original
- **WHEN** amount=100, from=BRL, to=BRL
- **THEN** retorna 100 (rate ignorada)

---

### Requirement: InsufficientFundsError detalha o erro

O sistema SHALL definir `InsufficientFundsError` com:
- `currency: Currency` — moeda com saldo insuficiente
- `requested: Decimal` — valor solicitado
- `available: Decimal` — valor disponível

#### Scenario: Mensagem de erro clara
- **WHEN** InsufficientFundsError(currency=USD, requested=200, available=100)
- **THEN** str(error) contém "USD", "200", "100"

---

### Requirement: CashBook serializa para persistência

O sistema SHALL implementar `to_dict()` e `from_dict()`.

#### Scenario: Serializar para dict
- **WHEN** CashBook com BRL=50000, USD=1000
- **THEN** `to_dict()` retorna:
  ```json
  {
    "base_currency": "BRL",
    "entries": {
      "BRL": {"amount": 50000, "conversion_rate": 1.0},
      "USD": {"amount": 1000, "conversion_rate": 5.7}
    }
  }
  ```

#### Scenario: Desserializar de dict
- **WHEN** `from_dict(data)` com dict válido
- **THEN** CashBook reconstruído com mesmos valores

---

### Requirement: Factory cria CashBook com moeda única

O sistema SHALL implementar `CashBook.from_single_currency(base, amount)`.

#### Scenario: Criar com saldo em BRL
- **WHEN** `CashBook.from_single_currency(BRL, 100000)`
- **THEN** CashBook com base_currency=BRL
- **AND** única entrada BRL(amount=100000, rate=1.0)

---

## Non-Functional Requirements

### NFR: Performance
- `total_in_base_currency` deve ser O(n) onde n = número de moedas
- Cache de taxas deve ser usado pelo caller (não pelo CashBook)

### NFR: Precisão
- Todos os valores usam `Decimal` (não float)
- Conversões preservam precisão

### NFR: Imutabilidade
- `CashEntry` é imutável (frozen dataclass)
- Operações retornam novas instâncias quando aplicável

---

> "Especificação é contrato" – made by Sky 🚀
