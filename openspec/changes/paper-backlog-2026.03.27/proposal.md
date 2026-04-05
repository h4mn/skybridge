# Proposal: Paper Backlog 2026.03.27

## Resumo

Implementação dos três principais gaps identificados pelo consultor no módulo de paper trading:

1. **Orchestrator + Workers** — Sistema que mantém o paper trading "vivo"
2. **Quantity (Decimal)** — Value Objects para quantidades contextuais
3. **Currency/Money** — Sistema multi-moeda com conversão

## Motivação

Durante a avaliação do consultor (`paper-trading-module-improvement-2026.03.27.md`), foram identificados gaps críticos não resolvidos na migração anterior:

| Gap | Impacto | Prioridade |
|-----|---------|------------|
| Quantidade como int | Não opera 0.1 BTC | Alta |
| Câmbio hardcoded 1:1 | PnL inflado R$150k | Alta |
| Sem componente ativo | Sistema 100% reativo | Média |

## Escopo

### Incluído

1. **Orchestrator + Workers**
   - `PaperOrchestrator` que coordena workers
   - `StrategyWorker` para modelagem de estratégias
   - `BacktestWorker` para simulações históricas
   - `PositionWorker` para gerenciamento de posições
   - Implementação no `facade/sandbox/`

2. **Quantity (Value Object + Services)**
   - `Quantity` VO com precisão contextual
   - `QuantityRules` service por ticker/corretora
   - Suporte a B3 (lotes), cripto (satoshis), forex

3. **Currency/Money**
   - `Currency` enum (BRL, USD, EUR, BTC, ETH)
   - `Money` VO com amount + currency
   - `CurrencyConverterPort` + adapter Yahoo
   - `PortfolioView` multi-moeda com consolidação

### Não Incluído

- Estratégias automatizadas (próxima change)
- Integração com broker real
- Persistência em SQLite

## Critérios de Sucesso

- [x] Orchestrator roda no sandbox com pelo menos 1 worker
- [x] Quantity VO suporta BTC com 8 casas e PETR4 com lotes
- [x] CurrencyConverter converte USD→BRL via Yahoo
- [x] Portfolio consolida BTC-USD + PETR4-BRL em R$ ou U$

## Dependências

- `paper-state-migration` (arquivada) — PaperStatePort já implementado
- Yahoo Finance para cotações e câmbio

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Complexidade do Orchestrator | Começar simples no sandbox |
| Precisão de cripto variável | Pesquisar por ticker |
| Rate limit Yahoo para câmbio | Cache com TTL |

> "Antes de automatizar, precisa estar vivo" – made by Sky 🚀
