# TASK003 - Implementar ADR002 (Estrutura do Repositório Skybridge)

## Objetivo
Aplicar a estrutura canônica definida na ADR002 para o repositório Skybridge, garantindo fronteiras claras (Kernel/Core/Platform/Infra) e contratos de plugin estáveis.

## Entrada
- `docs/adr/ADR002-Estrutura do Repositório Skybridge.md`
- Snapshot atual do repositório (raiz e `docs/`)

## Instruções
- Use SnDD: primeiro gerar snapshot e comparar com a estrutura esperada; evitar leitura profunda antes do mapa.
- Produzir um relatório de discovery com evidências (paths existentes vs ausentes).
- Gerar uma tabela comparativa (ADR002 x estado atual) com gaps por área.
- Propor e priorizar recomendações acionáveis.
- **Execução**: qualquer mudança fora de `.agents/` exige autorização explícita.

## Resultado esperado
- `adr002-discovery-report.md` (snapshot + gaps + evidências).
- `adr002-comparativo.md` (tabela ADR002 x atual).
- `adr002-recomendacoes.md` (backlog acionável e priorizado).
- Lista de passos técnicos para:
  - Criar a árvore `src/skybridge/` (kernel, core, platform, infra).
  - Criar READMEs obrigatórios.
  - Definir política de compatibilidade do `kernel_api` (v1).
  - Adicionar guardrails (lint/checks de import).

---
> "Clareza de estrutura reduz custo de evolução." - made by Sky
