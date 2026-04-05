## Why

Existe um gap entre especificações, código e testes: mesmo com docs e testes, funcionalidades não comportam conforme especificado. O Spec Validator resolve isso automaticamente validando se o código implementa as specs através de testes gerados, propondo correções quando falha.

## What Changes

- Adiciona camada **application** ao AutoKarpa com serviço de validação de specs
- Adiciona camada **infrastructure** com 4 novos componentes:
  - `spec_parser.py`: extrai requisitos de arquivos Markdown
  - `test_generator.py`: usa LLM para gerar testes a partir de specs
  - `test_runner.py`: executa pytest em subprocess isolado
  - `llm_client.py`: wrapper para Claude API
- Estende entidades de domínio com `SpecExperiment` e `SpecRequirement`
- Cria `program.md` definindo o loop Auto Research para validação de specs

## Capabilities

### New Capabilities
- `spec-parser`: Extração estruturada de requisitos (Requirement + Scenario) de arquivos Markdown/Spec
- `test-generator`: Geração automática de testes pytest a partir de specs usando LLM
- `test-runner`: Execução isolada de testes e captura de resultados (pass/fail)
- `solution-generator`: Proposição de correções de código via LLM quando testes falham
- `spec-experiment`: Experimento que valida se um requisito de spec está satisfeito

### Modified Capabilities
Nenhuma — são capabilities novas para AutoKarpa.

## Impact

- **Código**: `src/core/autokarpa/application/` e `src/core/autokarpa/infrastructure/` — novos módulos
- **Dependências**: Claude SDK (anthropic), subprocess (já stdlib), pytest (já instalado)
- **Testes**: `tests/unit/core/autokarpa/application/` e `infrastructure/` — testes para nova camada
- **Sistemas**: Nenhum sistema existente afetado (bounded context isolado)

> "Spec sem teste é promessa sem prova." – made by Sky 🌵
