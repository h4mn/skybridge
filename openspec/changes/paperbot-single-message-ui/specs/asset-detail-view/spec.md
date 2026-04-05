# Spec: Asset Detail View

Tela mostrando detalhes específicos de um ativo selecionado: gráfico candlestick, dados de 24h, e menu de negociação.

## ADDED Requirements

### Requirement: Gráfico candlestick

O sistema SHALL exibir um gráfico candlestick do ativo selecionado.

#### Scenario: Geração de gráfico
- **GIVEN** o estado é ASSET_DETAIL
- **AND** `ctx.selected_asset` está definido (ex: "BTC")
- **WHEN** o usuário clica em "📈 Gráfico <ATIVO>"
- **THEN** o bot chama `BinancePublicFeed.get_klines(symbol, "1h", 24)`
- **AND** um gráfico candlestick é gerado com matplotlib
- **AND** o gráfico é enviado como anexo da mensagem
- **AND** o embed é atualizado com a imagem do gráfico

#### Scenario: Dados do gráfico
- **GIVEN** o gráfico foi gerado
- **WHEN** a view é renderizada
- **THEN** o título mostra "<emoji> Gráfico <SYMBOL>USDT"
- **AND** a descrição mostra "Candlestick das últimas 24 horas"
- **AND** a variação 24h é exibida (ex: "+0.32%")
- **AND** o footer mostra "Dados Binance API • Paper Trading Sandbox"

### Requirement: Dados de 24h do ativo

O sistema SHALL exibir métricas de 24h do ativo selecionado.

#### Scenario: Exibição de dados de ticker
- **GIVEN** o estado é ASSET_DETAIL
- **WHEN** a view é renderizada pela primeira vez
- **THEN** o embed é atualizado com dados de 24h do ticker
- **AND** os seguintes campos são exibidos: Preço atual, Variação 24h, Volume, Máxima 24h, Mínima 24h
- **AND** dados são obtidos via `BinancePublicFeed.get_ticker(symbol)`

### Requirement: Menu de negociação

O sistema SHALL exibir botões de negociação no estado ASSET_DETAIL.

#### Scenario: Botões de compra/venda (futuro)
- **GIVEN** o estado é ASSET_DETAIL
- **WHEN** a view é renderizada
- **THEN** botões "Comprar" e "Vender" estão visíveis
- **AND** futuramente conectarão com API de execução de ordens

### Requirement: Navegação de volta

O sistema SHALL permitir múltiplos caminhos de volta ao Dashboard.

#### Scenario: Botão Home
- **GIVEN** o estado é ASSET_DETAIL
- **WHEN** o usuário clica em "🏠 Home"
- **THEN** o estado muda para DASHBOARD
- **AND** `ctx.selected_asset` é resetado para `None`

#### Scenario: Botão Voltar (para Asset List)
- **GIVEN** o estado é ASSET_DETAIL
- **WHEN** o usuário clica em "⬅️ Voltar"
- **THEN** o estado muda para ASSET_LIST
- **AND** `ctx.selected_asset` é mantido (o usuário pode querer ver detalhes de outro ativo)

### Requirement: Atualização dinâmica do gráfico

O sistema SHALL gerar novo gráfico quando solicitado, sem criar novas mensagens.

#### Scenario: Re-clique no botão de gráfico
- **GIVEN** o gráfico já foi exibido
- **WHEN** o usuário clica novamente em "📈 Gráfico <ATIVO>"
- **THEN** `interaction.response.defer()` é chamado
- **THEN** novos dados de klines são buscados da Binance
- **AND** um novo gráfico é gerado
- **AND** `interaction.followup.send()` é usado para enviar o novo gráfico
- **AND** uma nova mensagem é criada no canal (apenas para o gráfico)
