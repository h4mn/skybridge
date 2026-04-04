## ADDED Requirements

### Requirement: Command Pattern para Operações de Escrita
O sistema SHALL definir Commands para todas as operações que modificam estado.

#### Scenario: SendMessageCommand
- **WHEN** uma mensagem precisa ser enviada
- **THEN** SendMessageCommand SHALL conter channel_id, content, reply_to e files

#### Scenario: SendEmbedCommand
- **WHEN** um embed precisa ser enviado
- **THEN** SendEmbedCommand SHALL conter channel_id e embed_data

#### Scenario: SendButtonsCommand
- **WHEN** botões interativos precisam ser enviados
- **THEN** SendButtonsCommand SHALL conter channel_id, texto e lista de buttons

#### Scenario: ReactCommand
- **WHEN** uma reação precisa ser adicionada
- **THEN** ReactCommand SHALL conter channel_id, message_id e emoji

### Requirement: Query Pattern para Operações de Leitura
O sistema SHALL definir Queries para todas as operações de leitura.

#### Scenario: FetchMessagesQuery
- **WHEN** histórico de mensagens é solicitado
- **THEN** FetchMessagesQuery SHALL conter channel_id e limit opcional

#### Scenario: ListThreadsQuery
- **WHEN** threads de um canal são listadas
- **THEN** ListThreadsQuery SHALL conter channel_id e include_archived opcional

### Requirement: Command Handlers
O sistema SHALL implementar Handlers que processam Commands.

#### Scenario: SendMessageHandler executa comando
- **WHEN** SendMessageHandler.handle(command) é chamado
- **THEN** SHALL validar acesso, criar Message, salvar e publicar MessageSentEvent

#### Scenario: Handler valida permissões
- **WHEN** command é recebido
- **THEN** handler SHALL verificar se canal está autorizado via ChannelRepository

### Requirement: Query Handlers
O sistema SHALL implementar Handlers que processam Queries.

#### Scenario: FetchMessagesHandler retorna DTO
- **WHEN** FetchMessagesHandler.handle(query) é chamado
- **THEN** SHALL retornar lista de MessageDTO

### Requirement: DiscordService Application Service
O sistema SHALL fornecer DiscordService como fachada para operações Discord.

#### Scenario: Injeção de dependências
- **WHEN** DiscordService é instanciado
- **THEN** SHALL receber MessageRepository, ChannelRepository, AccessService e EventPublisher

#### Scenario: send_message orquestra fluxo
- **WHEN** discord_service.send_message(command) é chamado
- **THEN** SHALL orquestrar validação, criação, persistência e publicação de evento

### Requirement: Regras de Dependência da Application
A Application Layer SHALL depender apenas de Domain.

#### Scenario: Application importa Domain
- **WHEN** verificado imports de application/
- **THEN** MAY conter imports de domain/

#### Scenario: Application não importa Infrastructure
- **WHEN** verificado imports de application/
- **THEN** SHALL NOT conter imports de infrastructure/

#### Scenario: Application não importa Presentation
- **WHEN** verificado imports de application/
- **THEN** SHALL NOT conter imports de presentation/
