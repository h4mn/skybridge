# Spec: Dashboard View

Tela inicial do PaperBot mostrando resumo de corretoras (Binance/Yahoo) e métricas de desempenho.

## ADDED Requirements

### Requirement: Resumo de corretoras

O sistema SHALL exibir um resumo dos saldos e desempenho por corretora.

#### Scenario: Exibição de resumo
- **GIVEN** o estado é DASHBOARD
- **WHEN** a view é renderizada
- **THEN** dois cards de corretora são exibidos lado a lado
- **AND** o card da Binance mostra "Patrimônio" e "Posicionado"
- **AND** o card do Yahoo Finance mostra "Patrimônio" e "Posicionado"
- **AND** um gráfico circular mostra o percentual de desempenho (8,53%)

#### Scenario: Dados em tempo real da Binance
- **GIVEN** o painel Dashboard está ativo
- **WHEN** o usuário visualiza o painel
- **THEN** os dados da Binance são atualizados em tempo real
- **AND** preços são obtidos via `BinancePublicFeed.get_ticker()`

### Requirement: Resumo de desempenho

O sistema SHALL exibir métricas de desempenho global da carteira.

#### Scenario: Exibição de desempenho
- **GIVEN** o estado é DASHBOARD
- **WHEN** a view é renderizada
- **THEN** um card de desempenho é exibido
- **AND** mostra "Maior Alta" (ex: R$ 8.510)
- **AND** mostra "Maior Lucro" (ex: R$ 2.250)
- **AND** mostra "Sharpe" (ex: 1,16)

### Requirement: Interação com botões de ação

O sistema SHALL responder a cliques em botões específicos do Dashboard.

#### Scenario: Botão "Ativos"
- **GIVEN** o estado é DASHBOARD
- **WHEN** o usuário clica em "💰 Ativos"
- **THEN** o estado muda para ASSET_LIST
- **AND** a view é editada com a tabela de ativos

#### Scenario: Botão "Posição" (futuro)
- **GIVEN** o estado é DASHBOARD
- **WHEN** o usuário clica em "📊 Posição"
- **THEN** o estado muda para POSITION
- **AND** a view é editada com posições abertas/fechadas
