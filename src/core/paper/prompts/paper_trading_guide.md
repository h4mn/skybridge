# Paper Trading Guide

## Visão Geral

O módulo de Paper Trading permite simular operações de compra e venda de ativos com dados de mercado reais, sem risco financeiro real.

## Capacidades

### Consulta de Mercado
- **Cotações em tempo real**: Preços atualizados via Yahoo Finance
- **Histórico de preços**: Candlesticks OHLCV para análise técnica
- **Tickers suportados**:
  - B3: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`, `BBDC4.SA`
  - Cripto: `BTC-USD`, `ETH-USD`, `SOL-USD`
  - EUA: `AAPL`, `MSFT`, `TSLA`, `GOOGL`

### Operações
- **Compra/Venda**: Ordens a mercado executadas instantaneamente
- **Depósito**: Adicionar saldo ao portfolio
- **Reset**: Limpar posições e voltar ao saldo inicial

### Análise
- **PnL**: Lucro/prejuízo marcado a mercado
- **Posições**: Visualizar carteira atual
- **Histórico de ordens**: Rastro de todas operações

## Fluxo de Uso

1. Consultar cotação do ativo desejado
2. Verificar saldo disponível
3. Executar ordem de compra ou venda
4. Acompanhar PnL das posições

## Limitações

- Sem ordens limitadas (apenas a mercado)
- Sem short selling
- Sem cotação em tempo real (atualização sob demanda)
- Dados com delay de alguns minutos

## Exemplo de Conversa

```
Usuário: Qual o preço da Petrobras?
Assistente: [consulta cotação] PETR4.SA está cotada a R$ 49,26.

Usuário: Compra 100 ações.
Assistente: [executa ordem] Ordem executada! Comprou 100x PETR4.SA
a R$ 49,26 (total: R$ 4.926,00).

Usuário: Como está meu portfolio?
Assistente: [consulta portfolio] Seu portfolio tem:
- Saldo: R$ 95.074,00
- Posições: 100 PETR4.SA (R$ 4.926,00)
- Patrimônio: R$ 100.000,00
- PnL: R$ 0,00 (0%)
```

> "O papel aceita qualquer ordem, o mercado não." – made by Sky 📈
