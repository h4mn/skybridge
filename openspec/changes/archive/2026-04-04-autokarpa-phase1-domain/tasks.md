## 1. Value Objects — Metrics

- [x] 1.1 Escrever testes para Metrics (criação, lower/higher_is_better, is_improvement, imutabilidade)
- [x] 1.2 Implementar Metrics como dataclass frozen com comparador e threshold

## 2. Value Objects — Program

- [x] 2.1 Escrever testes para Program (criação, validação instruções não vazias, métrica obrigatória, imutabilidade)
- [x] 2.2 Implementar Program como dataclass frozen com instruções, restrições e métrica

## 3. Entidade — Experiment

- [x] 3.1 Escrever testes para Experiment (criação no estado proposed, transições de estado válidas, transições inválidas, campos obrigatórios, referência ao anterior)
- [x] 3.2 Implementar Experiment como dataclass com Enum de status e métodos de transição de estado

## 4. Entidade — AutoResearchAgent

- [x] 4.1 Escrever testes para AutoResearchAgent (criação idle, transição running/stopped, histórico, melhor score, contadores)
- [x] 4.2 Implementar AutoResearchAgent como dataclass com Enum de estado e métodos de gestão

## 5. Interface — ExperimentRepository

- [x] 5.1 Escrever testes para o Protocol ExperimentRepository (contrato de interface)
- [x] 5.2 Implementar ExperimentRepository como Protocol com metodos save, find_by_id, find_by_status

## 6. Integração e Exports

- [x] 6.1 Atualizar `__init__.py` do domínio com exports públicos
- [x] 6.2 Rodar suite completa de testes e validar 100% de cobertura no módulo autokarpa
