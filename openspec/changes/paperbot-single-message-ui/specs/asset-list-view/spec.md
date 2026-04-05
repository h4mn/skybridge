# Spec: Asset List View

Tela listando todos os ativos da carteira com dados em tempo real de múltiplas fontes (Binance, Yahoo Finance, etc.).

## ADDED Requirements

### Requirement: Tabela de ativos

O sistema SHALL exibir uma tabela com todos os ativos da carteira.

#### Scenario: Exibição da tabela
- **GIVEN** o estado é ASSET_LIST
- **WHEN** a view é renderizada
- **THEN** uma tabela é exibida com as colunas: Ícone, Ativo, Fonte, Preço
- **AND** cada linha mostra um ativo diferente (BTCUSDT, PETR4F, MNQ1!, etc.)

#### Scenario: Dados de múltiplas fontes
- **GIVEN** a tabela de ativos está ativa
- **WHEN** a view é renderizada
- **THEN** dados são buscados de múltiplas fontes (Binance, Yahoo Finance, Metatrader, etc.)
- **AND** cada ativo mostra sua fonte de dados específica

### Requirement: Seleção de ativo

O sistema SHALL permitir seleção de um ativo específico para ver detalhes.

#### Scenario: Clique em ativo
- **GIVEN** o estado é ASSET_LIST
- **WHEN** o usuário clica em um botão de ativo (ex: "🪙 Bitcoin")
- **THEN** o estado muda para ASSET_DETAIL
- **AND** `ctx.selected_asset` é definido com o símbolo do ativo (ex: "BTC")
- **AND** a view é editada com detalhes e gráfico do ativo selecionado

#### Scenario: Botões de ativo dinâmicos
- **GIVEN** múltiplos ativos na carteira
- **WHEN** a view ASSET_LIST é renderizada
- **THEN** um botão é criado para cada ativo (BTC, ETH, PETR4F, etc.)
- **AND** cada botão mostra o ícone e nome do ativo

### Requirement: Navegação de volta ao Dashboard

O sistema SHALL permitir retorno ao Dashboard a partir da Asset List.

#### Scenario: Botão Home
- **GIVEN** o estado é ASSET_LIST
- **WHEN** o usuário clica em "🏠 Home"
- **THEN** o estado muda para DASHBOARD
- **AND** a view é editada com conteúdo do Dashboard

#### Scenario: Botão Voltar (do Asset Detail)
- **GIVEN** o estado é ASSET_DETAIL
- **WHEN** o usuário clica em "⬅️ Voltar"
- **THEN** o estado muda para ASSET_LIST
- **AND** `ctx.selected_asset` é resetado para `None`
- **AND** a view é editada com a lista de ativos
