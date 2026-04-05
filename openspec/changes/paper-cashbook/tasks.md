# Tasks: Paper CashBook

## 1. Fase 1 — Domain: CashBook

### 1.1 CashEntry Value Object
- [x] 1.1.1 Criar `src/core/paper/domain/cashbook.py`
- [x] 1.1.2 Criar dataclass `CashEntry` com `currency`, `amount`, `conversion_rate`
- [x] 1.1.3 Implementar property `value_in_base_currency`
- [x] 1.1.4 Implementar `__str__` para formatação
- [x] 1.1.5 Criar testes unitários para CashEntry

### 1.2 CashBook Aggregate
- [x] 1.2.1 Criar dataclass `CashBook` com `base_currency` e `_entries`
- [x] 1.2.2 Implementar property `total_in_base_currency`
- [x] 1.2.3 Implementar `get(currency) -> CashEntry`
- [x] 1.2.4 Implementar `add(currency, amount, rate)`
- [x] 1.2.5 Implementar `subtract(currency, amount)`
- [x] 1.2.6 Implementar `convert(amount, from, to, rate)`
- [x] 1.2.7 Criar `InsufficientFundsError` exception
- [x] 1.2.8 Criar testes unitários para CashBook

### 1.3 Factory Method
- [x] 1.3.1 Criar `CashBook.from_single_currency(base, amount)` factory
- [x] 1.3.2 Criar `CashBook.from_dict(data)` para desserialização
- [x] 1.3.3 Criar `CashBook.to_dict()` para serialização
- [x] 1.3.4 Testes de serialização/desserialização

---

## 2. Fase 2 — Integration: PaperBroker

### 2.1 Injetar CurrencyConverter
- [x] 2.1.1 Adicionar `CurrencyConverterPort` no `__init__` do `PaperBroker`
- [x] 2.1.2 Adicionar `CashBook` no `__init__` do `PaperBroker`
- [x] 2.1.3 Atualizar `JsonFilePaperBroker` para injetar dependências

### 2.2 Atualizar enviar_ordem
- [x] 2.2.1 Inferir moeda do ticker (`_infer_currency(ticker)`)
- [x] 2.2.2 Obter taxa de conversão via `CurrencyConverterPort`
- [x] 2.2.3 Calcular valor em base_currency antes de comparar
- [x] 2.2.4 Debitar da moeda do ativo (ou converter de base)
- [x] 2.2.5 Creditar na moeda correta em vendas
- [x] 2.2.6 Criar testes de integração para compra multi-moeda

### 2.3 Atualizar listar_posicoes_marcadas
- [x] 2.3.1 Calcular valor de posição na moeda do ativo
- [x] 2.3.2 Adicionar campo `currency` no retorno
- [x] 2.3.3 Calcular PnL na moeda correta

### 2.4 Atualizar Dependencies
- [x] 2.4.1 Criar `get_cashbook()` em `dependencies.py`
- [x] 2.4.2 Injetar `CurrencyConverterPort` no `get_broker()`
- [x] 2.4.3 Criar instância inicial do CashBook com saldo do PaperState

---

## 3. Fase 3 — Persistence: PaperState

### 3.1 Atualizar PaperState
- [x] 3.1.1 Adicionar campo `base_currency: Currency = BRL`
- [x] 3.1.2 Adicionar campo `cashbook: dict` no estado
- [x] 3.1.3 Manter `saldo` como property calculada (compatibilidade)
- [x] 3.1.4 Criar migration no `carregar()` para estado legado
### 3.2 Atualizar JsonFilePaperState
- [x] 3.2.1 Serializar CashBook no `salvar()`
- [x] 3.2.2 Desserializar CashBook no `carregar()`
- [x] 3.2.3 Migration: `saldo` → `cashbook` na primeira carga
- [x] 3.2.4 Criar testes de persistência
### 3.3 Atualizar Handlers
- [x] 3.3.1 `DepositarHandler` adiciona ao CashBook
- [x] 3.3.2 `ResetarHandler` limpa CashBook
- [x] 3.3.3 `ConsultarPortfolioHandler` lê do CashBook
---

## 4. Fase 4 — API: Endpoints
### 4.1 Atualizar /portfolio
- [x] 4.1.1 Adicionar campo `cashbook` no response
- [x] 4.1.2 Adicionar campo `total_cash_in_base_currency`
- [x] 4.1.3 Adicionar campo `base_currency`
- [x] 4.1.4 Atualizar schema Pydantic
### 4.2 Query Param base_currency
- [x] 4.2.1 Adicionar parâmetro opcional `base_currency` em `/portfolio`
- [x] 4.2.2 Converter total para moeda solicit
- [x] 4.2.3 Validar moeda suportada
### 4.3 Atualizar /depositar
- [x] 4.3.1 Adicionar parâmetro opcional `currency` (default: base)
- [x] 4.3.2 Creditificar na moeda especificada

---

## 5. Fase 5 — Validação

### 5.1 Testes Unitários
- [x] 5.1.1 Testes de CashBook (domain)
- [x] 5.1.2 Testes de PaperBroker com multi-moeda
- [x] 5.1.3 Testes de PaperState com migration
- [x] 5.1.4 Testes de API endpoints

### 5.2 Smoke Tests
- [x] 5.2.1 Depositar USD via API
- [x] 5.2.2 Comprar ativo em USD (AAPL)
- [x] 5.2.3 Verificar débito do saldo USD (não BRL)
- [x] 5.2.4 Consultar portfolio com cashbook detalhado
- [x] 5.2.5 Verificar taxa de conversão correta

### 5.3 Validação Discord MCP
- [x] 5.3.1 Testar comando de compra BTC-USD
- [x] 5.3.2 Verificar painel mostra saldos por moeda
- [x] 5.3.3 Validar conversão correta no log

---

## 6. Documentação

- [x] 6.1 Atualizar `openspec/specs/paper-commands/spec.md` com moeda
- [x] 6.2 Atualizar `openspec/specs/paper-portfolio-queries/spec.md` com cashbook
- [x] 6.3 Criar spec `openspec/changes/paper-cashbook/specs/cashbook/spec.md`
- [x] 6.4 Atualizar troubleshooting com cenários multi-moeda

---

## Progresso

✅ **100% COMPLETO** (68/68 tarefas)

**Data de conclusão:** 2026-03-30

**Bug corrigido durante validação:**
- Removido `cashbook.add(asset_currency, valor_total, rate)` em `paper_broker.py:145`
- Isso corrigiu o problema onde USD aumentava ao comprar ativo USD com conversão BRL→USD

**Issues Linear:**
- SKY-87: Change principal ✅ Done
- SKY-88: Validação Discord MCP ✅ Done
- SKY-89: Troubleshooting docs ✅ Done

---

> "Multi-moeda, multi-validações, multi-conquistas" – made by Sky 🚀
