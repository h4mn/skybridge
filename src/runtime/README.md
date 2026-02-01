# Platform — Host e Runtime do Produto

## O que é

A **Platform** é responsável pelo runtime do produto Skybridge: bootstrap, injeção de dependências, observabilidade, lifecycle de plugins e políticas de segurança em tempo de execução.

## Responsabilidades

### `bootstrap/`
Composição do aplicativo (wire-up), carregamento de configuração e inicialização de todos os componentes.

### `config/`
Carregamento e merge de configurações (base + profiles + context files + env vars).

### `di/`
Container de injeção de dependências (leve, sem framework pesado).

### `observability/`
Correlation IDs, logging estruturado, metrics e tracing.

### `plugin_host/`
Loader, lifecycle e policies de execução de plugins.

### `security/`
Políticas de segurança em runtime: allow/deny, rate-limit, auth middleware.

### `delivery/`
Empacotamento, release e concerns de runtime (versioning, health checks).

## Regras Importantes

- **PROIBIDO** conter regras de negócio de Bounded Contexts (FileOps, Tasks)
- Depende de Core (application layer), mas não de domain diretamente
- Apps e Plugins dependem da Platform para executar

---

> "Platform é o chão que todos pisam, mas ninguém vê." – made by Sky ✨
