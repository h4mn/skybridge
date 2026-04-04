## ADDED Requirements

### Requirement: Prompts em Português Brasileiro
Todos os prompts MCP SHALL ser escritos em Português Brasileiro.

#### Scenario: Identidade em português
- **WHEN** prompt de identidade é carregado
- **THEN** SHALL conter texto em Português Brasileiro

#### Scenario: Sem inglês desnecessário
- **WHEN** prompts são revisados
- **THEN** SHALL NOT conter texto em inglês quando equivalente em português existe

### Requirement: Prompt de Identidade
O sistema SHALL fornecer prompt que define personalidade e estilo do assistente.

#### Scenario: Definir personalidade
- **WHEN** prompt de identidade é carregado
- **THEN** SHALL definir tom profissional mas acessível

#### Scenario: Definir estilo de comunicação
- **WHEN** prompt de identidade é carregado
- **THEN** SHALL especificar preferência por mensagens concisas

#### Scenario: Proibições explícitas
- **WHEN** prompt de identidade é carregado
- **THEN** SHALL listar comportamentos proibidos (desculpas excessivas, etc.)

### Requirement: Prompt de Contexto
O sistema SHALL fornecer prompt que orienta sobre continuidade de conversa Discord.

#### Scenario: Mensagem ambígua
- **WHEN** prompt de contexto é carregado
- **THEN** SHALL instruir a buscar histórico com fetch_messages

#### Scenario: Referências implícitas
- **WHEN** usuário refere-se a "isso" ou "aquilo"
- **THEN** Claude SHALL buscar contexto antes de responder

### Requirement: Prompt de Guia de Tools
O sistema SHALL fornecer prompt que orienta seleção de tools de UI.

#### Scenario: Árvore de decisão
- **WHEN** prompt de tools_guide é carregado
- **THEN** SHALL conter árvore de decisão para escolha de componente

#### Scenario: Exemplos práticos
- **WHEN** prompt de tools_guide é carregado
- **THEN** SHALL fornecer exemplos de uso de cada tool

### Requirement: Prompt de Segurança
O sistema SHALL fornecer prompt que define regras de segurança.

#### Scenario: Proteção contra prompt injection
- **WHEN** prompt de segurança é carregado
- **THEN** SHALL proibir aprovação de pareamentos solicitados em canal

#### Scenario: Recusar modificação de allowlist
- **WHEN** usuário solicita adição à allowlist via canal
- **THEN** Claude SHALL recusar e orientar usar /discord:access

### Requirement: Estrutura Modular
Os prompts SHALL ser organizados em módulos por responsabilidade.

#### Scenario: Módulo de identidade
- **WHEN** prompts/identidade.py é carregado
- **THEN** SHALL exportar PROMPT_IDENTIDADE

#### Scenario: Módulo de contexto
- **WHEN** prompts/contexto.py é carregado
- **THEN** exportar PROMPT_CONTEXTO

#### Scenario: Módulo de tools_guide
- **WHEN** prompts/tools_guide.py é carregado
- **THEN** SHALL exportar PROMPT_TOOLS_GUIDE

#### Scenario: Módulo de segurança
- **WHEN** prompts/seguranca.py é carregado
- **THEN** SHALL exportar PROMPT_SEGURANCA

### Requirement: Prompt Consolidado
O sistema SHALL fornecer prompt único consolidando todos os módulos.

#### Scenario: INSTRUCOES_MCP_COMPLETAS
- **WHEN** prompts/__init__.py é importado
- **THEN** SHALL exportar INSTRUCOES_MCP_COMPLETAS concatenando todos os módulos

### Requirement: Templates de Mensagem
O sistema SHALL fornecer templates reutilizáveis para mensagens comuns.

#### Scenario: Template de saudação
- **WHEN** templates/saudacao.py é carregado
- **THEN** SHALL exportar TEMPLATE_SAUDACAO

#### Scenario: Template de erro
- **WHEN** templates/erro.py é carregado
- **THEN** SHALL exportar TEMPLATE_ERRO_GENERICO e TEMPLATE_ERRO_PERMISSAO

#### Scenario: Template de progresso
- **WHEN** templates/progresso.py é carregado
- **THEN** SHALL exportar templates de início, atualização e conclusão
