# discord-paper-integration Specification

## Purpose
TBD - created by archiving change discord-ddd-migration. Update Purpose after archive.
## Requirements
### Requirement: Camada de Integração Separada
O sistema SHALL manter Integration Layer em `src/core/integrations/discord_paper/` separada dos módulos Paper e Discord.

#### Scenario: Paper não conhece Discord
- **WHEN** verificado imports de src/core/paper/
- **THEN** SHALL NOT conter imports de src/core/discord/

#### Scenario: Discord não conhece Paper
- **WHEN** verificado imports de src/core/discord/
- **THEN** SHALL NOT conter imports de src/core/paper/

### Requirement: Projections para Transformação
O sistema SHALL fornecer Projections que transformam entidades Paper em Value Objects Discord.

#### Scenario: PortfolioEmbedProjection
- **WHEN** PortfolioEmbedProjection.from_portfolio(portfolio) é chamado
- **THEN** SHALL retornar projeção com titulo, descricao, cor, campos e rodape

#### Scenario: Cor baseada em PnL
- **WHEN** portfolio.pnl >= 0
- **THEN** projection.cor SHALL ser "verde"

#### Scenario: Cor vermelha para prejuízo
- **WHEN** portfolio.pnl < 0
- **THEN** projection.cor SHALL ser "vermelho"

### Requirement: OrdemButtonsProjection
O sistema SHALL fornecer projeção de ordens para botões de confirmação.

#### Scenario: Criar botões de confirmação
- **WHEN** OrdemButtonsProjection.from_ordem_intent(ticker, lado, quantidade, preco) é chamado
- **THEN** SHALL retornar projeção com botões "Confirmar" e "Cancelar"

#### Scenario: Texto com valor total
- **WHEN** projeção é criada
- **THEN** texto SHALL incluir cálculo de valor total (quantidade * preco)

### Requirement: Handlers de Integração
O sistema SHALL fornecer Handlers que orquestram fluxos Paper → Discord.

#### Scenario: PortfolioUIHandler.handle_consultar_portfolio()
- **WHEN** handle_consultar_portfolio(chat_id) é chamado
- **THEN** SHALL consultar Paper, criar projeção, enviar via Discord

#### Scenario: OrdemUIHandler.iniciar_fluxo_ordem()
- **WHEN** iniciar_fluxo_ordem(chat_id, ticker, lado, quantidade) é chamado
- **THEN** SHALL consultar cotação, enviar botões de confirmação

#### Scenario: OrdemUIHandler.processar_confirmacao()
- **WHEN** processar_confirmacao(interaction_id, True) é chamado
- **THEN** SHALL executar ordem no Paper e atualizar UI

### Requirement: Estado de Interação
O sistema SHALL manter estado de interações pendentes.

#### Scenario: Salvar estado pendente
- **WHEN** fluxo de ordem é iniciado
- **THEN** estado SHALL ser salvo em InteractionStateRepository

#### Scenario: Recuperar estado
- **WHEN** confirmação é recebida
- **THEN** estado SHALL ser recuperado por interaction_id

### Requirement: Regras de Dependência da Integration
A Integration Layer SHALL depender de Paper (Facade) e Discord (Application).

#### Scenario: Integration importa Paper Facade
- **WHEN** verificado imports de integrations/discord_paper/
- **THEN** MAY conter imports de src/core/paper/facade/

#### Scenario: Integration importa Discord Application
- **WHEN** verificado imports de integrations/discord_paper/
- **THEN** MAY conter imports de src/core/discord/application/

#### Scenario: Integration não importa Infrastructure
- **WHEN** verificado imports de integrations/discord_paper/
- **THEN** SHALL NOT conter imports de infrastructure de Paper ou Discord

