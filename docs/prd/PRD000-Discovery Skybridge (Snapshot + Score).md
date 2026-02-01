---
status: aceito
data: 2025-12-22
---

# PRD000 — Descoberta da Skybridge via Snapshot + Scoring

## 1. Objetivo
Identificar, mapear e comparar tentativas de implementação da Skybridge espalhadas em `B:\_repositorios`, produzindo um diagnóstico objetivo que permita unificação e retomada do desenvolvimento.

## 2. Problema
A Skybridge evoluiu por múltiplas tentativas, incluindo código legado monolítico, sem um mapa confiável de onde estão os núcleos reais, fragmentos reaproveitáveis e esforços abandonados. Isso impede decisões claras e aumenta o custo cognitivo.

## 3. Escopo
### Dentro do escopo
- Varredura automatizada por snapshot até profundidade 5.
- Identificação de entidades candidatas via scoring.
- Relatório comparativo com evidências.

### Fora do escopo
- Refatoração ou unificação de código.
- Decisão final de arquitetura.
- Remoção de código legado.

## 4. Usuários / Stakeholders
- Autor do projeto Skybridge.
- Agentes IA (Codex).
- Futuro time colaborador.

## 5. Requisitos
### Funcionais
- Detectar diretórios candidatos a Skybridge.
- Calcular score por entidade com base em arquivos e marcadores.
- Gerar relatório ordenado por score.
- Produzir tabela comparativa de recursos.

### Não funcionais
- Baixo ruído (leitura mínima de conteúdo).
- Reprodutibilidade do diagnóstico.
- Execução rápida em repositório grande.

## 6. Critérios de Sucesso
- Lista clara de entidades candidatas ordenadas.
- Evidências explícitas por entidade.
- Identificação de um núcleo provável da Skybridge.
- Relatório utilizável como base para ADRs posteriores.

## 7. Dependências e Restrições
- Ferramenta snapshot existente.
- Repositório local `B:\_repositorios`.
- Profundidade máxima configurada (5).

## 8. Riscos e Mitigações
- Risco: ruído do monolito.
  - Mitigação: penalização sem marcadores fortes.
- Risco: falsos positivos.
  - Mitigação: score ponderado + evidências.

## 9. Entregáveis
- Relatório de descoberta.
- Tabela comparativa por entidade.
- Evidências baseadas em snapshot.

## 10. Próximos Passos
- Executar descoberta.
- Abrir ADR de unificação.
- Definir roadmap técnico.

---
> "Diagnóstico claro corta ciclos pela raiz." – made by Sky ✨
