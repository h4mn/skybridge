## ADDED Requirements

### Requirement: MCP Tool reply
O sistema SHALL fornecer tool MCP `reply` para enviar mensagens de texto.

#### Scenario: Enviar resposta simples
- **WHEN** reply(chat_id, text) é chamado
- **THEN** SHALL enviar mensagem de texto para o canal

#### Scenario: Responder com quote
- **WHEN** reply(chat_id, text, reply_to=message_id) é chamado
- **THEN** SHALL enviar mensagem citando a mensagem original

#### Scenario: Enviar com anexos
- **WHEN** reply(chat_id, text, files=[path1, path2]) é chamado
- **THEN** SHALL enviar mensagem com arquivos anexados

### Requirement: MCP Tool send_embed
O sistema SHALL fornecer tool MCP `send_embed` para enviar mensagens formatadas.

#### Scenario: Enviar embed básico
- **WHEN** send_embed(chat_id, title, description) é chamado
- **THEN** SHALL enviar Discord Embed com título e descrição

#### Scenario: Enviar embed com campos
- **WHEN** send_embed com fields=[{nome, valor}] é chamado
- **THEN** SHALL enviar Embed com campos estruturados

#### Scenario: Escolher cor do embed
- **WHEN** send_embed com color="verde" é chamado
- **THEN** SHALL enviar Embed com cor verde

### Requirement: MCP Tool send_progress
O sistema SHALL fornecer tool MCP `send_progress` para indicar progresso.

#### Scenario: Progresso indeterminado
- **WHEN** send_progress(chat_id, status="executando", mensagem="...") é chamado
- **THEN** SHALL enviar indicador de progresso sem percentual

#### Scenario: Progresso com percentual
- **WHEN** send_progress(chat_id, progresso_percentual=50) é chamado
- **THEN** SHALL enviar indicador visual com 50%

#### Scenario: Progresso concluído
- **WHEN** send_progress(chat_id, status="sucesso") é chamado
- **THEN** SHALL enviar indicador de sucesso

### Requirement: MCP Tool send_buttons
O sistema SHALL fornecer tool MCP `send_buttons` para botões interativos.

#### Scenario: Enviar botões de confirmação
- **WHEN** send_buttons(chat_id, texto, botoes=[{id, label}]) é chamado
- **THEN** SHALL enviar mensagem com botões clicáveis

#### Scenario: Limitar quantidade de botões
- **WHEN** send_buttons com mais de 5 botões é chamado
- **THEN** SHALL retornar erro de validação

#### Scenario: Processar clique de botão
- **WHEN** usuário clica em botão
- **THEN** sistema SHALL gerar notificação inbound com component_id

### Requirement: MCP Tool send_menu
O sistema SHALL fornecer tool MCP `send_menu` para menus dropdown.

#### Scenario: Enviar menu de seleção
- **WHEN** send_menu(chat_id, texto, opcoes=[...]) é chamado
- **THEN** SHALL enviar dropdown com opções

#### Scenario: Seleção múltipla
- **WHEN** send_menu com multipla_selecao=true é chamado
- **THEN** SHALL permitir selecionar múltiplas opções

### Requirement: MCP Tool update_component
O sistema SHALL fornecer tool MCP `update_component` para atualizar componentes.

#### Scenario: Atualizar progresso
- **WHEN** update_component(chat_id, message_id, progress={...}) é chamado
- **THEN** SHALL atualizar componente existente

#### Scenario: Desabilitar botões
- **WHEN** update_component com desabilitar_botoes=true é chamado
- **THEN** SHALL desabilitar todos os botões da mensagem

### Requirement: DTOs para Tools
O sistema SHALL definir DTOs Pydantic para entrada de cada tool.

#### Scenario: Validação de entrada
- **WHEN** tool é chamada com dados inválidos
- **THEN** SHALL retornar erro de validação Pydantic

### Requirement: Regras de Dependência da Presentation
A Presentation Layer SHALL depender de Application.

#### Scenario: Presentation importa Application
- **WHEN** verificado imports de presentation/
- **THEN** MAY conter imports de application/

#### Scenario: Presentation não importa Infrastructure
- **WHEN** verificado imports de presentation/
- **THEN** SHALL NOT conter imports de infrastructure/

#### Scenario: Presentation não importa Domain diretamente
- **WHEN** verificado imports de presentation/
- **THEN** SHALL NOT conter imports diretos de domain/ (usar via Application)
