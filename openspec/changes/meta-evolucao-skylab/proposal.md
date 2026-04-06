# Proposal: Meta-Evolução do Skylab (Self-Hosting)

## Why

O Skylab está bloqueado para evoluir a **si mesmo** (meta-evolução). Na Iteração 3 do Ralph Loop, o `scope_validator` protegeu `core/`, `testing/`, `quality/` de modificações, impedindo que o agente melhorasse o próprio sistema de evolução. Precisamos de uma arquitetura que permita auto-modificação segura e controlada.

## What Changes

Implementar arquitetura em 3 camadas para meta-evolução controlada:

- **Camada 0 - Invólucro (Inviolável)**: Meta-Gate + Git Snapshot Engine + Rollback
  - `meta_gate.py`: Portão que valida intenção, baseline snapshot, Code Health mínimo
  - `snapshot_engine.py`: Git como mecanismo de snapshot (commit/reset)
  - Controle de entrada para meta-modo com critérios explícitos

- **Camada 1 - Meta-Modificável (Core com Snapshot Obrigatório)**: Sistema pode evoluir
  - `evolution.py`: Pode ser modificado (com snapshot antes)
  - `scope_validator.py`: Respeita meta-mode (permite core/ quando liberado)
  - `test_runner.py`: Teste duplo (target + sistema)

- **Camada 2 - Target (Livre)**: Domínio evolui durante meta-evolução
  - `target/`: Código alvo que pode ser modificado livremente

- **Mecanismos de Segurança**:
  - **Recursão Controlada**: N=1 (sandbox), N=2 (meta-mode em main), N≤3 (meta-gate evolui meta-gate)
  - **Isolamento por Branch**: Cada sessão meta cria branch isolado
  - **Teste Duplo**: Após mudanças em `core/`, testa tanto target quanto sistema

## Capabilities

### New Capabilities

- `meta-gate`: Validação e controle de entrada para meta-modo de evolução
- `meta-snapshot`: Snapshot engine usando git para rollback seguro
- `meta-mode`: Modo de evolução onde `core/` pode ser modificado com proteções
- `self-hosting-session`: Sessões isoladas de meta-evolução com branch separado

### Modified Capabilities

- `scope-validation`: Adicionar parâmetro `meta_mode` para permitir modificar `core/` quando autorizado
- `evolution-loop`: Integrar com meta-gate para auto-evolução controlada

## Impact

- **Código**: Novos módulos em `programs/skylab/core/` (meta_gate.py, snapshot_engine.py, self_hosting_agent.py)
- **Modificações**: `scope_validator.py` (meta_mode parameter), `evolution.py` (integração)
- **Testes**: Novos testes de meta-mode em `tests/core/autokarpa/programs/skylab/test_meta_mode.py`
- **Documentação**: `doc/skylab/META-EVOLUÇÃO.md` com guia completo
- **Dependências**: Git (já existe) como mecanismo de snapshot
- **Risco**: Baixo - sandbox isolado previne corrupção do sistema principal

---

> "O guardião que se guarda é guardião duas vezes" – ditado popular
> "Meta-evolução é o Santo Graal da evolução autônoma" – made by Sky 🔄
