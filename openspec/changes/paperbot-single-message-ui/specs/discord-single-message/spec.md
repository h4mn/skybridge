# Spec: Discord Single Message

Sistema de UI que mantém apenas 1 mensagem ativa em um tópico do Discord, atualizada dinamicamente via `edit()`.

## ADDED Requirements

### Requirement: Single message per topic

O sistema SHALL manter apenas 1 mensagem ativa no tópico do Discord.

#### Scenario: Criação inicial do painel
- **GIVEN** um usuário envia o comando `!paper` em um canal
- **WHEN** o comando é processado
- **THEN** o bot cria um novo tópico com 1 mensagem inicial
- **AND** o bot edita essa mensagem com `content=None, embed=..., view=...`

#### Scenario: Navegação sem criar novas mensagens
- **GIVEN** um painel está ativo em um tópico
- **WHEN** o usuário clica em um botão de navegação
- **THEN** o bot edita a mesma mensagem com novo conteúdo
- **AND** nenhuma nova mensagem é criada no tópico
- **AND** o número total de mensagens no tópico permanece 1

### Requirement: Conteúdo substituído por edit

O sistema SHALL substituir completamente o conteúdo da mensagem a cada interação.

#### Scenario: Substituição bem-sucedida
- **GIVEN** uma mensagem ativa com embed A
- **WHEN** o bot chama `message.edit(content=None, embed=B, view=v)`
- **THEN** o conteúdo anterior é removido
- **AND** apenas o novo embed B e view v são visíveis

#### Scenario: Compatibilidade discord.py 2.7.1
- **GIVEN** o bot está rodando discord.py versão 2.7.1
- **WHEN** edit é chamado com `content=None`
- **THEN** o conteúdo anterior é limpo corretamente
- **AND** o novo embed aparece sem o texto original

### Requirement: View controla botões visíveis

O sistema SHALL exibir diferentes botões baseado no estado atual da view.

#### Scenario: Botões do Dashboard
- **GIVEN** o estado é DASHBOARD
- **WHEN** a view é renderizada
- **THEN** botões "💰 Ativos" e "📊 Posição" estão visíveis
- **AND** botão "Configuração" é desabilitado (futuro)

#### Scenario: Botões de Asset List
- **GIVEN** o estado é ASSET_LIST
- **WHEN** a view é renderizada
- **THEN** botões "🏠 Home" e botões para cada ativo (BTC, ETH, etc) estão visíveis
