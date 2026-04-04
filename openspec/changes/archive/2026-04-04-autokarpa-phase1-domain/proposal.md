## Why

O AutoKarpa precisa de entidades de domínio fundamentais para implementar o padrão **Auto Research** de Andrej Karpathy. Atualmente o bounded context `src/core/autokarpa/` contém apenas documentação e `__init__.py` vazio — sem código de produção. A Fase 1 do checklist define as entidades core (`Experiment`, `AutoResearchAgent`, `Metrics`, `Program`) que formarão a base do loop automatizado de experimentação.

## What Changes

- Criar entidade `Experiment` — representa um ciclo individual do loop Auto Research (código proposto, score, status, timestamp)
- Criar entidade `AutoResearchAgent` — orquestra o estado do agente (histórico de experimentos, regras de iteração)
- Criar modelo de `Metrics` — define score único, comparador e threshold de melhoria
- Criar modelo de `Program` — representa as instruções (`program.md`) como objeto de domínio
- Criar interfaces de repositório para persistência de experimentos
- Escrever testes unitários para cada entidade (TDD estrito)

## Capabilities

### New Capabilities
- `autokarpa-experiment`: Entidade Experiment com ciclo de vida (proposed → running → completed/failed)
- `autokarpa-agent`: Entidade AutoResearchAgent com estado e histórico de experimentos
- `autokarpa-metrics`: Definição de métricas — score único, comparador, threshold de melhora
- `autokarpa-program`: Representação de program.md como objeto de domínio com instruções e restrições

### Modified Capabilities
<!-- Nenhuma capability existente é modificada — é código novo -->

## Impact

- **Código**: `src/core/autokarpa/domain/` — novas entidades e testes
- **Dependências**: Nenhuma dependência externa nova (dataclasses/attrs, pytest)
- **Testes**: `tests/unit/core/autokarpa/` — testes unitários para cada entidade
- **Sistemas**: Nenhum sistema existente é afetado (bounded context isolado)
