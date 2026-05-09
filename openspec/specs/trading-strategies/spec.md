## ADDED Requirements

### Requirement: TipoSinal enum
O sistema SHALL definir um enum `TipoSinal` com valores `COMPRA`, `VENDA` e `NEUTRO` para classificar sinais de estratégia.

#### Scenario: Criar tipo de sinal de compra
- **WHEN** instanciar `TipoSinal.COMPARA`
- **THEN** o valor SHALL ser `"compra"` (string lowercase)

#### Scenario: Criar tipo de sinal de venda
- **WHEN** instanciar `TipoSinal.VENDA`
- **THEN** o valor SHALL ser `"venda"` (string lowercase)

#### Scenario: Criar tipo de sinal neutro
- **WHEN** instanciar `TipoSinal.NEUTRO`
- **THEN** o valor SHALL ser `"neutro"` (string lowercase)

### Requirement: DadosMercado value object
O sistema SHALL definir um VO imutável `DadosMercado` contendo ticker (str), preco_atual (Decimal) e historico_precos (tuple[Decimal, ...]).

#### Scenario: Criar dados de mercado
- **WHEN** criar `DadosMercado(ticker="BTC-USD", preco_atual=Decimal("50000"), historico_precos=[...])`
- **THEN** o objeto SHALL ser frozen (imutável)

#### Scenario: DadosMercado com histórico vazio
- **WHEN** criar `DadosMercado` com `historico_precos=[]`
- **THEN** o objeto SHALL ser criado sem erro (estratégia decide se usa ou não)

### Requirement: SinalEstrategia value object
O sistema SHALL definir um VO imutável `SinalEstrategia` contendo ticker (str), tipo (TipoSinal), preco (Decimal), razao (str) e timestamp (datetime).

#### Scenario: Criar sinal de compra
- **WHEN** criar `SinalEstrategia(ticker="BTC-USD", tipo=TipoSinal.COMPRA, preco=Decimal("50000"), razao="SMA5 > SMA15")`
- **THEN** o objeto SHALL ser frozen e `timestamp` SHALL ser preenchido automaticamente com `datetime.now()` se não fornecido

#### Scenario: Serializar sinal para dict
- **WHEN** chamar `sinal.to_dict()` em um `SinalEstrategia`
- **THEN** SHALL retornar dict com chaves `ticker`, `tipo`, `preco`, `razao`, `timestamp`

### Requirement: StrategyProtocol interface
O sistema SHALL definir um `StrategyProtocol` (typing.Protocol) com propriedade `name: str` e método `evaluate(dados: DadosMercado) -> SinalEstrategia | None`.

#### Scenario: Duck typing com StrategyProtocol
- **WHEN** uma classe qualquer implementa `name` e `evaluate(dados)`
- **THEN** ela SHALL satisfazer o StrategyProtocol sem herança explícita

#### Scenario: Estratégia retorna None quando sem sinal
- **WHEN** `evaluate()` não detecta oportunidade
- **THEN** SHALL retornar `None`

#### Scenario: Estratégia retorna sinal quando detecta oportunidade
- **WHEN** `evaluate()` detecta oportunidade de compra/venda
- **THEN** SHALL retornar `SinalEstrategia` com `tipo` diferente de `NEUTRO`

> "Value objects são a verdade que não mente" – made by Sky 🎯
