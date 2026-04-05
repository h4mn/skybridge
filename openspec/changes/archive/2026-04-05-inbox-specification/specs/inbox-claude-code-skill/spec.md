# Spec: Inbox Claude Code Skill

## ADDED Requirements

### Requirement: Capturar ideia via comando no Claude Code

O sistema SHALL capturar uma ideia através do comando `/inbox add <título>` no Claude Code.

#### Scenario: Captura bem-sucedida

- **WHEN** usuário executa `/inbox add Adicionar suporte a Webhook no Paper Trading`
- **THEN** sistema cria uma issue no projeto "Inbox" do Linear via Linear MCP
- **AND** issue title é "Adicionar suporte a Webhook no Paper Trading"
- **AND** issue status é "Inbox Entry"
- **AND** issue contém descrição estruturada com campos Fonte, Inspiração, Ação sugerida, Expires

#### Scenario: Captura sem título nem descrição

- **WHEN** usuário executa `/inbox add` sem fornecer título nem descrição
- **THEN** sistema retorna mensagem de erro solicitando pelo menos título ou descrição
- **AND** nenhuma issue é criada

#### Scenario: Captura com título muito longo

- **WHEN** usuário executa `/inbox add` com título maior que 200 caracteres
- **THEN** sistema trunca título para 200 caracteres
- **AND** cria issue com título truncado
- **AND** título completo é preservado no corpo da descrição

#### Scenario: Captura apenas com descrição (sem título)

- **WHEN** usuário executa `/inbox add description:"Texto longo da ideia..."`
- **THEN** sistema cria issue com título gerado das primeiras 5 palavras da descrição
- **AND** descrição completa fornecida é incluída no corpo da issue
- **AND** campos estruturados são adicionados após a descrição do usuário

#### Scenario: Captura com título e descrição

- **WHEN** usuário executa `/inbox add Título description:"Contexto adicional..."`
- **THEN** sistema cria issue com título fornecido
- **AND** descrição do usuário aparece antes dos campos estruturados
- **AND** campos estruturados (Fonte, Ação, Expires) são mantidos

### Requirement: Preencher metadados automaticamente

O sistema SHALL preencher metadados da issue automaticamente baseado no contexto do Claude Code.

#### Scenario: Labels automáticas

- **WHEN** usuário executa `/inbox add` no Claude Code
- **THEN** sistema adiciona label `fonte:claude-code` à issue
- **AND** sistema adiciona label `ação:implementar` à issue

#### Scenario: Domínio padrão

- **WHEN** usuário executa `/inbox add` sem contexto específico
- **THEN** sistema adiciona label `domínio:geral` à issue

#### Scenario: Data de expiração

- **WHEN** usuário executa `/inbox add`
- **THEN** sistema calcula data de expires como hoje + 60 dias
- **AND** insere campo `**Expires:** YYYY-MM-DD (60 dias)` na descrição

### Requirement: Descrição estruturada padrão

O sistema SHALL criar descrição da issue seguindo template estruturado em Markdown.

#### Scenario: Template mínimo

- **WHEN** usuário executa `/inbox add Título da ideia`
- **THEN** descrição da issue contém:

```markdown
**Fonte:** Claude Code

---

**Ação sugerida:** Implementar | Pesquisar | Arquivar | Descartar
**Expires:** <data-60-dias> (60 dias)
```

### Requirement: Feedback de criação

O sistema SHALL fornecer feedback ao usuário após criação da issue.

#### Scenario: Issue criada com sucesso

- **WHEN** issue é criada com sucesso no Linear
- **THEN** sistema responde no Claude Code com link para a issue
- **AND** resposta contém título da issue
- **AND** resposta contém emoji de confirmação (✅)

#### Scenario: Erro na criação

- **WHEN** ocorre erro ao criar issue no Linear
- **THEN** sistema responde no Claude Code com mensagem de erro
- **AND** mensagem sugere tentar novamente
- **AND** detalhes do erro são logados
