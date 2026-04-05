## Context

O AutoKarpa Fase 1 implementou as entidades de domínio (Experiment, Agent, Metrics, Program, Repository) mas sem camada de aplicação ou infraestrutura. Esta change adiciona essas camadas para tornar o Auto Research funcional, especificamente para validação de specs.

**Estado atual:**
- Domínio completo em `src/core/autokarpa/domain/`
- Nenhum serviço orquestrador
- Nenhum executor de código
- Nenhum wrapper para LLM

**Contexto da Skybridge:**
- Python 3.11+, dataclasses, pytest
- Specs em Markdown em `openspec/specs/` e `docs/spec/`
- Código em `src/core/` (discord, paper, sky, etc.)

**Stakeholders:**
- Desenvolvedores que mantêm código com specs
- QA que valida comportamento documentado
- Documentação que precisa refletir realidade

## Goals / Non-Goals

**Goals:**
- Implementar serviço que orquestra loop de Auto Research para validação de specs
- Criar componentes de infra para ler specs, gerar/executar testes e chamar LLM
- Integrar com Claude API como motor de geração de código/testes
- Executar experimentos em subprocess isolado (segurança)
- Garantir 100% cobertura dos novos componentes

**Non-Goals:**
- Interface com Discord/Kanban (Fase 4)
- Execução real de experimentos em código de produção (Fase 3 é sandbox seguro)
- Suporte a specs em formato diferente de Markdown
- Paralelização de experimentos (futuro)

## Decisions

### D1: Claude API via SDK oficial
**Escolha:** `anthropic` SDK Python
**Por que:** Suporte nativo a streaming, type hints, mantido pela Anthropic. Alternativas seriam HTTP direto (mais trabalho) ou OpenAI (não é o modelo que queremos).

**Alternativa considerada:** HTTP + requests — reinventaria a roda.

### D2: Spec Parser via Regex (não LLM)
**Escolha:** Regex para extrair `### Requirement:` e `#### Scenario:`
**Por que:** Extração estruturada é determinística e barata. LLM seria overkill e mais lento.

**Alternativa considerada:** LLM para parser — adicionaria latência e custo sem benefício.

### D3: Testes gerados em arquivo temporário
**Escolha:** Cada experimento gera um arquivo `test_spec_<id>.py` em `/tmp/`
**Por que:** Isolamento total — testes não poluem o repo, são descartáveis após medição.

**Alternativa considerada:** Gerar testes permanentes — criaria ruído, testes podem não ser bons.

### D4: Subprocess para execução de teste
**Escolha:** `subprocess.run(["pytest", tmpfile, "--tb=short"])`
**Por que:** Simples, padronizado, captura stdout/stderr para análise.

**Alternativa considerada:** `pytest.main()` inline — quebraria isolamento, hard to mock.

### D5: Solução LLM aplicada via git apply (não edição direta)
**Escolha:** LLM gera patch (unified diff), `git apply` aplica
**Por que:** Segurança — patches podem ser revertidos, revistos antes de commit.

**Alternativa considerada:** Edição direta de arquivo — mais complexo, perigoso.

## Risks / Trade-offs

- **Risco:** LLM pode gerar teste incorreto (falso-positivo/negativo) → **Mitigação:** Teste gerado é descartável, não commitado. Apenas correções **aprovadas** via commit humano são permanentes.
- **Risco:** LLM pode gerar código que não compila → **Mitigação:** Validação sintática (AST parse) antes de aplicar patch.
- **Risco:** Subprocess pytest pode travar → **Mitigação:** Timeout em cada execução (ex: 30s).
- **Risco:** Custo Claude API em 100+ ciclos → **Mitigação:** Começar com 5-10 ciclos manuais para validação, depois escalar.
- **Trade-off:** Validação 100% automatizada vs responsabilidade humana → Aceitável porque humano aprova cada commit.

## Open Questions

- **Q1:** Qual spec usar como primeiro alvo? → Escolher após design: sky/chat é bom candidato (documentado, bugs conhecidos).
- **Q2:** Como medir "spec satisfeita" se teste é falso-positivo? → Resposta: Testes gerados são descartáveis, validação humana final nos patches.
- **Q3:** Limite de ciclos por execução? → Decidir após MVP: começar com 10, aumentar para 100 se estável.
