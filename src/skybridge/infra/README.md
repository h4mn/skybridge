# Infra — Implementações Concretas

## O que é

A **Infra** contém todas as implementações concretas dos ports definidos nos contexts e integrations externas.

## Estrutura

### `contexts/`
Implementações de ports por Bounded Context:
- `fileops/` — FileSystemPort, SecurityPolicyPort, AuditLogPort, SecretScannerPort
- `tasks/` — EventStorePort, ProjectionPort, TaskRepositoryPort

### `persistence/`
Implementações de persistência:
- Event store em JSON
- Repositórios de leitura (projections)
- Filesystem storage

### `integrations/`
Adapters para serviços externos:
- Discord (bot, webhooks)
- GitHub (commits, issues, PRs)
- Trello (cards, lists, boards)
- Spotify (contexto musical)
- VS Code (editor automation)
- DALL-E 3 (image generation)
- MCP (Model Context Protocol)

## Contratos e Testes

Cada implementação deve:
- Declarar explicitamente qual port implementa
- Seguir contrato definido no context
- Ter contract tests quando crítico

## Regras

- Domain nunca importa Infra (regra da Hexagonal)
- Application depende de ports (interfaces), não de implementações
- Integrations são opcionais e podem ser removidas

---

> "Infra é pluggable, domínio é eterno." – made by Sky ✨
