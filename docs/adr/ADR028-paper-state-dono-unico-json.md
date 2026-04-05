---
status: aceito
data: 2026-03-27
data_implementacao: 2026-03-27
contexto: src/core/paper
---

# ADR028 — PaperState como dono único do paper_state.json

## Status
Aceito

## Contexto

Durante o desenvolvimento do playground helloworld, dois adapters foram
implementados com o mesmo `DEFAULT_FILE = "paper_state.json"`:

- `JsonFilePaperBroker` — persiste saldo, ordens e posições
- `JsonFilePortfolioRepository` — persiste entidades Portfolio

Ambos escrevem schemas incompatíveis no mesmo arquivo. O último a salvar
apaga silenciosamente o estado do outro. O bug não se manifestou no helloworld
porque apenas o broker é instanciado. Mas quando `facade/api` e `facade/mcp`
forem implementadas com DI real, ambos serão instanciados simultaneamente e
o conflito vai corromper o estado.

## Decisão

Criar a classe `PaperState` como **único responsável** por ler e escrever
o arquivo `paper_state.json`. Tanto o broker quanto o repository delegam
persistência para ela — nunca escrevem diretamente no arquivo.

```
JsonFilePaperBroker   ──┐
                        ├──► PaperState ──► paper_state.json
JsonFilePortfolioRepo ──┘
```

`PaperState` expõe uma interface (`PaperStatePort`) que define:
- o schema canônico do arquivo (versão, saldo, ordens, posições, portfolios)
- operações atômicas de leitura e escrita
- fallback em caso de arquivo corrompido

## Racional

- **Fonte única de verdade**: elimina o risco de sobrescrita silenciosa
- **Schema versionado**: `PaperState` controla a evolução do formato JSON
- **Testável em isolamento**: implementações podem ser trocadas (JsonFile → SQLite)
  sem alterar broker ou repository
- **Alinha com ADR003**: ports & adapters, separação de responsabilidades

## Alternativas Consideradas

### A) Arquivos separados (broker.json + portfolios.json)
Rejeitada. Divide o estado do sistema em dois arquivos sem ganho real.
Dificulta backup, transferência e inspeção manual.

### B) Broker como dono único, repository removido do helloworld
Válida para o playground isolado, mas não escala para facades oficiais
que precisarão de ambos simultaneamente.

### C) Manter como está, resolver na hora do conflito
Rejeitada. O conflito é determinístico e vai ocorrer na próxima fase.

## Consequências

### Positivas
- Fim do conflito de writers
- Schema do JSON documentado e versionado em um único lugar
- Broker e repository se tornam mais simples (delegam I/O)
- Abre caminho para substituir JSON por SQLite sem tocar no domínio

### Negativas
- Introduce uma nova classe e interface no sistema
- Requer refatoração de `JsonFilePaperBroker` e `JsonFilePortfolioRepository`
  para delegar em vez de escrever diretamente

## Tarefas Derivadas

Ver PRD029 para o plano de implementação completo.

- [x] Criar `ports/paper_state_port.py` com `PaperStatePort`
- [x] Criar `adapters/persistence/json_file_paper_state.py`
- [x] Refatorar `JsonFilePaperBroker` para delegar ao `PaperState`
- [x] Refatorar `JsonFilePortfolioRepository` para delegar ao `PaperState`
- [x] Escrever testes unitários para `PaperStatePort`
- [x] Atualizar spec `paper-adapters` com novos cenários

## Implementação

Concluído em 2026-03-27 via change `paper-state-migration`.

### Decisões de Implementação

1. **Sem cache em memória**: Para evitar stale reads quando múltiplas instâncias
   de `JsonFilePaperState` são criadas via DI do FastAPI.

2. **Write atômico**: `salvar()` usa estratégia tmp + rename para evitar corrupção.

3. **Migração automática v1→v2**: Detecta schema legado e migra com backup automático.

### Arquivos Criados/Modificados

- `src/core/paper/ports/paper_state_port.py` — Interface + PaperStateData
- `src/core/paper/adapters/persistence/json_file_paper_state.py` — Implementação
- `src/core/paper/adapters/brokers/json_file_broker.py` — Refatorado para delegar
- `src/core/paper/adapters/persistence/json_file_repository.py` — Refatorado para delegar
- `tests/unit/core/paper/test_paper_state_port.py` — Testes unitários
