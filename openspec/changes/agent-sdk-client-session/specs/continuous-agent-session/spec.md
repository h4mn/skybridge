# Sessão Contínua do Claude Agent SDK

Especificação para sessão contínua do agente com ferramentas habilitadas no Sky Chat.

## ADDED Requirements

### Requirement: Cliente SDK persistente por sessão de chat
O sistema SHALL manter uma única instância do `ClaudeSDKClient` durante toda a sessão de chat, em vez de criar uma nova instância a cada mensagem.

#### Scenario: Primeira mensagem cria cliente SDK
- **WHEN** usuário envia a primeira mensagem da sessão
- **THEN** sistema cria instância do `ClaudeSDKClient`
- **AND** cliente é armazenado em `ClaudeChatAdapter._sdk_client`

#### Scenario: Mensagens subsequentes reutilizam cliente
- **WHEN** usuário envia mensagem após a primeira
- **THEN** sistema reutiliza instância existente do `ClaudeSDKClient`
- **AND** nenhuma nova instância é criada

### Requirement: Ferramentas básicas habilitadas
O sistema SHALL configurar o cliente SDK com `allowed_tools=["Read", "Glob", "Grep"]` para permitir que a Sky descubra informações sobre o projeto.

#### Scenario: Sky pode ler arquivos do projeto
- **WHEN** usuário pergunta "qual o nome deste projeto?"
- **THEN** Sky usa ferramenta `Read` para ler `README.md` ou `pyproject.toml`
- **AND** responde com o nome correto do projeto

#### Scenario: Sky pode buscar arquivos por padrão
- **WHEN** usuário pergunta "quais arquivos Python existem?"
- **THEN** Sky usa ferramenta `Glob` para buscar `**/*.py`
- **AND** lista os arquivos encontrados

#### Scenario: Sky pode pesquisar conteúdo
- **WHEN** usuário pergunta "onde está definida a função X?"
- **THEN** Sky usa ferramenta `Grep` para buscar por "def X"
- **AND** retorna o caminho do arquivo

### Requirement: Multi-turno sem limite
O sistema SHALL configurar `max_turns=None` (ou valor suficientemente alto) para permitir conversas contínuas com múltiplos turnos.

#### Scenario: Conversa com múltiplos turnos
- **WHEN** Sky precisa de mais de um turno para responder
- **THEN** SDK continua processando até conclusão
- **AND** não há limite artificial de `max_turns=1`

### Requirement: Gerenciamento de ciclo de vida da sessão
O sistema SHALL fornecer método `close()` em `ClaudeChatAdapter` para encerrar a sessão SDK adequadamente.

#### Scenario: Encerramento de sessão libera recursos
- **WHEN** sessão de chat é encerrada
- **THEN** método `ClaudeChatAdapter.close()` é chamado
- **AND** cliente SDK é fechado com `__aexit__`
- **AND** recursos são liberados

#### Scenario: Reentrada após close
- **WHEN** `close()` é chamado e nova mensagem é enviada
- **THEN** novo cliente SDK é criado
- **AND** sessão continua normalmente

### Requirement: Compatibilidade com API existente
O sistema SHALL manter a assinatura do método `ClaudeChatAdapter.respond()` inalterada para não quebrar código existente.

#### Scenario: Chamada existente de respond() funciona
- **WHEN** código existente chama `await chat.respond(message)`
- **THEN** método funciona sem alterações
- **AND** retorna resposta como string
