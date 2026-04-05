# Proposal: Paper CashBook

## Resumo

Implementação do padrão **CashBook** para gerenciamento de múltiplas moedas no paper trading, inspirado no QuantConnect LEAN. Isso resolve o GAP-2 (conversão BRL/USD) e estabelece base para operações multi-moeda.

## Motivação

Durante os testes M0 do Paper Trading via Discord, identificamos o **GAP-2**: o broker compara preço de ativos em USD (BTC-USD) diretamente com saldo em BRL, sem conversão. Isso gera:

1. **Saldo insuficiente falso** — Comprar 1 BTC a $85k USD com R$100k BRL falha porque 85000 > 100000
2. **PnL inflado** — Vender BTC devolve USD no saldo BRL sem conversão
3. **Inconsistência** — Sistema assume câmbio 1:1 inexistente

**Causa raiz**: `PaperBroker.saldo` é um `Decimal` único, sem noção de moeda.

## Solução Proposta

Implementar **CashBook** seguindo o padrão do QuantConnect LEAN:

```
┌─────────────────────────────────────────────────────────┐
│                     CashBook                            │
├─────────────────────────────────────────────────────────┤
│  base_currency: Currency = BRL                          │
│  cash: Dict[Currency, CashEntry]                        │
│    ├── BRL → { amount: 100000, conversion_rate: 1.0 }   │
│    ├── USD → { amount: 5000, conversion_rate: 5.7 }     │
│    └── BTC → { amount: 0.5, conversion_rate: 485000 }   │
├─────────────────────────────────────────────────────────┤
│  total_in_base_currency: Decimal  (soma convertida)     │
│  convert(amount, from, to): Decimal                     │
└─────────────────────────────────────────────────────────┘
```

## Escopo

### Incluído

1. **Domain: CashBook**
   - `CashEntry` — quantidade + taxa de conversão
   - `CashBook` — dicionário de moedas com base_currency
   - `total_in_base_currency` — valor consolidado

2. **Integration: PaperBroker**
   - Substituir `saldo: Decimal` por `cashbook: CashBook`
   - Converter moeda antes de comparar em `enviar_ordem()`
   - Atualizar posições com moeda correta

3. **Persistence: PaperState**
   - Adicionar `base_currency` ao estado
   - Migrar `saldo` existente para `cashbook`

4. **API Updates**
   - Endpoint `/portfolio` mostra saldo por moeda
   - Query param `base_currency` para consolidação

### Não Incluído

- Orchestrator/Workers (change separada)
- Novas moedas além das já suportadas (BRL, USD, EUR, BTC, ETH)
- Persistência em SQLite

## Critérios de Sucesso

- [ ] Comprar BTC-USD com saldo BRL funciona (converte USD→BRL antes de comparar)
- [ ] Vender BTC-USD creditifica USD no cashbook (não BRL)
- [ ] Endpoint `/portfolio` mostra saldos por moeda + total consolidado
- [ ] Testes unitários cobrindo cenários multi-moeda
- [ ] Smoke test via Discord MCP validado

## Dependências

- `CurrencyConverterPort` + `YahooCurrencyAdapter` (já implementados)
- `Currency` enum e `Money` VO (já implementados)
- Yahoo Finance para taxas de câmbio

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Breaking change no PaperState | Migration layer temporária |
| Rate limit Yahoo para câmbio | Cache 5min TTL (já existe) |
| Complexidade do CashBook | Começar minimalista (apenas saldo) |

## Timeline

| Fase | Duração | Entregável |
|------|---------|------------|
| 1. Domain | 1d | CashBook + CashEntry |
| 2. Integration | 1d | PaperBroker com CashBook |
| 3. Persistence | 0.5d | PaperState migrado |
| 4. API | 0.5d | Endpoints atualizados |
| 5. Validação | 0.5d | Smoke tests via Discord |

> "Antes de contar, precisa saber em que moeda" – made by Sky 🚀
