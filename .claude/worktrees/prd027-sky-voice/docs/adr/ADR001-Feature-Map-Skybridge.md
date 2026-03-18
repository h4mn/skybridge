---
status: aceito
data: 2025-12-22
---

﻿# ADR001 - Evolução do Discovery para Mapa de Funcionalidades (Skybridge)

## Status
Proposto

## Contexto
O relatório `task001-discovery-report.md` consolidou um mapa das entidades-base da Skybridge. O próximo passo necessário não é mais localizar, e sim entender cada entidade e extrair suas funcionalidades para orientar unificação e estratégia.

## Decisão
Mudar o objetivo de discovery para **inventário de funcionalidades por entidade**, com classificação por score e comparação contra o núcleo. A saída principal passa a ser `features-report.md`, estruturado para uso em mapa de domínios/infras, blueprints e strategy ladder.

## Escopo
Dentro:
- Inventariar features por entidade (item, local, o que faz, propósito unificado, como agrega, score).
- Classificar entidades contra o núcleo provável.
- Extrair padrões e preferências (arquitetura, integrações, estilo de CLI/API).
- Preparar mapa de domínios e infras, e rascunho de blueprints.

Fora:
- Unificação de código.
- Decisões finais de arquitetura.
- Refatorações ou migrações.

## Consequências
Positivas:
- Mapa funcional comparável e reutilizável.
- Clareza sobre o que reaproveitar e o que abandonar.
- Base objetiva para roadmap e strategy ladder.

Negativas / Trade-offs:
- Leitura de conteúdo mais profunda (README/configs/código crítico).
- Tempo adicional de análise por entidade.

## Riscos e mitigações
- Risco: viés pelo score de discovery.
  - Mitigação: validar features por evidência direta e registrar gaps.
- Risco: ruidão por entidades genéricas.
  - Mitigação: priorizar top scores e limitar escopo por entidade.

## Próximos passos
1) Executar PRD e Playbook de feature mapping.
2) Produzir `features-report.md`.
3) Consolidar padrões e candidatos a blueprints.

---
> "Mapa funcional antes de unificar." - made by Sky
