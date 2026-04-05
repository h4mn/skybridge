# discord-infrastructure Specification

## Purpose
TBD - created by archiving change discord-ddd-migration. Update Purpose after archive.
## Requirements
### Requirement: DiscordAdapter
O sistema SHALL implementar DiscordAdapter que encapsula discord.py.

#### Scenario: Enviar mensagem via adapter
- **WHEN** adapter.send_message(channel_id, content) é chamado
- **THEN** SHALL usar discord.py client para enviar mensagem

#### Scenario: Buscar histórico via adapter
- **WHEN** adapter.fetch_messages(channel_id, limit) é chamado
- **THEN** SHALL retornar lista de mensagens do Discord API

#### Scenario: Tratar erros do Discord API
- **WHEN** discord.py lança exceção
- **THEN** adapter SHALL converter para DomainException apropriada

### Requirement: MCPAdapter
O sistema SHALL implementar MCPAdapter que configura o MCP Server.

#### Scenario: Criar MCP Server
- **WHEN** create_mcp_server() é chamado
- **THEN** SHALL retornar instância de Server configurada com tools e prompts

#### Scenario: Registrar tools MCP
- **WHEN** MCP Server é configurado
- **THEN** SHALL registrar todas as tools de presentation/tools/

#### Scenario: Configurar prompts
- **WHEN** MCP Server é criado
- **THEN** SHALL usar INSTRUCOES_MCP_COMPLETAS como instructions

### Requirement: AccessRepository JSON Implementation
O sistema SHALL implementar AccessRepository usando arquivo JSON.

#### Scenario: Carregar access.json
- **WHEN** AccessRepository é instanciado
- **THEN** SHALL carregar configurações de access.json

#### Scenario: Verificar canal autorizado
- **WHEN** is_authorized(channel_id) é chamado
- **THEN** SHALL verificar se canal está na lista de canais autorizados

#### Scenario: Persistir alterações
- **WHEN** save() é chamado
- **THEN** SHALL escrever alterações no arquivo JSON

### Requirement: Repository Implementations
O sistema SHALL implementar interfaces de repositório definidas no Domain.

#### Scenario: MessageRepositoryImpl
- **WHEN** MessageRepositoryImpl é instanciado
- **THEN** SHALL usar DiscordAdapter para buscar mensagens

### Requirement: Regras de Dependência da Infrastructure
A Infrastructure Layer SHALL depender de Domain e Application.

#### Scenario: Infrastructure importa Domain
- **WHEN** verificado imports de infrastructure/
- **THEN** MAY conter imports de domain/

#### Scenario: Infrastructure importa Application
- **WHEN** verificado imports de infrastructure/
- **THEN** MAY conter imports de application/

#### Scenario: Infrastructure não importa Presentation
- **WHEN** verificado imports de infrastructure/
- **THEN** SHALL NOT conter imports de presentation/

