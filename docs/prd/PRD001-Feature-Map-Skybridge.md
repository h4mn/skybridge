---
status: aceito
data: 2025-12-22
---

﻿# PRD001 - Mapa de Funcionalidades da Skybridge

## 1. Objetivo
Com base no discovery, mapear e comparar as funcionalidades presentes em cada entidade Skybridge para orientar unificação, domínios e estratégia.

## 2. Problema
O discovery indica onde estão as entidades, mas não descreve o que cada uma faz. Sem esse mapa funcional, a unificação vira tentativa e erro.

## 3. Escopo
### Dentro do escopo
- Inventário de features por entidade.
- Classificação contra o núcleo provável.
- Extração de padrões e preferências.
- Preparação de mapa de domínios/infras e possíveis blueprints.
- Estrutura inicial para strategy ladder.

### Fora do escopo
- Refatoração e consolidação de código.
- Decisão final de arquitetura.
- Implementação de novas features.

## 4. Usuários / Stakeholders
- Autor do projeto Skybridge.
- Agentes IA (Codex).
- Time futuro.

## 5. Requisitos
### Funcionais
- Gerar `features-report.md` com campos: item, local, o que faz, propósito unificado, como agrega, valor (score).
- Inventariar por entidade e ordenar por score.
- Classificar cada entidade contra o núcleo.
- Listar padrões e preferências (CLI, API, orquestração, integrações).
- Indicar domínios e infras potenciais.
- Sugerir blueprints candidatos.

### Não funcionais
- Evidências auditáveis (paths e trechos curtos).
- Baixo ruído (foco no top score).
- Formato legível e reutilizável.

## 6. Critérios de sucesso
- Features inventariadas por entidade com evidência clara.
- Comparação objetiva contra o núcleo.
- Padrões e preferências destacados.
- Mapa inicial de domínios/infras e blueprints propostos.

## 7. Dependências e restrições
- Relatório `task001-discovery-report.md`.
- Acesso leitura a README/configs/código mínimo.

## 8. Entregáveis
- `features-report.md`.
- Tabela de comparação por entidade.
- Sumário de padrões, domínios e blueprints.

## 9. Próximos passos
- Executar playbook.
- Validar com o dono do projeto.
- Abrir ADR para unificação quando necessário.

---
> "Funcionalidade clara guia a unificação." - made by Sky
