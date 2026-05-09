## ADDED Requirements

### Requirement: Cálculo de SMA
O Guardião Conservador SHALL calcular a Simple Moving Average (SMA) para um período dado a partir de uma lista de preços.

#### Scenario: SMA com dados suficientes
- **WHEN** calcular SMA(3) com preços [10, 20, 30]
- **THEN** o resultado SHALL ser `Decimal("20")` ((10+20+30)/3)

#### Scenario: SMA com dados insuficientes
- **WHEN** calcular SMA(5) com preços [10, 20]
- **THEN** SHALL retornar `None` (não há dados suficientes)

#### Scenario: SMA com histórico exato
- **WHEN** calcular SMA(5) com exatamente 5 preços
- **THEN** SHALL retornar a média aritmética dos 5 preços

### Requirement: Detecção de crossover
O Guardião Conservador SHALL detectar quando a SMA curta cruza a SMA longa para cima (sinal de compra) ou para baixo (sinal de venda).

#### Scenario: Crossover de compra
- **WHEN** SMA(5) atual > SMA(15) atual E SMA(5) anterior <= SMA(15) anterior
- **THEN** SHALL gerar sinal com `TipoSinal.COMPRA` e razao contendo "SMA5 cruzou acima de SMA15"

#### Scenario: Crossover de venda
- **WHEN** SMA(5) atual < SMA(15) atual E SMA(5) anterior >= SMA(15) anterior
- **THEN** SHALL gerar sinal com `TipoSinal.VENDA` e razao contendo "SMA5 cruzou abaixo de SMA15"

#### Scenario: Sem crossover (tendência mantida)
- **WHEN** SMA(5) estava acima e continua acima (sem cruzamento)
- **THEN** SHALL retornar `None` (sem sinal)

#### Scenario: Dados insuficientes para SMA
- **WHEN** histórico tem menos de 15 preços (período da SMA longa)
- **THEN** SHALL retornar `None` (não pode calcular)

### Requirement: Propriedade name
O Guardião Conservador SHALL ter propriedade `name` com valor `"guardiao-conservador"`.

#### Scenario: Nome da estratégia
- **WHEN** acessar `strategy.name`
- **THEN** SHALL retornar `"guardiao-conservador"`

### Requirement: Parâmetros configuráveis
O Guardião Conservador SHALL aceitar `short_period` (default 5) e `long_period` (default 15) no construtor.

#### Scenario: Períodos padrão
- **WHEN** criar `GuardiaoConservador()` sem argumentos
- **THEN** SHALL usar `short_period=5` e `long_period=15`

#### Scenario: Períodos customizados
- **WHEN** criar `GuardiaoConservador(short_period=10, long_period=30)`
- **THEN** SHALL usar os períodos fornecidos

> "O guardião observa as médias e age no cruzamento" – made by Sky 🛡️
