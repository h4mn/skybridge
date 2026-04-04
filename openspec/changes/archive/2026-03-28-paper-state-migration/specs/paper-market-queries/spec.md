# Spec: paper-market-queries

## ADDED Requirements

### Requirement: ConsultarCotacaoQuery retorna preço atual

O sistema SHALL definir `ConsultarCotacaoQuery` com:
- `ticker: str`

#### Scenario: Cotação de ticker válido
- **WHEN** query com ticker="BTC-USD"
- **THEN** retorna `CotacaoResult` com preco, variacao_dia, updated_at

#### Scenario: Cotação de ticker brasileiro
- **WHEN** query com ticker="PETR4.SA"
- **THEN** retorna cotação em BRL

#### Scenario: Ticker inválido retorna erro
- **WHEN** query com ticker="INVALIDO"
- **THEN** retorna erro "ticker_nao_encontrado"

---

### Requirement: ConsultarCotacaoHandler delega para DataFeedPort

O handler SHALL usar `DataFeedPort.obter_cotacao()` para obter dados.

#### Scenario: Handler usa feed injetado
- **WHEN** handler processa query
- **THEN** chama `feed.obter_cotacao(ticker)`
- **AND** mapeia resultado para `CotacaoResult`

---

### Requirement: ConsultarHistoricoQuery retorna série temporal

O sistema SHALL definir `ConsultarHistoricoQuery` com:
- `ticker: str`
- `periodo: str` ("1d", "1w", "1m", "1y")

#### Scenario: Histórico de 7 dias
- **WHEN** query com ticker="BTC-USD", periodo="1w"
- **THEN** retorna lista de `CandleData` com 7 candles diários

#### Scenario: Histórico vazio para ticker sem dados
- **WHEN** ticker não tem histórico disponível
- **THEN** retorna lista vazia

---

### Requirement: ConsultarHistoricoHandler delega para DataFeedPort

O handler SHALL usar `DataFeedPort.obter_historico()`.

#### Scenario: Handler converte período
- **WHEN** periodo="1m"
- **THEN** chama `feed.obter_historico(ticker, dias=30)`

---

### Requirement: CotacaoResult padroniza resposta

O sistema SHALL definir `CotacaoResult` com:
- `ticker: str`
- `preco: Decimal`
- `variacao_dia: Optional[Decimal]`
- `moeda: str`
- `updated_at: datetime`

#### Scenario: Resultado serializável
- **WHEN** `CotacaoResult` é convertido para dict
- **THEN** todos os campos são JSON-serializáveis

---

### Requirement: CandleData representa OHLCV

O sistema SHALL definir `CandleData` com:
- `data: date`
- `abertura: Decimal`
- `alta: Decimal`
- `baixa: Decimal`
- `fechamento: Decimal`
- `volume: Optional[Decimal]`

#### Scenario: Candle completo
- **WHEN** feed retorna dados OHLC
- **THEN** `CandleData` é populado corretamente
