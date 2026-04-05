# discord-domain Specification

## Purpose
TBD - created by archiving change discord-ddd-migration. Update Purpose after archive.
## Requirements
### Requirement: Message Aggregate Root
O sistema SHALL definir Message como Aggregate Root contendo ID, channel_id, author_id, content, timestamp, attachments e reactions.

#### Scenario: Criar mensagem válida
- **WHEN** uma mensagem é criada com dados válidos
- **THEN** a mensagem SHALL conter MessageId, ChannelId, UserId e MessageContent

#### Scenario: Editar mensagem dentro do prazo
- **WHEN** edit() é chamado em mensagem com menos de 24h
- **THEN** o conteúdo SHALL ser atualizado e edited_at SHALL ser definido

#### Scenario: Rejeitar edição de mensagem expirada
- **WHEN** edit() é chamado em mensagem com mais de 24h
- **THEN** o sistema SHALL lançar MessageEditError

### Requirement: Channel Entity
O sistema SHALL definir Channel como Entity com id, type, name e guild_id opcional.

#### Scenario: Identificar canal como DM
- **WHEN** channel.type == ChannelType.DM
- **THEN** is_dm() SHALL retornar True

#### Scenario: Identificar canal como Thread
- **WHEN** channel.type == ChannelType.THREAD
- **THEN** is_thread() SHALL retornar True

### Requirement: MessageContent Value Object
O sistema SHALL definir MessageContent como Value Object com comportamento de chunking.

#### Scenario: Mensagem dentro do limite
- **WHEN** MessageContent tem menos de 2000 caracteres
- **THEN** chunk() SHALL retornar lista com um único elemento

#### Scenario: Mensagem excede limite
- **WHEN** MessageContent tem mais de 2000 caracteres
- **THEN** chunk() SHALL dividir em múltiplos chunks respeitando quebras de parágrafo

#### Scenario: Mensagem excede limite máximo
- **WHEN** MessageContent excede 20000 caracteres
- **THEN** o sistema SHALL lançar MessageTooLongError

### Requirement: AccessPolicy Value Object
O sistema SHALL definir AccessPolicy com dm_policy, allow_from e mention_patterns.

#### Scenario: Política DISABLED bloqueia tudo
- **WHEN** dm_policy == DMPolicy.DISABLED
- **THEN** is_allowed() SHALL retornar False para qualquer usuário

#### Scenario: Política ALLOWLIST verifica lista
- **WHEN** dm_policy == DMPolicy.ALLOWLIST
- **THEN** is_allowed() SHALL retornar True apenas se user_id estiver em allow_from

#### Scenario: Política PAIRING requer pareamento
- **WHEN** dm_policy == DMPolicy.PAIRING
- **THEN** is_allowed() SHALL verificar se user_id foi pareado

### Requirement: Domain Events
O sistema SHALL emitir Domain Events para mudanças de estado significativas.

#### Scenario: Mensagem recebida emite evento
- **WHEN** uma mensagem é recebida do Discord
- **THEN** MessageReceivedEvent SHALL ser publicado

#### Scenario: Mensagem enviada emite evento
- **WHEN** uma mensagem é enviada com sucesso
- **THEN** MessageSentEvent SHALL ser publicado

#### Scenario: Botão clicado emite evento
- **WHEN** usuário clica em botão interativo
- **THEN** ButtonClickedEvent SHALL ser publicado

### Requirement: Repository Interfaces (Ports)
O sistema SHALL definir interfaces de repositório no Domain Layer.

#### Scenario: MessageRepository interface
- **WHEN** MessageRepository é implementado
- **THEN** SHALL fornecer get_by_id(), save() e get_history()

#### Scenario: ChannelRepository interface
- **WHEN** ChannelRepository é implementado
- **THEN** SHALL fornecer get_by_id() e is_authorized()

### Requirement: Regras de Dependência do Domain
O Domain Layer SHALL NOT depender de nenhuma outra camada.

#### Scenario: Domain não importa Application
- **WHEN** verificado imports do domain/
- **THEN** SHALL NOT conter imports de application/

#### Scenario: Domain não importa Infrastructure
- **WHEN** verificado imports do domain/
- **THEN** SHALL NOT conter imports de infrastructure/

#### Scenario: Domain não importa Presentation
- **WHEN** verificado imports do domain/
- **THEN** SHALL NOT conter imports de presentation/

