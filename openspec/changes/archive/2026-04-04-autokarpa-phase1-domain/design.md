## Context

O AutoKarpa é um bounded context isolado em `src/core/autokarpa/` dentro da Skybridge. Atualmente contém apenas documentação (briefing, checklist, transcrição) e `__init__.py` vazio. O projeto segue DDD com separação domain/application/infrastructure.

O padrão Auto Research (Karpathy) define um loop: IA lê código + instruções → propõe mudança → executa experimento → mede score → salva ou desfaz → repete. Esta change implementa as entidades de domínio que modelam esse loop.

A Skybridge usa Python 3.11+, dataclasses para entidades de domínio, e pytest para testes.

## Goals / Non-Goals

**Goals:**
- Modelar as 4 entidades core do domínio AutoKarpa: Experiment, AutoResearchAgent, Metrics, Program
- Definir o ciclo de vida de um Experiment (proposed → running → completed/failed)
- Criar interface de repositório para persistência de experimentos
- Garantir 100% de cobertura de testes unitários via TDD

**Non-Goals:**
- Implementar camada de application (service) — futuro
- Implementar camada de infrastructure (executor, LLM wrapper) — futuro
- Integrar com EventBus da Skybridge — Fase 4
- Interface com Discord/Kanban — Fase 4
- Execução real de experimentos (sandbox, subprocess) — Fase 2

## Decisions

### D1: dataclasses ao invés de attrs/pydantic
**Escolha:** `@dataclass` nativo do Python
**Por que:** Entidades de domínio não precisam de validação Pydantic (isso é boundary). attrs adicionaria dependência. dataclasses são suficientes para value objects e entidades com comportamento.
**Alternativa considerada:** attrs — mais features mas dependência desnecessária para este caso.

### D2: Enums para status ao invés de strings
**Escolha:** `StrEnum` para `ExperimentStatus` e `AgentState`
**Por que:** Tipagem forte, autodocumentável, impossível ter status inválido. `StrEnum` (3.11+) permite comparação com strings quando necessário.

### D3: Score como float simples
**Escolha:** Score é `float` puro, não um value object
**Por que:** O pattern Auto Research usa uma métrica única e simples. Adicionar complexidade (Score object) seria over-engineering. Se precisar, refatora-se depois.

### D4: Repository como Protocol (interface)
**Escolha:** `typing.Protocol` para `ExperimentRepository`
**Por que:** Define o contrato sem depender de implementação. Segue o padrão da Skybridge (DDD). A implementação concreta (JSON, SQLite) fica na camada de infrastructure.

### D5: Entidades imutáveis por padrão
**Escolha:** `frozen=True` em value objects, entidades mutáveis com métodos de transição de estado
**Por que:** Value objects (Metrics, Program) são imutáveis. Experiment e Agent têm estado que transiciona — usam métodos explícitos (não setters diretos).

## Risks / Trade-offs

- **Risco:** Definir domínio muito cedo pode levar a refatoração quando o loop real rodar → **Mitigação:** Entidades simples e testadas. Refatorar é barato com testes.
- **Risco:** Não ter a camada de application pode dificultar testes de integração → **Mitigação:** Repository como Protocol permite mocks fáceis nos testes unitários.
- **Trade-off:** Score como float perde type-safety vs value object → Aceitável porque o pattern é deliberadamente simples (métrica única).
