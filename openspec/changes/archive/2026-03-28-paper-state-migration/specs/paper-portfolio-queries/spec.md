# Spec: paper-portfolio-queries

## ADDED Requirements

### Requirement: ConsultarPortfolioQuery retorna visão consolidada

O sistema SHALL expandir `ConsultarPortfolioQuery` para retornar:
- Saldo disponível
- Posições atuais com preço médio
- PnL não realizado (marcado a mercado)
- PnL realizado acumulado

#### Scenario: Portfolio com posições
- **WHEN** query é processada
- **THEN** retorna `PortfolioResult` com todas as posições
- **AND** cada posição tem pnl_nao_realizado calculado

#### Scenario: Portfolio vazio
- **WHEN** não há posições
- **THEN** retorna apenas saldo disponível
- **AND** lista de posições vazia

---

### Requirement: ConsultarPortfolioHandler marca a mercado

O handler SHALL:
1. Carregar estado via `PaperStatePort`
2. Obter cotação atual para cada posição via `DataFeedPort`
3. Calcular PnL não realizado

#### Scenario: Cálculo de PnL não realizado
- **WHEN** posição em BTC-USD quantidade=1 preco_medio=65000
- **AND** cotação atual=66000
- **THEN** pnl_nao_realizado = (66000 - 65000) * 1 = 1000

#### Scenario: Falha de cotação mantém último preço conhecido
- **WHEN** feed falha para um ticker
- **THEN** usa último preço do posicao.preco_atual
- **AND** marca posição como "stale"

---

### Requirement: PortfolioResult inclui métricas agregadas

O sistema SHALL definir `PortfolioResult` com:
- `saldo_disponivel: Decimal`
- `valor_total_posicoes: Decimal`
- `patrimonio_total: Decimal`
- `pnl_nao_realizado: Decimal`
- `pnl_realizado: Decimal`
- `posicoes: List[PosicaoResult]`

#### Scenario: Patrimônio calculado
- **WHEN** saldo=50000 e valor_total_posicoes=60000
- **THEN** patrimonio_total = 110000

---

### Requirement: PosicaoResult detalha cada posição

O sistema SHALL definir `PosicaoResult` com:
- `ticker: str`
- `quantidade: int`
- `preco_medio: Decimal`
- `preco_atual: Decimal`
- `valor_mercado: Decimal`
- `pnl_nao_realizado: Decimal`
- `variacao_percentual: Decimal`

#### Scenario: Variação percentual positiva
- **WHEN** preco_medio=100 e preco_atual=110
- **THEN** variacao_percentual = 10.0%

---

### Requirement: ConsultarOrdensQuery lista histórico

O sistema SHALL definir `ConsultarOrdensQuery` com:
- `ticker: Optional[str]` (filtro)
- `status: Optional[str]` (filtro: "executada", "rejeitada", "pendente")

#### Scenario: Listar todas as ordens
- **WHEN** query sem filtros
- **THEN** retorna todas as ordens do estado

#### Scenario: Filtrar por ticker
- **WHEN** query com ticker="BTC-USD"
- **THEN** retorna apenas ordens desse ticker

---

### Requirement: ConsultarOrdensHandler lê do PaperState

O handler SHALL usar `PaperStatePort.carregar().ordens`.

#### Scenario: Ordens ordenadas por timestamp
- **WHEN** múltiplas ordens existem
- **THEN** retorna em ordem decrescente de created_at
