## 1. Infrastructure - Spec Parser

- [x] 1.1 Escrever testes para SpecParser (leitura markdown, extração requirement/scenario, identificação função alvo)
- [x] 1.2 Implementar SpecParser com regex para extrair `### Requirement:` e `#### Scenario:`
- [x] 1.3 Adicionar scan recursivo de diretório e filtro de arquivos `.md`

## 2. Infrastructure - LLM Client

- [x] 2.1 Escrever testes para LLMClient (inicialização, método chat, tratamento de erro)
- [x] 2.2 Implementar LLMClient usando `anthropic` SDK
- [x] 2.3 Adicionar configuração de API key via environment variable

## 3. Infrastructure - Test Generator

- [x] 3.1 Escrever testes para TestGenerator (geração de teste a partir de SpecRequirement)
- [x] 3.2 Implementar TestGenerator com prompt template (spec + código → teste pytest)
- [x] 3.3 Adicionar validação de retorno (código Python válido)

## 4. Infrastructure - Test Runner

- [x] 4.1 Escrever testes para TestRunner (escrita arquivo temp, execução subprocess, captura output, timeout)
- [x] 4.2 Implementar TestRunner usando `subprocess.run` com `pytest`
- [x] 4.3 Adicionar timeout de 30s e captura de stdout/stderr

## 5. Infrastructure - Solution Generator

- [x] 5.1 Escrever testes para SolutionGenerator (proposta de correção a partir de falha)
- [x] 5.2 Implementar SolutionGenerator com prompt (erro + código + spec → correção)
- [x] 5.3 Adicionar validação de sintaxe (AST parse) do código proposto

## 6. Application - Spec Validator Service

- [x] 6.1 Escrever testes para SpecValidatorService (orquestra loop: parser → gen → run → fix)
- [x] 6.2 Implementar SpecValidatorService integrando todos os componentes de infrastructure
- [x] 6.3 Adicionar método `run_validation_cycle()` que executa um ciclo completo

## 7. Domain - SpecRequirement

- [x] 7.1 Escrever testes para SpecRequirement (campos obrigatórios, imutabilidade)
- [x] 7.2 Implementar SpecRequirement como dataclass frozen com source_file, requirement_id, description, scenario, target_function

## 8. Domain - SpecExperiment

- [x] 8.1 Escrever testes para SpecExperiment (herda Experiment, campos spec_requirement, generated_test, test_passed, proposed_solution)
- [x] 8.2 Implementar SpecExperiment estendendo Experiment com campos específicos de validação de spec

## 9. Integration - Program.md

- [x] 9.1 Criar `program.md` definindo objetivo (validar specs), métrica (% specs satisfeitas), alvo (domínio Sky), critério de parada (N ciclos ou 100% specs)
- [x] 9.2 Adicionar instruções de restrições (não modificar código de produção, sandbox, aprovação humana)

## 10. Integration - Testes End-to-End

- [x] 10.1 Escrever teste E2E simulando ciclo completo: spec → parser → teste gen → execução → correção
- [x] 10.2 Criar spec de exemplo para teste (simples, com bug conhecido)
- [x] 10.3 Validar que Service orquestra todos os componentes e produz SpecExperiment com score

## 11. Export e Limpeza

- [x] 11.1 Atualizar `__init__.py` do domínio com exports de SpecRequirement e SpecExperiment
- [x] 11.2 Rodar suite completa de testes e validar 100% cobertura nos novos módulos

---

## Status Final

**Data:** 2026-04-04
**Progresso:** 29/29 tarefas (100%)
**Testes:** 124/124 passing
**Cobertura:** 100%
**E2E:** 4/4 passing

> "Spec sem teste é promessa sem prova." – made by Sky 🌵
